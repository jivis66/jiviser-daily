"""
用户画像管理
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import UserProfileDB, parse_json_list, dump_json_list
from src.models import ChannelType, UserProfile


class ProfileManager:
    """用户画像管理器"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_profile(self, user_id: str = "default") -> UserProfile:
        """获取用户画像"""
        result = await self.session.execute(
            select(UserProfileDB).where(UserProfileDB.user_id == user_id)
        )
        db_profile = result.scalar_one_or_none()
        
        if db_profile:
            return self._db_to_model(db_profile)
        
        # 创建默认画像
        return self._create_default_profile(user_id)
    
    async def save_profile(self, profile: UserProfile) -> UserProfile:
        """保存用户画像"""
        result = await self.session.execute(
            select(UserProfileDB).where(UserProfileDB.user_id == profile.user_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # 更新
            existing.industry = profile.industry
            existing.position = profile.position
            existing.expertise = dump_json_list(profile.expertise)
            existing.interests = dump_json_list(profile.interests)
            existing.preferred_sources = dump_json_list(profile.preferred_sources)
            existing.blocked_sources = dump_json_list(profile.blocked_sources)
            existing.keywords_include = dump_json_list(profile.keywords_include)
            existing.keywords_exclude = dump_json_list(profile.keywords_exclude)
            existing.reading_time = profile.reading_time
            existing.summary_style = profile.summary_style
            existing.content_depth = profile.content_depth
            existing.push_channels = dump_json_list([c.value for c in profile.push_channels])
            existing.push_time = profile.push_time
            existing.timezone = profile.timezone
        else:
            # 创建
            db_profile = UserProfileDB(
                user_id=profile.user_id,
                industry=profile.industry,
                position=profile.position,
                expertise=dump_json_list(profile.expertise),
                interests=dump_json_list(profile.interests),
                preferred_sources=dump_json_list(profile.preferred_sources),
                blocked_sources=dump_json_list(profile.blocked_sources),
                keywords_include=dump_json_list(profile.keywords_include),
                keywords_exclude=dump_json_list(profile.keywords_exclude),
                reading_time=profile.reading_time,
                summary_style=profile.summary_style,
                content_depth=profile.content_depth,
                push_channels=dump_json_list([c.value for c in profile.push_channels]),
                push_time=profile.push_time,
                timezone=profile.timezone,
                liked_items=dump_json_list(profile.liked_items),
                saved_items=dump_json_list(profile.saved_items),
                dismissed_items=dump_json_list(profile.dismissed_items)
            )
            self.session.add(db_profile)
        
        await self.session.commit()
        return profile
    
    async def update_interests(
        self, 
        user_id: str, 
        interests: List[str],
        append: bool = True
    ) -> UserProfile:
        """更新兴趣标签"""
        profile = await self.get_profile(user_id)
        
        if append:
            # 合并去重
            profile.interests = list(set(profile.interests + interests))
        else:
            profile.interests = interests
        
        return await self.save_profile(profile)
    
    async def add_feedback(
        self, 
        user_id: str, 
        item_id: str, 
        feedback_type: str
    ) -> UserProfile:
        """添加反馈"""
        profile = await self.get_profile(user_id)
        
        if feedback_type == "like":
            if item_id not in profile.liked_items:
                profile.liked_items.append(item_id)
        elif feedback_type == "save":
            if item_id not in profile.saved_items:
                profile.saved_items.append(item_id)
        elif feedback_type == "dismiss":
            if item_id not in profile.dismissed_items:
                profile.dismissed_items.append(item_id)
        
        return await self.save_profile(profile)
    
    def _db_to_model(self, db_profile: UserProfileDB) -> UserProfile:
        """数据库模型转业务模型"""
        channels = parse_json_list(db_profile.push_channels)
        channel_types = []
        for c in channels:
            try:
                channel_types.append(ChannelType(c))
            except ValueError:
                pass
        
        if not channel_types:
            channel_types = [ChannelType.IMARKDOWN]
        
        return UserProfile(
            user_id=db_profile.user_id,
            industry=db_profile.industry,
            position=db_profile.position,
            expertise=parse_json_list(db_profile.expertise),
            interests=parse_json_list(db_profile.interests),
            preferred_sources=parse_json_list(db_profile.preferred_sources),
            blocked_sources=parse_json_list(db_profile.blocked_sources),
            keywords_include=parse_json_list(db_profile.keywords_include),
            keywords_exclude=parse_json_list(db_profile.keywords_exclude),
            reading_time=db_profile.reading_time,
            summary_style=db_profile.summary_style,
            content_depth=db_profile.content_depth,
            push_channels=channel_types,
            push_time=db_profile.push_time,
            timezone=db_profile.timezone,
            liked_items=parse_json_list(db_profile.liked_items),
            saved_items=parse_json_list(db_profile.saved_items),
            dismissed_items=parse_json_list(db_profile.dismissed_items)
        )
    
    def _create_default_profile(self, user_id: str) -> UserProfile:
        """创建默认用户画像"""
        return UserProfile(
            user_id=user_id,
            interests=["AI", "technology", "programming"],
            summary_style="3_points",
            push_channels=[ChannelType.IMARKDOWN],
            push_time="09:00"
        )
