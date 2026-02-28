"""
核心业务服务
整合采集、处理、筛选、生成、推送流程
"""
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.collector import (
    BilibiliCollector,
    CollectorManager,
    CollectorResult,
    HackerNewsCollector,
    RSSCollector,
    # 中国科技媒体
    JuejinCollector, OschinaCollector, InfoqChinaCollector,
    SegmentFaultCollector,
    # 中国商业媒体
    HuxiuCollector, LeiphoneCollector, PingWestCollector,
    GeekParkCollector, SinaTechCollector, NetEaseTechCollector,
    # 中国社区
    V2EXCollector, XueqiuCollector, WallstreetCnCollector,
    ITPubCollector, ChinaUnixCollector,
    # 优质生活方式/工具类媒体
    SspaiCollector, IfanrCollector, DgtleCollector,
    AppinnCollector, LiqiCollector, UisdcCollector,
    ToodaylabCollector,
)
from src.config import get_column_config, get_settings
from src.database import (
    ContentItemDB,
    ContentRepository,
    DailyReportDB,
    DailyReportItemDB,
    DailyReportRepository,
    get_session,
    init_db
)
from src.filter.selector import ContentSelector
from src.models import ChannelType, ContentItem, ContentStatus, DailyReport
from src.output.publisher import Publisher, PushResult
from src.processor.summarizer import ContentProcessor
from src.progress import ErrorHandler

settings = get_settings()


