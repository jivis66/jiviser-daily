"""
Pydantic 数据模型定义
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ContentStatus(str, Enum):
    """内容状态"""
    PENDING = "pending"           # 待处理
    PROCESSING = "processing"     # 处理中
    PROCESSED = "processed"       # 已处理
    FAILED = "failed"             # 处理失败
    FILTERED = "filtered"         # 已过滤
    SELECTED = "selected"         # 已选中
    PUBLISHED = "published"       # 已发布


class SourceType(str, Enum):
    """数据源类型"""
    RSS = "rss"
    API = "api"
    WEB = "web"
    VIDEO = "video"           # 视频平台 (B站、YouTube等)
    SOCIAL = "social"         # 社交平台 (小红书、微博等)
    TWITTER = "twitter"
    GITHUB = "github"
    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    CUSTOM = "custom"


class ChannelType(str, Enum):
    """推送渠道类型"""
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"
    IMARKDOWN = "markdown"
    IMESSAGE = "imessage"
    WHATSAPP = "whatsapp"


class ContentItem(BaseModel):
    """内容条目模型"""
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="唯一标识")
    title: str = Field(description="标题")
    url: str = Field(description="原文链接")
    source: str = Field(description="来源名称")
    source_type: SourceType = Field(description="来源类型")
    
    # 内容信息
    content: Optional[str] = Field(default=None, description="正文内容")
    summary: Optional[str] = Field(default=None, description="摘要")
    key_points: List[str] = Field(default_factory=list, description="关键要点")
    
    # 元数据
    author: Optional[str] = Field(default=None, description="作者")
    publish_time: Optional[datetime] = Field(default=None, description="发布时间")
    fetch_time: datetime = Field(default_factory=datetime.utcnow, description="采集时间")
    
    # 分类标签
    topics: List[str] = Field(default_factory=list, description="主题标签")
    entities: List[str] = Field(default_factory=list, description="提取的实体")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    
    # 媒体信息
    image_url: Optional[str] = Field(default=None, description="封面图片")
    read_time: Optional[int] = Field(default=None, description="预估阅读时间（分钟）")
    
    # 质量评分
    quality_score: float = Field(default=0.0, description="质量评分")
    relevance_score: float = Field(default=0.0, description="相关性评分")
    popularity_score: float = Field(default=0.0, description="热度评分")
    
    # 附加数据
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="原始数据")
    extra: Dict[str, Any] = Field(default_factory=dict, description="额外字段")
    
    # 状态
    status: ContentStatus = Field(default=ContentStatus.PENDING, description="状态")
    column_id: Optional[str] = Field(default=None, description="所属分栏")
    is_duplicate: bool = Field(default=False, description="是否重复")
    duplicate_of: Optional[str] = Field(default=None, description="重复自")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserProfile(BaseModel):
    """用户画像模型"""
    
    user_id: str = Field(description="用户ID")
    
    # 基础属性
    industry: Optional[str] = Field(default=None, description="行业")
    position: Optional[str] = Field(default=None, description="职位")
    expertise: List[str] = Field(default_factory=list, description="专业领域")
    
    # 兴趣标签
    interests: List[str] = Field(default_factory=list, description="兴趣标签")
    preferred_sources: List[str] = Field(default_factory=list, description="偏好来源")
    blocked_sources: List[str] = Field(default_factory=list, description="屏蔽来源")
    keywords_include: List[str] = Field(default_factory=list, description="包含关键词")
    keywords_exclude: List[str] = Field(default_factory=list, description="排除关键词")
    
    # 行为偏好
    reading_time: Optional[str] = Field(default=None, description="偏好阅读时段")
    summary_style: str = Field(default="3_points", description="摘要风格")
    content_depth: str = Field(default="medium", description="内容深度偏好")
    
    # 推送设置
    push_channels: List[ChannelType] = Field(
        default_factory=lambda: [ChannelType.IMARKDOWN],
        description="推送渠道"
    )
    push_time: str = Field(default="09:00", description="推送时间")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    
    # 交互历史
    liked_items: List[str] = Field(default_factory=list, description="点赞的内容")
    saved_items: List[str] = Field(default_factory=list, description="收藏的内容")
    dismissed_items: List[str] = Field(default_factory=list, description="屏蔽的内容")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DailyReport(BaseModel):
    """日报模型"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    date: datetime = Field(description="日报日期")
    user_id: str = Field(description="用户ID")
    
    # 内容
    columns: List[Dict[str, Any]] = Field(default_factory=list, description="分栏内容")
    total_items: int = Field(default=0, description="总条目数")
    
    # 元信息
    title: str = Field(default="今日日报", description="日报标题")
    summary: Optional[str] = Field(default=None, description="日报概述")
    highlights: List[str] = Field(default_factory=list, description="今日亮点")
    
    # 统计
    sources_count: int = Field(default=0, description="来源数")
    topics_count: int = Field(default=0, description="主题数")
    
    # 状态
    is_generated: bool = Field(default=False, description="是否已生成")
    is_sent: bool = Field(default=False, description="是否已发送")
    sent_at: Optional[datetime] = Field(default=None, description="发送时间")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FilterConfig(BaseModel):
    """内容过滤配置"""
    
    keywords: List[str] = Field(default_factory=list, description="包含关键词")
    exclude: List[str] = Field(default_factory=list, description="排除关键词")
    min_score: Optional[int] = Field(default=None, description="最小分数")
    min_likes: Optional[int] = Field(default=None, description="最小点赞数")
    time_range_hours: Optional[int] = Field(default=None, description="时间范围（小时）")


