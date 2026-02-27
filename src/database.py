"""
数据库模型和会话管理
使用 SQLAlchemy 2.0 语法
"""
import json
from datetime import datetime, timedelta
from typing import AsyncGenerator, List, Optional

from sqlalchemy import (
    JSON, DateTime, Float, ForeignKey, Integer, String, Text, 
    create_engine, select, delete, func
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


class ContentItemDB(Base):
    """内容条目表"""
    __tablename__ = "content_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2000), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    publish_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    fetch_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    entities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    image_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    read_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    raw_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    column_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    is_duplicate: Mapped[bool] = mapped_column(default=False)
    duplicate_of: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    daily_reports = relationship("DailyReportItemDB", back_populates="content_item")


class DailyReportDB(Base):
    """日报表"""
    __tablename__ = "daily_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(200), default="今日日报")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    highlights: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    sources_count: Mapped[int] = mapped_column(Integer, default=0)
    topics_count: Mapped[int] = mapped_column(Integer, default=0)
    
    is_generated: Mapped[bool] = mapped_column(default=False)
    is_sent: Mapped[bool] = mapped_column(default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    items = relationship("DailyReportItemDB", back_populates="daily_report")


class DailyReportItemDB(Base):
    """日报-内容关联表"""
    __tablename__ = "daily_report_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("daily_reports.id"), index=True)
    content_id: Mapped[str] = mapped_column(String(36), ForeignKey("content_items.id"), index=True)
    column_id: Mapped[str] = mapped_column(String(50), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    daily_report = relationship("DailyReportDB", back_populates="items")
    content_item = relationship("ContentItemDB", back_populates="daily_reports")


class UserProfileDB(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"
    
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expertise: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    interests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    preferred_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    blocked_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    keywords_include: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    keywords_exclude: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    reading_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    summary_style: Mapped[str] = mapped_column(String(50), default="3_points")
    content_depth: Mapped[str] = mapped_column(String(50), default="medium")
    
    push_channels: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    push_time: Mapped[str] = mapped_column(String(10), default="09:00")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Shanghai")
    
    liked_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    saved_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    dismissed_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserFeedbackDB(Base):
    """用户反馈表"""
    __tablename__ = "user_feedback"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)  # like/dislike/save/dismiss
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# 数据库引擎和会话工厂
_engine = None
_async_session_maker = None


def get_database_url() -> str:
    """获取异步数据库URL"""
    url = settings.database_url
    # 转换 SQLite URL 为异步版本
    if url.startswith("sqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def init_engine():
    """初始化数据库引擎"""
    global _engine
    if _engine is None:
        url = get_database_url()
        _engine = create_async_engine(
            url,
            echo=settings.debug,
            future=True
        )
    return _engine


async def init_db():
    """初始化数据库表"""
    engine = init_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入使用）"""
    global _async_session_maker
    if _async_session_maker is None:
        engine = init_engine()
        _async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class ContentRepository:
    """内容仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, item: ContentItemDB) -> ContentItemDB:
        """创建内容条目"""
        self.session.add(item)
        await self.session.flush()
        return item
    
    async def get_by_id(self, item_id: str) -> Optional[ContentItemDB]:
        """根据ID获取内容"""
        result = await self.session.execute(
            select(ContentItemDB).where(ContentItemDB.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_url(self, url: str) -> Optional[ContentItemDB]:
        """根据URL获取内容"""
        result = await self.session.execute(
            select(ContentItemDB).where(ContentItemDB.url == url)
        )
        return result.scalar_one_or_none()
    
    async def get_by_column(
        self, 
        column_id: str, 
        date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ContentItemDB]:
        """获取分栏内容"""
        query = select(ContentItemDB).where(ContentItemDB.column_id == column_id)
        
        if date:
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            query = query.where(ContentItemDB.fetch_time >= start, ContentItemDB.fetch_time < end)
        
        if status:
            query = query.where(ContentItemDB.status == status)
        
        query = query.order_by(ContentItemDB.quality_score.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, item: ContentItemDB) -> ContentItemDB:
        """更新内容"""
        await self.session.flush()
        return item
    
    async def delete_old(self, days: int) -> int:
        """删除旧内容"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            delete(ContentItemDB).where(ContentItemDB.fetch_time < cutoff)
        )
        return result.rowcount
    
    async def count_by_status(self, status: str) -> int:
        """统计状态数量"""
        result = await self.session.execute(
            select(func.count()).where(ContentItemDB.status == status)
        )
        return result.scalar()


class DailyReportRepository:
    """日报仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, report: DailyReportDB) -> DailyReportDB:
        """创建日报"""
        self.session.add(report)
        await self.session.flush()
        return report
    
    async def get_by_id(self, report_id: str) -> Optional[DailyReportDB]:
        """根据ID获取日报"""
        result = await self.session.execute(
            select(DailyReportDB).where(DailyReportDB.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_date(
        self, 
        user_id: str, 
        date: datetime
    ) -> Optional[DailyReportDB]:
        """根据日期获取日报"""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        result = await self.session.execute(
            select(DailyReportDB).where(
                DailyReportDB.user_id == user_id,
                DailyReportDB.date >= start,
                DailyReportDB.date < end
            )
        )
        return result.scalar_one_or_none()
    
    async def update(self, report: DailyReportDB) -> DailyReportDB:
        """更新日报"""
        await self.session.flush()
        return report
    
    async def add_item(self, report_item: DailyReportItemDB) -> DailyReportItemDB:
        """添加日报条目"""
        self.session.add(report_item)
        await self.session.flush()
        return report_item


# JSON 辅助函数

def parse_json_list(data: Optional[str]) -> List[str]:
    """解析 JSON 列表字符串"""
    if not data:
        return []
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return []


def dump_json_list(data: List) -> str:
    """转储列表为 JSON 字符串"""
    return json.dumps(data, ensure_ascii=False)
