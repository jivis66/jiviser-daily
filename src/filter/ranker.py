"""
内容排序模块
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from src.models import ContentItem, UserProfile


class ContentRanker:
    """内容排序器"""
    
    def __init__(self, user_profile: Optional[UserProfile] = None):
        self.user_profile = user_profile
    
    def rank(
        self, 
        items: List[ContentItem], 
        sort_by: str = "relevance",
        user_profile: Optional[UserProfile] = None
    ) -> List[ContentItem]:
        """
        排序内容
        
        Args:
            items: 内容列表
            sort_by: 排序方式 (relevance/time/popularity/mixed)
            user_profile: 用户画像（可选，覆盖初始化时的设置）
            
        Returns:
            List[ContentItem]: 排序后的内容
        """
        profile = user_profile or self.user_profile
        
        if sort_by == "time":
            return self._sort_by_time(items)
        elif sort_by == "popularity":
            return self._sort_by_popularity(items)
        elif sort_by == "relevance" and profile:
            return self._sort_by_relevance(items, profile)
        else:
            return self._mixed_sort(items, profile)
    
    def _sort_by_time(self, items: List[ContentItem]) -> List[ContentItem]:
        """按时间排序（最新的在前）"""
        return sorted(
            items,
            key=lambda x: x.publish_time or x.fetch_time,
            reverse=True
        )
    
    def _sort_by_popularity(self, items: List[ContentItem]) -> List[ContentItem]:
        """按热度排序"""
        return sorted(
            items,
            key=lambda x: x.popularity_score,
            reverse=True
        )
    
    def _sort_by_relevance(
        self, 
        items: List[ContentItem], 
        user_profile: UserProfile
    ) -> List[ContentItem]:
        """按用户相关性排序"""
        # 计算每个内容的相关性分数
        scored_items = []
        for item in items:
            score = self._calculate_relevance_score(item, user_profile)
            item.relevance_score = score
            scored_items.append((item, score))
        
        # 排序
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored_items]
    
    def _mixed_sort(
        self, 
        items: List[ContentItem], 
        user_profile: Optional[UserProfile]
    ) -> List[ContentItem]:
        """混合排序 - 综合多种因素"""
        now = datetime.now(timezone.utc)
        
        scored_items = []
        for item in items:
            score = 0.0
            
            # 1. 时效性分数 (0-40)
            time_score = self._calculate_time_score(item, now)
            score += time_score * 0.4
            
            # 2. 热度分数 (0-30)
            score += min(item.popularity_score / 100, 1.0) * 0.3
            
            # 3. 质量分数 (0-20)
            score += item.quality_score * 0.2
            
            # 4. 相关性分数 (0-10)
            if user_profile:
                relevance = self._calculate_relevance_score(item, user_profile)
                score += relevance * 0.1
            
            item.relevance_score = score
            scored_items.append((item, score))
        
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored_items]
    
    def _calculate_time_score(self, item: ContentItem, now: datetime) -> float:
        """计算时效性分数"""
        time = item.publish_time or item.fetch_time
        if not time:
            return 0.5
        
        age_hours = (now - time).total_seconds() / 3600
        
        if age_hours < 1:
            return 1.0
        elif age_hours < 6:
            return 0.9
        elif age_hours < 24:
            return 0.8
        elif age_hours < 48:
            return 0.6
        elif age_hours < 72:
            return 0.4
        else:
            return 0.2
    
    def _calculate_relevance_score(
        self, 
        item: ContentItem, 
        user_profile: UserProfile
    ) -> float:
        """计算内容与用户的相关性分数"""
        score = 0.0
        total_weights = 0
        
        # 1. 兴趣标签匹配
        if user_profile.interests:
            total_weights += 1
            interest_match = self._calculate_keyword_match(
                item, user_profile.interests
            )
            score += interest_match * 1.0
        
        # 2. 偏好来源匹配
        if user_profile.preferred_sources:
            total_weights += 1
            if item.source in user_profile.preferred_sources:
                score += 1.0
        
        # 3. 包含关键词匹配
        if user_profile.keywords_include:
            total_weights += 1
            include_match = self._calculate_keyword_match(
                item, user_profile.keywords_include
            )
            score += include_match * 1.0
        
        # 4. 排除关键词（扣分）
        if user_profile.keywords_exclude:
            exclude_match = self._calculate_keyword_match(
                item, user_profile.keywords_exclude
            )
            score -= exclude_match * 0.5
        
        # 5. 专业领域匹配
        if user_profile.expertise:
            total_weights += 1
            expertise_match = self._calculate_keyword_match(
                item, user_profile.expertise
            )
            score += expertise_match * 1.0
        
        # 归一化
        if total_weights > 0:
            score = max(0, min(1, score / total_weights))
        
        return score
    
    def _calculate_keyword_match(
        self, 
        item: ContentItem, 
        keywords: List[str]
    ) -> float:
        """计算关键词匹配度"""
        if not keywords:
            return 0.0
        
        text = f"{item.title} {' '.join(item.keywords)} {item.content or ''}".lower()
        
        matches = sum(1 for kw in keywords if kw.lower() in text)
        return matches / len(keywords)
    
    def diversity_rerank(
        self, 
        items: List[ContentItem], 
        max_per_source: float = 0.4,
        max_per_topic: float = 0.5
    ) -> List[ContentItem]:
        """
        多样性重排序
        
        确保来源和主题的多样性
        
        Args:
            items: 已排序的内容列表
            max_per_source: 单个来源最大占比
            max_per_topic: 单个主题最大占比
            
        Returns:
            List[ContentItem]: 重排序后的列表
        """
        if not items:
            return []
        
        result = []
        source_counts: Dict[str, int] = {}
        topic_counts: Dict[str, int] = {}
        total = 0
        
        for item in items:
            source = item.source
            topics = item.topics[:1] if item.topics else ["uncategorized"]
            
            # 检查来源限制
            source_ratio = source_counts.get(source, 0) / (total + 1)
            if source_ratio > max_per_source:
                continue
            
            # 检查主题限制
            topic_ratio = max(
                topic_counts.get(t, 0) for t in topics
            ) / (total + 1)
            if topic_ratio > max_per_topic:
                continue
            
            result.append(item)
            source_counts[source] = source_counts.get(source, 0) + 1
            for t in topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1
            total += 1
        
        return result


class QualityScorer:
    """内容质量评分器"""
    
    def score(self, item: ContentItem) -> float:
        """
        计算内容质量分数 (0-1)
        
        评分维度：
        - 内容长度
        - 标题质量
        - 元数据完整性
        - 来源可信度
        """
        scores = []
        
        # 1. 内容长度 (0-0.25)
        content_len = len(item.content or "")
        if content_len > 2000:
            scores.append(0.25)
        elif content_len > 1000:
            scores.append(0.2)
        elif content_len > 500:
            scores.append(0.15)
        elif content_len > 200:
            scores.append(0.1)
        else:
            scores.append(0.05)
        
        # 2. 标题质量 (0-0.25)
        title_len = len(item.title)
        if 20 <= title_len <= 100:
            scores.append(0.25)
        elif 10 <= title_len < 20:
            scores.append(0.15)
        else:
            scores.append(0.1)
        
        # 3. 元数据完整性 (0-0.25)
        metadata_score = 0
        if item.author:
            metadata_score += 0.08
        if item.publish_time:
            metadata_score += 0.08
        if item.image_url:
            metadata_score += 0.05
        if item.keywords:
            metadata_score += 0.04
        scores.append(min(metadata_score, 0.25))
        
        # 4. 来源可信度 (0-0.25)
        # 基于域名/来源评分
        trustworthy_sources = [
            "github.com", "arxiv.org", "medium.com", "dev.to",
            "techcrunch.com", "wired.com", "theverge.com",
        ]
        if any(ts in item.source.lower() for ts in trustworthy_sources):
            scores.append(0.25)
        else:
            scores.append(0.15)
        
        total_score = sum(scores)
        item.quality_score = total_score
        return total_score
    
    def score_batch(self, items: List[ContentItem]) -> List[ContentItem]:
        """批量评分"""
        for item in items:
            self.score(item)
        return items
