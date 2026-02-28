"""
内容选择模块
负责根据规则选择和组合内容
"""
from typing import Dict, List, Optional

from src.filter.deduper import ContentDeduper
from src.filter.ranker import ContentRanker, QualityScorer
from src.models import ContentItem, UserProfile


class ContentSelector:
    """内容选择器"""
    
    def __init__(
        self, 
        user_profile: Optional[UserProfile] = None,
        composition_rules: Optional[Dict] = None
    ):
        self.user_profile = user_profile
        self.composition_rules = composition_rules or {}
        self.deduper = ContentDeduper()
        self.ranker = ContentRanker(user_profile)
        self.quality_scorer = QualityScorer()
    
    def select(
        self,
        items: List[ContentItem],
        max_items: int = 10,
        sort_by: str = "relevance",
        dedup_strategy: str = "semantic",
        **kwargs
    ) -> List[ContentItem]:
        """
        选择内容
        
        Args:
            items: 候选内容列表
            max_items: 最大选择数量
            sort_by: 排序方式
            dedup_strategy: 去重策略
            
        Returns:
            List[ContentItem]: 选中的内容
        """
        if not items:
            return []
        
        # 1. 质量评分
        items = self.quality_scorer.score_batch(items)
        
        # 2. 去重
        dedup_result = self.deduper.dedup(items, strategy=dedup_strategy)
        items = dedup_result.items
        
        # 3. 排序
        items = self.ranker.rank(items, sort_by=sort_by)
        
        # 4. 多样性重排序
        items = self.ranker.diversity_rerank(
            items,
            max_per_source=self.composition_rules.get("source_diversity", {}).get("max_ratio_per_source", 0.4),
            max_per_topic=0.5
        )
        
        # 5. 限制数量
        items = items[:max_items]
        
        return items
    
    def select_for_columns(
        self,
        column_items: Dict[str, List[ContentItem]],
        column_configs: List[Dict],
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, List[ContentItem]]:
        """
        为每个分栏选择内容
        
        Args:
            column_items: 分栏 -> 内容列表 映射
            column_configs: 分栏配置列表
            user_profile: 用户画像
            
        Returns:
            Dict[str, List[ContentItem]]: 分栏选择结果
        """
        result = {}
        profile = user_profile or self.user_profile
        
        for col_config in column_configs:
            col_id = col_config.get("id")
            if col_id not in column_items:
                continue
            
            items = column_items[col_id]
            
            # 获取分栏配置
            max_items = col_config.get("max_items", 5)
            sort_by = col_config.get("organization", {}).get("sort_by", "relevance")
            dedup_strategy = col_config.get("organization", {}).get("dedup_strategy", "semantic")
            
            # 选择内容
            selected = self.select(
                items=items,
                max_items=max_items,
                sort_by=sort_by,
                dedup_strategy=dedup_strategy
            )
            
            result[col_id] = selected
        
        return result
    
    def filter_by_quality(
        self, 
        items: List[ContentItem], 
        min_score: float = 0.3
    ) -> List[ContentItem]:
        """按质量过滤"""
        return [item for item in items if item.quality_score >= min_score]
    
    def filter_by_time(
        self, 
        items: List[ContentItem], 
        max_age_hours: int = 48
    ) -> List[ContentItem]:
        """按时间过滤"""
        from datetime import datetime, timedelta, timezone
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        return [
            item for item in items 
            if (item.publish_time or item.fetch_time) >= cutoff
        ]
    
    def ensure_topic_coverage(
        self, 
        items: List[ContentItem], 
        min_topics: int = 3
    ) -> List[ContentItem]:
        """
        确保主题覆盖度
        
        如果主题不够，放宽选择条件
        """
        topics = set()
        for item in items:
            topics.update(item.topics)
        
        if len(topics) >= min_topics:
            return items
        
        # 主题不够，目前简单返回
        # 实际可以动态调整参数重新选择
        return items
