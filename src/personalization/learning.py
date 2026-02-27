"""
兴趣学习模块
根据用户行为学习和更新兴趣偏好
"""
from collections import Counter
from typing import Dict, List, Set, Tuple

from src.models import ContentItem, UserProfile


class InterestLearner:
    """兴趣学习器"""
    
    def __init__(self):
        # 行为权重
        self.weights = {
            "like": 3.0,      # 点赞
            "save": 5.0,      # 收藏
            "dismiss": -2.0,  # 屏蔽
            "click": 1.0,     # 点击
            "read_time": 0.1  # 阅读时长（每分钟）
        }
    
    def learn_from_interactions(
        self,
        profile: UserProfile,
        interactions: List[Tuple[ContentItem, str, float]]
    ) -> UserProfile:
        """
        从交互记录中学习
        
        Args:
            profile: 用户画像
            interactions: [(内容, 行为类型, 权重), ...]
            
        Returns:
            UserProfile: 更新后的画像
        """
        # 统计关键词得分
        keyword_scores: Counter = Counter()
        topic_scores: Counter = Counter()
        source_scores: Counter = Counter()
        
        for item, action, weight in interactions:
            action_weight = self.weights.get(action, 1.0) * weight
            
            # 关键词得分
            for kw in item.keywords:
                keyword_scores[kw] += action_weight
            
            # 主题得分
            for topic in item.topics:
                topic_scores[topic] += action_weight
            
            # 来源得分
            source_scores[item.source] += action_weight
        
        # 更新画像
        # 1. 更新兴趣标签
        if keyword_scores:
            # 获取高频关键词
            top_keywords = [kw for kw, _ in keyword_scores.most_common(20)]
            profile.interests = self._merge_interests(profile.interests, top_keywords)
        
        # 2. 更新偏好来源
        if source_scores:
            # 正分的来源加入偏好
            preferred = [s for s, score in source_scores.items() if score > 0]
            profile.preferred_sources = list(set(profile.preferred_sources + preferred))
            
            # 负分过多的来源加入屏蔽
            blocked = [s for s, score in source_scores.items() if score < -5]
            profile.blocked_sources = list(set(profile.blocked_sources + blocked))
        
        return profile
    
    def learn_from_feedback(
        self,
        profile: UserProfile,
        item: ContentItem,
        feedback_type: str
    ) -> UserProfile:
        """
        从单条反馈学习
        
        Args:
            profile: 用户画像
            item: 内容
            feedback_type: 反馈类型
            
        Returns:
            UserProfile: 更新后的画像
        """
        if feedback_type == "like":
            # 将内容的关键词加入兴趣
            profile.interests = self._merge_interests(
                profile.interests, 
                item.keywords[:5]
            )
            
            # 来源加分
            if item.source not in profile.preferred_sources:
                profile.preferred_sources.append(item.source)
        
        elif feedback_type == "dismiss":
            # 分析屏蔽原因
            # 如果是特定来源的内容，可能不喜欢该来源
            source_dismiss_count = self._count_source_in_list(
                item.source, 
                profile.dismissed_items
            )
            if source_dismiss_count >= 3:
                if item.source not in profile.blocked_sources:
                    profile.blocked_sources.append(item.source)
            
            # 排除关键词
            profile.keywords_exclude = self._merge_keywords(
                profile.keywords_exclude,
                item.keywords[:3]
            )
        
        return profile
    
    def detect_interest_drift(
        self,
        profile: UserProfile,
        recent_items: List[ContentItem]
    ) -> Tuple[bool, List[str]]:
        """
        检测兴趣漂移
        
        Args:
            profile: 用户画像
            recent_items: 最近消费的内容
            
        Returns:
            (是否漂移, 新兴趣列表)
        """
        if not recent_items:
            return False, []
        
        # 统计最近内容的主题
        recent_topics: Counter = Counter()
        for item in recent_items:
            recent_topics.update(item.topics)
        
        # 对比当前兴趣
        current_topics = set(profile.interests)
        new_topics = []
        
        for topic, count in recent_topics.most_common(5):
            if topic not in current_topics and count >= 3:
                new_topics.append(topic)
        
        has_drift = len(new_topics) >= 2
        return has_drift, new_topics
    
    def calculate_similarity(
        self, 
        item: ContentItem, 
        profile: UserProfile
    ) -> float:
        """
        计算内容与用户画像的相似度
        
        Args:
            item: 内容
            profile: 用户画像
            
        Returns:
            float: 相似度分数 (0-1)
        """
        score = 0.0
        total = 0.0
        
        # 1. 兴趣标签匹配
        if profile.interests:
            total += 1.0
            matches = sum(1 for i in profile.interests if i in item.keywords)
            score += (matches / len(profile.interests)) * 1.0
        
        # 2. 专业领域匹配
        if profile.expertise:
            total += 1.0
            matches = sum(1 for e in profile.expertise if e in item.topics)
            score += (matches / len(profile.expertise)) * 1.0
        
        # 3. 来源偏好
        if profile.preferred_sources:
            total += 0.5
            if item.source in profile.preferred_sources:
                score += 0.5
        
        # 4. 排除关键词（扣分）
        if profile.keywords_exclude:
            exclude_matches = sum(
                1 for k in profile.keywords_exclude if k in item.keywords
            )
            score -= exclude_matches * 0.1
        
        # 归一化
        if total > 0:
            score = max(0, min(1, score / total))
        
        return score
    
    def _merge_interests(
        self, 
        existing: List[str], 
        new: List[str],
        max_count: int = 30
    ) -> List[str]:
        """合并兴趣标签"""
        merged = list(set(existing + new))
        # 限制数量
        if len(merged) > max_count:
            # 保留原来的，新加的截断
            return merged[:max_count]
        return merged
    
    def _merge_keywords(self, existing: List[str], new: List[str]) -> List[str]:
        """合并关键词"""
        return list(set(existing + new))
    
    def _count_source_in_list(self, source: str, item_ids: List[str]) -> int:
        """统计来源在列表中的数量（简化实现）"""
        # 实际实现需要从 item_ids 获取内容并统计来源
        # 这里简化返回 0
        return 0


