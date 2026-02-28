"""
配置管理模块
使用 Pydantic Settings 管理环境变量和配置
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # ===== 基础配置 =====
    app_name: str = Field(default="DailyAgent", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="info", description="日志级别")
    host: str = Field(default="0.0.0.0", description="服务绑定地址")
    port: int = Field(default=8080, description="服务端口")
    
    # ===== 数据库配置（仅支持 SQLite）=====
    database_url: str = Field(
        default=f"sqlite:///{DATA_DIR}/daily.db",
        description="SQLite数据库路径"
    )
    
    # ===== LLM 配置（新版，支持多提供商）=====
    llm_provider: str = Field(default="openai", description="LLM提供商")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API密钥")
    llm_base_url: Optional[str] = Field(default=None, description="LLM API基础URL")
    llm_model: Optional[str] = Field(default=None, description="默认LLM模型")
    
    # 兼容旧版配置
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API密钥")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI API基础URL")
    openai_model: str = Field(default="gpt-4o-mini", description="默认LLM模型")
    
    # ===== LLM 功能开关 =====
    enable_summary: bool = Field(default=True, description="启用智能摘要")
    enable_quality_check: bool = Field(default=True, description="启用质量评估")
    enable_tagging: bool = Field(default=False, description="启用智能标签")
    enable_recommendation: bool = Field(default=False, description="启用推荐优化")
    summary_length: str = Field(default="medium", description="摘要长度")
    
    # ===== LLM 性能配置 =====
    llm_max_concurrency: int = Field(default=5, description="LLM 最大并发数")
    llm_timeout: float = Field(default=30.0, description="LLM 请求超时（秒）")
    llm_cache_size: int = Field(default=1000, description="LLM 结果缓存大小")
    llm_batch_mode: bool = Field(default=True, description="启用批量 LLM 模式（一次处理多条）")
    
    # ===== 采集配置 =====
    max_concurrent_collectors: int = Field(default=5, description="最大并发采集数")
    request_delay: float = Field(default=1.0, description="请求间隔（秒）")
    content_retention_days: int = Field(default=30, description="内容保留天数")
    
    # ===== 推送配置 =====
    default_push_time: str = Field(default="09:00", description="默认推送时间")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    
    # ===== Telegram 配置 =====
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram Bot Token")
    telegram_chat_id: Optional[str] = Field(default=None, description="Telegram Chat ID")
    
    # ===== Slack 配置 =====
    slack_bot_token: Optional[str] = Field(default=None, description="Slack Bot Token")
    slack_channel: Optional[str] = Field(default=None, description="Slack频道")
    
    # ===== Discord 配置 =====
    discord_bot_token: Optional[str] = Field(default=None, description="Discord Bot Token")
    discord_channel_id: Optional[str] = Field(default=None, description="Discord频道ID")
    
    # ===== 邮件配置 =====
    smtp_host: Optional[str] = Field(default=None, description="SMTP服务器")
    smtp_port: int = Field(default=587, description="SMTP端口")
    smtp_user: Optional[str] = Field(default=None, description="SMTP用户名")
    smtp_password: Optional[str] = Field(default=None, description="SMTP密码")
    email_from: Optional[str] = Field(default=None, description="发件人地址")
    email_to: Optional[str] = Field(default=None, description="收件人地址")
    
    # ===== 安全设置 =====
    api_secret_key: str = Field(default="change-this-secret-key", description="API密钥")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed:
            raise ValueError(f"log_level 必须是以下之一: {allowed}")
        return v.lower()


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


class ColumnConfig:
    """分栏配置管理"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (CONFIG_DIR / "columns.yaml")
        self._config: Optional[dict] = None
    
    def load(self) -> dict:
        """加载分栏配置"""
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        
        return self._config
    
    def reload(self) -> dict:
        """重新加载配置"""
        self._config = None
        return self.load()
    
    def get_columns(self, enabled_only: bool = True) -> List[dict]:
        """获取分栏列表"""
        config = self.load()
        columns = config.get("columns", [])
        
        if enabled_only:
            columns = [c for c in columns if c.get("enabled", True)]
        
        # 按 order 排序
        columns.sort(key=lambda x: x.get("order", 999))
        return columns
    
    def get_column(self, column_id: str) -> Optional[dict]:
        """获取指定分栏配置"""
        columns = self.get_columns(enabled_only=False)
        for col in columns:
            if col.get("id") == column_id:
                return col
        return None
    
    def get_composition_rules(self) -> dict:
        """获取智能组合规则"""
        config = self.load()
        return config.get("composition_rules", {})
    
    def get_quality_filter(self) -> dict:
        """获取质量过滤配置"""
        config = self.load()
        return config.get("quality_filter", {})


@lru_cache()
def get_column_config() -> ColumnConfig:
    """获取分栏配置单例"""
    return ColumnConfig()


# 敏感字段列表（用于日志脱敏）
SENSITIVE_FIELDS = [
    "token", "secret", "password", "key", "credential", 
    "api_key", "auth", "passwd"
]


def mask_sensitive_data(data: dict) -> dict:
    """
    对敏感数据进行脱敏处理
    
    Args:
        data: 原始数据字典
        
    Returns:
        脱敏后的数据字典
    """
    masked = {}
    for key, value in data.items():
        key_lower = key.lower()
        is_sensitive = any(field in key_lower for field in SENSITIVE_FIELDS)
        
        if is_sensitive and isinstance(value, str) and value:
            # 保留前4位和后4位，中间用 **** 代替
            if len(value) > 10:
                masked[key] = f"{value[:4]}****{value[-4:]}"
            else:
                masked[key] = "****"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value)
        else:
            masked[key] = value
    
    return masked