class CollectorConfig(BaseModel):
    """采集器配置"""
    
    name: str = Field(description="采集器名称")
    type: SourceType = Field(description="采集器类型")
    url: Optional[str] = Field(default=None, description="数据源URL")
    weight: float = Field(default=1.0, description="权重")
    filter: FilterConfig = Field(default_factory=FilterConfig, description="过滤配置")
    params: Dict[str, Any] = Field(default_factory=dict, description="额外参数")
    enabled: bool = Field(default=True, description="是否启用")
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("weight 必须在 0-1 之间")
        return v


class PushMessage(BaseModel):
    """推送消息模型"""
    
    title: str = Field(description="消息标题")
    content: str = Field(description="消息内容")
    channel: ChannelType = Field(description="推送渠道")
    
    # 可选字段
    html_content: Optional[str] = Field(default=None, description="HTML内容")
    markdown_content: Optional[str] = Field(default=None, description="Markdown内容")
    image_url: Optional[str] = Field(default=None, description="图片URL")
    
    # 按钮/交互
    buttons: List[Dict[str, str]] = Field(default_factory=list, description="交互按钮")
    
    # 目标
    user_id: Optional[str] = Field(default=None, description="目标用户ID")
    chat_id: Optional[str] = Field(default=None, description="目标聊天ID")


class HealthStatus(BaseModel):
    """健康状态模型"""
    
    status: str = Field(default="healthy", description="状态")
    version: str = Field(default="1.0.0", description="版本")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # 组件状态
    database: bool = Field(default=True, description="数据库状态")
    redis: bool = Field(default=True, description="Redis状态")
    llm: bool = Field(default=True, description="LLM服务状态")
    
    # 统计
    uptime_seconds: int = Field(default=0, description="运行时间（秒）")
    total_collected: int = Field(default=0, description="累计采集数")
    total_processed: int = Field(default=0, description="累计处理数")


# API 请求/响应模型

class GenerateReportRequest(BaseModel):
    """生成日报请求"""
    user_id: Optional[str] = Field(default="default")
    date: Optional[datetime] = None
    columns: Optional[List[str]] = None
    force_refresh: bool = Field(default=False, description="强制刷新")


class GenerateReportResponse(BaseModel):
    """生成日报响应"""
    success: bool
    report_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    """用户反馈请求"""
    user_id: str
    item_id: str
    feedback_type: str = Field(description="反馈类型: like/dislike/save/dismiss")
    comment: Optional[str] = None


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    user_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