class ColdStartHandler:
    """冷启动处理器"""
    
    # 预设的兴趣模板
    TEMPLATES = {
        "tech_enthusiast": {
            "interests": ["AI", "programming", "technology", "startup", "innovation"],
            "preferred_sources": ["GitHub", "Hacker News", "TechCrunch"],
            "summary_style": "3_points"
        },
        "developer": {
            "interests": ["programming", "open source", "software engineering", "cloud"],
            "preferred_sources": ["GitHub", "Dev.to", "Stack Overflow"],
            "summary_style": "paragraph"
        },
        "business_analyst": {
            "interests": ["business", "market", "investment", "startup", "finance"],
            "preferred_sources": ["Bloomberg", "Forbes", "36氪"],
            "summary_style": "1_sentence"
        },
        "researcher": {
            "interests": ["AI research", "machine learning", "deep learning", "science"],
            "preferred_sources": ["arXiv", "Papers With Code", "Google Research"],
            "summary_style": "detailed"
        }
    }
    
    def get_template(self, template_id: str) -> Dict:
        """获取兴趣模板"""
        return self.TEMPLATES.get(template_id, self.TEMPLATES["tech_enthusiast"])
    
    def apply_template(
        self, 
        profile: UserProfile, 
        template_id: str
    ) -> UserProfile:
        """应用模板到用户画像"""
        template = self.get_template(template_id)
        
        profile.interests = template.get("interests", [])
        profile.preferred_sources = template.get("preferred_sources", [])
        profile.summary_style = template.get("summary_style", "3_points")
        
        return profile
    
    def recommend_template(self, answers: Dict[str, str]) -> str:
        """
        根据问卷答案推荐模板
        
        Args:
            answers: {"q1": "answer", ...}
            
        Returns:
            str: 模板 ID
        """
        role = answers.get("role", "").lower()
        
        if "developer" in role or "programmer" in role:
            return "developer"
        elif "business" in role or "analyst" in role:
            return "business_analyst"
        elif "researcher" in role or "scientist" in role:
            return "researcher"
        else:
            return "tech_enthusiast"
