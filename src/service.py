"""
核心业务服务
整合采集、处理、筛选、生成、推送流程
"""
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.collector import (
    CollectorManager,
    CollectorResult,
    HackerNewsCollector,
    RSSCollector
)
from src.config import get_column_config, get_settings
from src.database import (
    ContentItemDB,
    ContentRepository,
    DailyReportDB,
    DailyReportItemDB,
    DailyReportRepository,
    get_session
)
from src.filter.selector import ContentSelector
from src.models import ChannelType, ContentItem, ContentStatus, DailyReport
from src.output.publisher import Publisher, PushResult
from src.processor.summarizer import ContentProcessor

settings = get_settings()


class DailyAgentService:
    """日报 Agent 服务"""
    
    def __init__(self):
        self.column_config = get_column_config()
        self.collector_manager = CollectorManager()
        self.content_processor = ContentProcessor(use_llm=bool(settings.openai_api_key))
        self.content_selector = ContentSelector()
        self.publisher = Publisher()
        self._initialized = False
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
        
        print("[Service] 初始化服务...")
        
        # 注册采集器
        await self._register_collectors()
        
        self._initialized = True
        print("[Service] 服务初始化完成")
    
    async def _register_collectors(self):
        """注册采集器"""
        columns = self.column_config.get_columns()
        
        for col in columns:
            sources = col.get("sources", [])
            for source_config in sources:
                source_type = source_config.get("type")
                name = source_config.get("name", "unknown")
                
                try:
                    if source_type == "rss":
                        collector = RSSCollector(name, source_config)
                        self.collector_manager.register(collector)
                        print(f"[Service] 注册 RSS 采集器: {name}")
                    
                    elif source_type == "api":
                        provider = source_config.get("provider")
                        if provider == "hackernews":
                            collector = HackerNewsCollector(name, source_config)
                            self.collector_manager.register(collector)
                            print(f"[Service] 注册 HN 采集器: {name}")
                        # 可以添加更多 API 采集器
                    
                    # TODO: 添加更多采集器类型
                    
                except Exception as e:
                    print(f"[Service] 注册采集器失败 {name}: {e}")
    
    async def collect_all(self) -> Dict[str, CollectorResult]:
        """执行所有采集"""
        print("[Service] 开始采集...")
        results = await self.collector_manager.collect_all()
        
        # 保存到数据库
        async for session in get_session():
            repo = ContentRepository(session)
            total_saved = 0
            
            for name, result in results.items():
                if not result.success:
                    continue
                
                for item in result.items:
                    try:
                        # 检查是否已存在
                        existing = await repo.get_by_url(item.url)
                        if existing:
                            continue
                        
                        # 转换为数据库模型
                        db_item = self._to_db_item(item)
                        await repo.create(db_item)
                        total_saved += 1
                        
                    except Exception as e:
                        print(f"[Service] 保存内容失败: {e}")
            
            print(f"[Service] 采集完成，保存 {total_saved} 条内容")
            break  # 只执行一次
        
        return results
    
    async def process_content(self, item: ContentItem) -> ContentItem:
        """处理内容"""
        return await self.content_processor.process(item)
    
    async def generate_daily_report(
        self,
        user_id: str = "default",
        date: Optional[datetime] = None,
        column_ids: Optional[List[str]] = None
    ) -> DailyReport:
        """
        生成日报
        
        Args:
            user_id: 用户ID
            date: 日期（默认今天）
            column_ids: 指定分栏（默认全部）
            
        Returns:
            DailyReport: 生成的日报
        """
        date = date or datetime.utcnow()
        print(f"[Service] 生成日报: {date.date()}, user={user_id}")
        
        # 1. 采集新内容
        await self.collect_all()
        
        # 2. 获取分栏配置
        columns = self.column_config.get_columns()
        if column_ids:
            columns = [c for c in columns if c.get("id") in column_ids]
        
        # 3. 处理内容并生成日报
        async for session in get_session():
            content_repo = ContentRepository(session)
            report_repo = DailyReportRepository(session)
            
            # 创建日报
            report = DailyReportDB(
                id=f"report_{user_id}_{date.strftime('%Y%m%d')}",
                date=date,
                user_id=user_id,
                title=f"今日日报 - {date.strftime('%Y年%m月%d日')}",
                is_generated=False
            )
            await report_repo.create(report)
            
            # 处理每个分栏
            items_by_column: Dict[str, List[ContentItem]] = {}
            total_items = 0
            all_sources = set()
            all_topics = set()
            
            for col in columns:
                col_id = col.get("id")
                col_sources = col.get("sources", [])
                
                # 获取该分栏的候选内容
                candidate_items = []
                
                for source_config in col_sources:
                    source_name = source_config.get("name")
                    items = await content_repo.get_by_column(
                        column_id=col_id,
                        date=date,
                        status=ContentStatus.PENDING.value,
                        limit=50
                    )
                    
                    for db_item in items:
                        item = self._from_db_item(db_item)
                        candidate_items.append(item)
                
                # 处理内容
                processed_items = []
                for item in candidate_items:
                    try:
                        processed = await self.process_content(item)
                        processed_items.append(processed)
                    except Exception as e:
                        print(f"[Service] 处理内容失败 {item.url}: {e}")
                
                # 选择内容
                max_items = col.get("max_items", 5)
                sort_by = col.get("organization", {}).get("sort_by", "relevance")
                dedup_strategy = col.get("organization", {}).get("dedup_strategy", "semantic")
                
                selected = self.content_selector.select(
                    items=processed_items,
                    max_items=max_items,
                    sort_by=sort_by,
                    dedup_strategy=dedup_strategy
                )
                
                # 更新状态
                for item in selected:
                    db_item = await content_repo.get_by_id(item.id)
                    if db_item:
                        db_item.status = ContentStatus.SELECTED.value
                        db_item.column_id = col_id
                        await content_repo.update(db_item)
                
                items_by_column[col_id] = selected
                total_items += len(selected)
                
                for item in selected:
                    all_sources.add(item.source)
                    all_topics.update(item.topics)
                
                # 添加到日报
                for order, item in enumerate(selected):
                    report_item = DailyReportItemDB(
                        report_id=report.id,
                        content_id=item.id,
                        column_id=col_id,
                        order=order
                    )
                    await report_repo.add_item(report_item)
            
            # 更新日报统计
            report.total_items = total_items
            report.sources_count = len(all_sources)
            report.topics_count = len(all_topics)
            report.is_generated = True
            
            await report_repo.update(report)
            
            # 构建返回对象
            result = DailyReport(
                id=report.id,
                date=report.date,
                user_id=report.user_id,
                title=report.title,
                total_items=report.total_items,
                is_generated=True
            )
            
            print(f"[Service] 日报生成完成: {report.id}, 共 {total_items} 条")
            return result
    
    async def push_report(
        self,
        report: DailyReport,
        channels: Optional[List[str]] = None,
        user_id: str = "default"
    ) -> Dict[ChannelType, PushResult]:
        """
        推送日报
        
        Args:
            report: 日报
            channels: 推送渠道（默认从用户画像获取）
            user_id: 用户ID
            
        Returns:
            Dict[ChannelType, PushResult]: 推送结果
        """
        print(f"[Service] 推送日报: {report.id}")
        
        # 获取分栏配置和内容
        columns = self.column_config.get_columns()
        
        async for session in get_session():
            # 获取日报内容
            content_repo = ContentRepository(session)
            report_repo = DailyReportRepository(session)
            
            db_report = await report_repo.get_by_id(report.id)
            if not db_report:
                raise ValueError(f"日报不存在: {report.id}")
            
            # 获取分栏内容
            items_by_column: Dict[str, List[ContentItem]] = {}
            for col in columns:
                col_id = col.get("id")
                items = await content_repo.get_by_column(
                    column_id=col_id,
                    date=db_report.date
                )
                items_by_column[col_id] = [self._from_db_item(item) for item in items]
            
            # 如果没有指定渠道，获取用户默认渠道
            if not channels:
                from src.personalization.profile import ProfileManager
                profile_manager = ProfileManager(session)
                profile = await profile_manager.get_profile(user_id)
                channels = [c.value for c in profile.push_channels]
            
            # 转换渠道类型
            channel_types = []
            for c in channels:
                try:
                    channel_types.append(ChannelType(c))
                except ValueError:
                    pass
            
            # 推送
            results = await self.publisher.publish(
                report=report,
                columns_config=columns,
                items_by_column=items_by_column,
                channels=channel_types
            )
            
            # 更新发送状态
            if any(r.success for r in results.values()):
                db_report.is_sent = True
                db_report.sent_at = datetime.utcnow()
                await report_repo.update(db_report)
            
            return results
    
    def _to_db_item(self, item: ContentItem) -> ContentItemDB:
        """转换为数据库模型"""
        import json
        
        return ContentItemDB(
            id=item.id,
            title=item.title,
            url=item.url,
            source=item.source,
            source_type=item.source_type.value,
            content=item.content,
            summary=item.summary,
            key_points=json.dumps(item.key_points, ensure_ascii=False) if item.key_points else None,
            author=item.author,
            publish_time=item.publish_time,
            fetch_time=item.fetch_time,
            topics=json.dumps(item.topics, ensure_ascii=False) if item.topics else None,
            entities=json.dumps(item.entities, ensure_ascii=False) if item.entities else None,
            keywords=json.dumps(item.keywords, ensure_ascii=False) if item.keywords else None,
            image_url=item.image_url,
            read_time=item.read_time,
            quality_score=item.quality_score,
            relevance_score=item.relevance_score,
            popularity_score=item.popularity_score,
            raw_data=json.dumps(item.raw_data, ensure_ascii=False) if item.raw_data else None,
            status=item.status.value,
            column_id=item.column_id,
            is_duplicate=item.is_duplicate,
            duplicate_of=item.duplicate_of
        )
    
    def _from_db_item(self, db_item: ContentItemDB) -> ContentItem:
        """从数据库模型转换"""
        import json
        from src.database import parse_json_list
        
        return ContentItem(
            id=db_item.id,
            title=db_item.title,
            url=db_item.url,
            source=db_item.source,
            source_type=db_item.source_type,
            content=db_item.content,
            summary=db_item.summary,
            key_points=parse_json_list(db_item.key_points),
            author=db_item.author,
            publish_time=db_item.publish_time,
            fetch_time=db_item.fetch_time,
            topics=parse_json_list(db_item.topics),
            entities=parse_json_list(db_item.entities),
            keywords=parse_json_list(db_item.keywords),
            image_url=db_item.image_url,
            read_time=db_item.read_time,
            quality_score=db_item.quality_score,
            relevance_score=db_item.relevance_score,
            popularity_score=db_item.popularity_score,
            raw_data=json.loads(db_item.raw_data) if db_item.raw_data else None,
            status=db_item.status,
            column_id=db_item.column_id,
            is_duplicate=db_item.is_duplicate,
            duplicate_of=db_item.duplicate_of
        )