class DailyAgentService:
    """日报 Agent 服务（优化版）"""
    
    def __init__(self, max_concurrency: int = None):
        self.column_config = get_column_config()
        self.collector_manager = CollectorManager()
        
        # 使用优化的内容处理器，支持并发
        # 从配置读取并发数，默认 5
        concurrency = max_concurrency or settings.llm_max_concurrency
        # 使用快速模式跳过非必要的预处理步骤
        self.content_processor = ContentProcessor(
            use_llm=bool(settings.openai_api_key),
            max_concurrency=concurrency,
            fast_mode=True  # 启用快速模式
        )
        self.content_selector = ContentSelector()
        self.publisher = Publisher()
        self._initialized = False
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return

        print("[Service] 初始化服务...")

        # 初始化数据库表
        await init_db()
        print("[Service] 数据库初始化完成")

        # 注册采集器
        await self._register_collectors()

        self._initialized = True
        print("[Service] 服务初始化完成")
    
    async def _register_collectors(self):
        """注册采集器 - 支持中国信息源"""
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
                            from src.collector import HackerNewsCollector
                            collector = HackerNewsCollector(name, source_config)
                            self.collector_manager.register(collector)
                            print(f"[Service] 注册 HN 采集器: {name}")
                        # 可以添加更多 API 采集器

                    elif source_type == "bilibili":
                        from src.collector import BilibiliCollector
                        collector = BilibiliCollector(name, source_config)
                        self.collector_manager.register(collector)
                        print(f"[Service] 注册 B站采集器: {name}")

                    elif source_type == "web":
                        provider = source_config.get("provider")
                        collector = self._create_web_collector(name, provider, source_config)
                        if collector:
                            self.collector_manager.register(collector)
                            print(f"[Service] 注册 Web 采集器: {name} ({provider})")

                except Exception as e:
                    print(f"[Service] 注册采集器失败 {name}: {e}")

    def _create_web_collector(self, name: str, provider: str, config: dict):
        """创建 Web 采集器 - 支持中国信息源"""
        from src.collector import (
            # 科技媒体
            JuejinCollector, OschinaCollector, InfoqChinaCollector,
            SegmentFaultCollector,
            # 商业媒体
            HuxiuCollector, LeiphoneCollector, PingWestCollector,
            GeekParkCollector, SinaTechCollector, NetEaseTechCollector,
            # 社区
            V2EXCollector, XueqiuCollector, WallstreetCnCollector,
            ITPubCollector, ChinaUnixCollector,
            # 生活方式/工具
            SspaiCollector, IfanrCollector, DgtleCollector,
            AppinnCollector, LiqiCollector, UisdcCollector,
            ToodaylabCollector,
        )

        # 映射 provider 到采集器类
        collector_map = {
            # 中国科技媒体
            "juejin": JuejinCollector,
            "oschina": OschinaCollector,
            "infoq_cn": InfoqChinaCollector,
            "segmentfault": SegmentFaultCollector,
            # 中国商业媒体
            "huxiu": HuxiuCollector,
            "leiphone": LeiphoneCollector,
            "pingwest": PingWestCollector,
            "geekpark": GeekParkCollector,
            "sina_tech": SinaTechCollector,
            "netease_tech": NetEaseTechCollector,
            # 中国社区
            "v2ex": V2EXCollector,
            "xueqiu": XueqiuCollector,
            "wallstreetcn": WallstreetCnCollector,
            "itpub": ITPubCollector,
            "chinaunix": ChinaUnixCollector,
            # 生活方式/工具
            "sspai": SspaiCollector,
            "ifanr": IfanrCollector,
            "dgtle": DgtleCollector,
            "appinn": AppinnCollector,
            "liqi": LiqiCollector,
            "uisdc": UisdcCollector,
            "toodaylab": ToodaylabCollector,
        }

        collector_class = collector_map.get(provider)
        if collector_class:
            return collector_class(name, config)
        return None
    
    async def _save_item(self, item) -> bool:
        """保存单个内容到数据库（独立会话）"""
        try:
            async with get_session() as session:
                repo = ContentRepository(session)
                # 检查是否已存在
                existing = await repo.get_by_url(item.url)
                if existing:
                    return False
                
                # 转换为数据库模型
                db_item = self._to_db_item(item)
                await repo.create(db_item)
                return True
        except Exception as e:
            print(f"[Service] 保存内容失败 {item.url[:50]}...: {e}")
            return False
    
    async def collect_all(self, show_progress: bool = True) -> Dict[str, CollectorResult]:
        """执行所有采集"""
        if show_progress:
            ErrorHandler.info("开始采集...")

        results = await self.collector_manager.collect_all()

        # 保存到数据库（每个内容独立会话，避免长时间锁定）
        total_saved = 0
        total_count = sum(len(r.items) for r in results.values() if r.success)

        if show_progress and total_count > 0:
            from src.progress import ProgressManager
            with ProgressManager(f"保存 {total_count} 条内容") as pm:
                processed = 0
                for name, result in results.items():
                    if not result.success:
                        continue
                    for item in result.items:
                        if await self._save_item(item):
                            total_saved += 1
                        processed += 1
                        pm.update(processed, total_count)
        else:
            for name, result in results.items():
                if not result.success:
                    continue
                for item in result.items:
                    if await self._save_item(item):
                        total_saved += 1

        if show_progress:
            ErrorHandler.success(f"采集完成，保存 {total_saved} 条内容")
        return results
    
    async def process_content(self, item: ContentItem) -> ContentItem:
        """处理内容"""
        return await self.content_processor.process(item)
    
    async def generate_daily_report(
        self,
        user_id: str = "default",
        date: Optional[datetime] = None,
        column_ids: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> DailyReport:
        """
        生成日报（优化版 - 批量并行处理）

        Args:
            user_id: 用户ID
            date: 日期（默认今天）
            column_ids: 指定分栏（默认全部）
            show_progress: 是否显示进度条

        Returns:
            DailyReport: 生成的日报
        """
        import time
        from src.progress import ProgressManager, ErrorHandler

        start_time = time.time()
        date = date or datetime.now(timezone.utc)

        if show_progress:
            ErrorHandler.info(f"生成日报: {date.date()}, user={user_id}")

        # 1. 采集新内容
        await self.collect_all(show_progress=show_progress)

        # 2. 获取分栏配置
        columns = self.column_config.get_columns()
        if column_ids:
            columns = [c for c in columns if c.get("id") in column_ids]

        # 3. 处理内容并生成日报
        async with get_session() as session:
            content_repo = ContentRepository(session)
            report_repo = DailyReportRepository(session)
            
            # 检查是否已存在同一天的日报，如存在则删除
            report_id = f"report_{user_id}_{date.strftime('%Y%m%d')}"
            existing_report = await report_repo.get_by_id(report_id)
            if existing_report:
                await report_repo.delete(report_id)
                print(f"[Service] 删除已存在的日报: {report_id}")
            
            # 创建日报
            report = DailyReportDB(
                id=report_id,
                date=date,
                user_id=user_id,
                title=f"今日日报 - {date.strftime('%Y年%m月%d日')}",
                is_generated=False
            )
            await report_repo.create(report)
            
            # 收集所有分栏的候选内容
            all_candidate_items = []
            column_candidate_map = {}  # 记录每个分栏的候选内容
            
            # 预加载所有待处理内容
            all_pending_items = await content_repo.get_by_status(
                status=ContentStatus.PENDING.value,
                date=date,
                limit=500
            )
            
            # 按 source 名称分组
            items_by_source: Dict[str, List[ContentItemDB]] = {}
            for db_item in all_pending_items:
                source = db_item.source
                if source not in items_by_source:
                    items_by_source[source] = []
                items_by_source[source].append(db_item)
            
            print(f"[Service] 共 {len(all_pending_items)} 条待处理内容，来自 {len(items_by_source)} 个来源")
            
            # 收集所有分栏的候选内容
            for col in columns:
                col_id = col.get("id")
                col_sources = col.get("sources", [])
                source_names = {s.get("name") for s in col_sources}
                
                col_items = []
                for source_name in source_names:
                    if source_name in items_by_source:
                        for db_item in items_by_source[source_name]:
                            item = self._from_db_item(db_item)
                            col_items.append(item)
                            # 避免重复添加（一个内容可能在多个分栏中）
                            if item not in all_candidate_items:
                                all_candidate_items.append(item)
                
                # 限制候选内容数量
                max_candidates = col.get("max_items", 5) * 3
                if len(col_items) > max_candidates:
                    col_items = col_items[:max_candidates]
                
                column_candidate_map[col_id] = col_items
                print(f"[Service] 分栏 '{col_id}': 收集 {len(col_items)} 条候选内容")
            
            if show_progress:
                ErrorHandler.info(f"总共需要处理 {len(all_candidate_items)} 条唯一内容")

            # 批量处理所有内容（使用并发优化）
            processed_items_map = {}
            if all_candidate_items:
                if show_progress:
                    ErrorHandler.info("开始批量处理内容...")
                process_start = time.time()

                # 使用批量处理
                def progress_callback(processed, total, message):
                    if show_progress and (processed % 5 == 0 or processed == total):
                        ErrorHandler.info(f"处理进度: {processed}/{total} - {message}")

                processed_items = await self.content_processor.process_batch(
                    all_candidate_items,
                    progress_callback=progress_callback
                )

                # 建立 ID 到处理后内容的映射
                for item in processed_items:
                    processed_items_map[item.id] = item

                process_time = time.time() - process_start
                if show_progress:
                    ErrorHandler.success(f"内容处理完成，耗时: {process_time:.1f}秒")
            
            # 处理每个分栏的选择
            items_by_column: Dict[str, List[ContentItem]] = {}
            total_items = 0
            all_sources = set()
            all_topics = set()
            
            for col in columns:
                col_id = col.get("id")
                col_items = column_candidate_map.get(col_id, [])
                
                # 获取处理后的内容
                processed_col_items = [
                    processed_items_map.get(item.id, item) 
                    for item in col_items
                ]
                
                # 选择内容
                max_items = col.get("max_items", 5)
                sort_by = col.get("organization", {}).get("sort_by", "relevance")
                dedup_strategy = col.get("organization", {}).get("dedup_strategy", "semantic")
                
                selected = self.content_selector.select(
                    items=processed_col_items,
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
            
            total_time = time.time() - start_time
            if show_progress:
                ErrorHandler.success(f"日报生成完成: {report.id}, 共 {total_items} 条, 总耗时: {total_time:.1f}秒")
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
        
        async with get_session() as session:
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
                db_report.sent_at = datetime.now(timezone.utc)
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
