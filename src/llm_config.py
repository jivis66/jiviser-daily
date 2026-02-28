"""
LLM 配置管理模块
提供交互式 LLM 配置向导和配置管理功能
"""
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

console = Console()


class LLMProvider(Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    GEMINI = "gemini"
    MOONSHOT = "moonshot"
    QWEN = "qwen"
    GLM = "glm"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    AZURE = "azure"
    BAIDU = "baidu"
    ALIYUN = "aliyun"
    ZHIPU = "zhipu"
    SKIP = "skip"


@dataclass
class LLMModelInfo:
    """模型信息"""
    id: str
    name: str
    description: str
    price_hint: str
    context_length: int = 4096
    recommended: bool = False


@dataclass
class LLMProviderConfig:
    """LLM 提供商配置"""
    key: str
    display_name: str
    emoji: str
    description: str
    requires_api_key: bool = True
    base_url_hint: Optional[str] = None
    models: List[LLMModelInfo] = field(default_factory=list)
    help_text: str = ""


# 提供商配置
PROVIDER_CONFIGS: Dict[LLMProvider, LLMProviderConfig] = {
    LLMProvider.OPENAI: LLMProviderConfig(
        key="openai",
        display_name="OpenAI",
        emoji="🌐",
        description="稳定、高质量、速度快",
        requires_api_key=True,
        base_url_hint="https://api.openai.com/v1",
        models=[
            LLMModelInfo("gpt-4o-mini", "GPT-4o-mini", "性价比高，适合日常使用", "$0.15 / 1M tokens", 128000, True),
            LLMModelInfo("gpt-4o", "GPT-4o", "最强性能，适合重要内容", "$5.00 / 1M tokens", 128000),
            LLMModelInfo("gpt-4-turbo", "GPT-4 Turbo", "平衡性能与价格", "$10.00 / 1M tokens", 128000),
            LLMModelInfo("gpt-3.5-turbo", "GPT-3.5 Turbo", "成本敏感", "$0.50 / 1M tokens", 16385),
        ],
        help_text="""
📖 获取 API Key 步骤：
   1. 访问 https://platform.openai.com/api-keys
   2. 登录您的 OpenAI 账号
   3. 点击 "Create new secret key"
   4. 复制生成的密钥
        """
    ),
    LLMProvider.GEMINI: LLMProviderConfig(
        key="gemini",
        display_name="Google Gemini",
        emoji="🔷",
        description="Google 出品，多模态能力强",
        requires_api_key=True,
        base_url_hint="https://generativelanguage.googleapis.com/v1beta",
        models=[
            LLMModelInfo("gemini-2.0-flash", "Gemini 2.0 Flash", "速度快，适合日常使用", "免费/低价", 1000000, True),
            LLMModelInfo("gemini-1.5-pro", "Gemini 1.5 Pro", "Google 最强模型", "$1.25 / 1M tokens", 2000000),
            LLMModelInfo("gemini-1.5-flash", "Gemini 1.5 Flash", "性价比高", "$0.075 / 1M tokens", 1000000),
        ],
        help_text="""
📖 获取 API Key 步骤：
   1. 访问 https://aistudio.google.com/app/apikey
   2. 登录 Google 账号
   3. 点击 "Create API Key"
   4. 复制生成的密钥
        """
    ),
    LLMProvider.MOONSHOT: LLMProviderConfig(
        key="moonshot",
        display_name="Kimi (月之暗面)",
        emoji="🌙",
        description="国产长文本专家，中文能力强",
        requires_api_key=True,
        base_url_hint="https://api.moonshot.cn/v1",
        models=[
            LLMModelInfo("moonshot-v1-8k", "Kimi K1 (8K)", "轻量快速", "按量计费", 8192),
            LLMModelInfo("moonshot-v1-32k", "Kimi K1 (32K)", "平衡选择", "按量计费", 32768),
            LLMModelInfo("moonshot-v1-128k", "Kimi K1 (128K)", "长文本专家", "按量计费", 128000, True),
        ],
        help_text="""
📖 获取 API Key 步骤：
   1. 访问 https://platform.moonshot.cn/
   2. 注册/登录 Kimi 开放平台账号
   3. 在 "API Key 管理" 页面创建 Key
   4. 复制生成的密钥
        """
    ),
    LLMProvider.QWEN: LLMProviderConfig(
        key="qwen",
        display_name="通义千问 (阿里)",
        emoji="🤖",
        description="中文优化，阿里出品",
        requires_api_key=True,
        base_url_hint="https://dashscope.aliyuncs.com/compatible-mode/v1",
        models=[
            LLMModelInfo("qwen-max", "Qwen Max", "阿里最强模型", "按量计费", 32768, True),
            LLMModelInfo("qwen-plus", "Qwen Plus", "平衡性能价格", "按量计费", 131072),
            LLMModelInfo("qwen-turbo", "Qwen Turbo", "高性价比", "按量计费", 65536),
        ],
        help_text="""
📖 获取 API Key 步骤：
   1. 访问 https://help.aliyun.com/zh/dashscope/
   2. 注册阿里云账号
   3. 开通 DashScope 服务
   4. 创建 API Key
        """
    ),
    LLMProvider.GLM: LLMProviderConfig(
        key="glm",
        display_name="智谱 GLM",
        emoji="🧠",
        description="中文对话模型，智谱 AI 出品",
        requires_api_key=True,
        base_url_hint="https://open.bigmodel.cn/api/paas/v4",
        models=[
            LLMModelInfo("glm-4", "GLM-4", "智谱最强模型", "按量计费", 128000, True),
            LLMModelInfo("glm-4-air", "GLM-4 Air", "高性价比", "按量计费", 128000),
            LLMModelInfo("glm-4-flash", "GLM-4 Flash", "轻量快速", "按量计费", 128000),
        ],
        help_text="""
📖 获取 API Key 步骤：
   1. 访问 https://open.bigmodel.cn/
   2. 注册智谱账号
   3. 在 "API Keys" 页面创建 Key
   4. 复制生成的密钥
        """
    ),
    LLMProvider.OPENROUTER: LLMProviderConfig(
        key="openrouter",
        display_name="OpenRouter",
        emoji="🔗",
        description="聚合多厂商、性价比高",
        requires_api_key=True,
        base_url_hint="https://openrouter.ai/api/v1",
        models=[
            LLMModelInfo("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet", "推荐，推理能力强", "$3.00 / 1M tokens", 200000, True),
            LLMModelInfo("openai/gpt-4o", "GPT-4o", "OpenAI 最强模型", "$5.00 / 1M tokens", 128000),
            LLMModelInfo("google/gemini-pro", "Gemini Pro", "Google 大模型", "$0.50 / 1M tokens", 128000),
            LLMModelInfo("moonshot/kimi-k2", "Kimi K2", "国产长文本模型", "$0.50 / 1M tokens", 200000),
        ],
        help_text="""
📖 获取 API Key 步骤：
   1. 访问 https://openrouter.ai/keys
   2. 注册/登录 OpenRouter 账号
   3. 创建新的 API Key
   4. 复制生成的密钥
        """
    ),
    LLMProvider.OLLAMA: LLMProviderConfig(
        key="ollama",
        display_name="Ollama (本地部署)",
        emoji="🏠",
        description="免费、隐私安全、无需网络",
        requires_api_key=False,
        base_url_hint="http://localhost:11434",
        models=[
            LLMModelInfo("qwen2.5:14b", "Qwen 2.5 (14B)", "中文推荐，阿里开源", "免费", 32768, True),
            LLMModelInfo("llama3.2:8b", "Llama 3.2 (8B)", "英文推荐，Meta开源", "免费", 128000),
            LLMModelInfo("mistral:7b", "Mistral (7B)", "平衡选择，欧洲开源", "免费", 32768),
            LLMModelInfo("phi4:14b", "Phi-4 (14B)", "微软开源，小巧强大", "免费", 16384),
        ],
        help_text="""
📖 Ollama 安装步骤：
   1. 安装 Ollama: curl -fsSL https://ollama.com/install.sh | sh
   2. 拉取模型: ollama pull qwen2.5:14b
   3. 验证运行: ollama run qwen2.5:14b
   4. 确保服务在 http://localhost:11434 运行
        """
    ),
    LLMProvider.AZURE: LLMProviderConfig(
        key="azure",
        display_name="Azure OpenAI",
        emoji="☁️",
        description="企业级、SLA保障",
        requires_api_key=True,
        base_url_hint="https://your-resource.openai.azure.com",
        models=[
            LLMModelInfo("gpt-4o", "GPT-4o", "Azure 托管的 GPT-4o", "按部署计费", 128000, True),
            LLMModelInfo("gpt-4", "GPT-4", "Azure 托管的 GPT-4", "按部署计费", 8192),
            LLMModelInfo("gpt-35-turbo", "GPT-3.5 Turbo", "Azure 托管的 GPT-3.5", "按部署计费", 16385),
        ],
        help_text="""
📖 Azure OpenAI 配置步骤：
   1. 访问 Azure Portal (https://portal.azure.com)
   2. 创建 Azure OpenAI 服务
   3. 在 "Keys and Endpoint" 获取 API Key
   4. 记录 Endpoint URL
   5. 部署模型并记录部署名称
        """
    ),
    LLMProvider.BAIDU: LLMProviderConfig(
        key="baidu",
        display_name="文心一言 (百度)",
        emoji="🇨🇳",
        description="中文优化、国内访问快",
        requires_api_key=True,
        models=[
            LLMModelInfo("ernie-bot-4", "ERNIE Bot 4.0", "百度最强模型", "按量计费", 8192, True),
            LLMModelInfo("ernie-bot", "ERNIE Bot", "百度标准模型", "按量计费", 8192),
        ],
        help_text="""
📖 文心一言 API Key 获取：
   1. 访问 https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ilkkrb0i5
   2. 注册百度智能云账号
   3. 创建应用获取 API Key 和 Secret Key
        """
    ),
    LLMProvider.ALIYUN: LLMProviderConfig(
        key="aliyun",
        display_name="通义千问 (旧版)",
        emoji="🇨🇳",
        description="已迁移到 Qwen 独立配置，请使用新版",
        requires_api_key=True,
        models=[
            LLMModelInfo("qwen-max", "Qwen Max", "阿里最强模型", "按量计费", 32768, True),
        ],
        help_text="""
⚠️ 提示：建议直接使用 Qwen 配置，支持更多模型选项
        """
    ),
    LLMProvider.ZHIPU: LLMProviderConfig(
        key="zhipu",
        display_name="智谱 AI (旧版)",
        emoji="🇨🇳",
        description="已迁移到 GLM 独立配置，请使用新版",
        requires_api_key=True,
        models=[
            LLMModelInfo("glm-4", "GLM-4", "智谱最强模型", "按量计费", 128000, True),
        ],
        help_text="""
⚠️ 提示：建议直接使用 GLM 配置，支持更多模型选项
        """
    ),
}


@dataclass
class LLMConfig:
    """LLM 配置数据类"""
    provider: str = ""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = ""
    api_version: Optional[str] = None  # Azure 专用
    deployment: Optional[str] = None   # Azure 专用
    secret_key: Optional[str] = None   # 百度专用
    
    # 功能开关
    enable_summary: bool = True
    enable_quality_check: bool = True
    enable_tagging: bool = False
    enable_recommendation: bool = False
    
    # 摘要设置
    summary_length: str = "medium"  # short/medium/long
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.provider and self.model)
    
    def get_masked_api_key(self) -> str:
        """获取脱敏的 API Key"""
        if not self.api_key:
            return "未设置"
        if len(self.api_key) <= 8:
            return "****"
        return f"{self.api_key[:4]}****{self.api_key[-4:]}"


class LLMConfigManager:
    """LLM 配置管理器"""
    
    ENV_FILE_PATH = Path(__file__).parent.parent / ".env"
    
    def __init__(self):
        self.config = LLMConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        from src.config import get_settings
        import os
        
        settings = get_settings()
        
        # 检测提供商（优先检查特定的 LLM_PROVIDER 变量）
        provider = os.getenv("LLM_PROVIDER", "").lower()
        
        if provider:
            self.config.provider = provider
            self.config.api_key = os.getenv("LLM_API_KEY", "")
            self.config.base_url = os.getenv("LLM_BASE_URL", "")
            self.config.model = os.getenv("LLM_MODEL", "")
        elif settings.openai_api_key:
            # 兼容旧版配置方式
            if settings.openai_base_url and "openrouter" in settings.openai_base_url:
                self.config.provider = "openrouter"
            elif settings.openai_base_url and "azure" in settings.openai_base_url:
                self.config.provider = "azure"
            elif settings.openai_base_url and "moonshot" in settings.openai_base_url:
                self.config.provider = "moonshot"
            elif settings.openai_base_url and "generativelanguage" in settings.openai_base_url:
                self.config.provider = "gemini"
            elif settings.openai_base_url and "bigmodel" in settings.openai_base_url:
                self.config.provider = "glm"
            elif settings.openai_base_url and "dashscope" in settings.openai_base_url:
                self.config.provider = "qwen"
            else:
                self.config.provider = "openai"
            
            self.config.api_key = settings.openai_api_key
            self.config.base_url = settings.openai_base_url
            self.config.model = settings.openai_model or "gpt-4o-mini"
        
        # 加载功能开关配置（从 Settings 读取）
        self.config.enable_summary = settings.enable_summary
        self.config.enable_quality_check = settings.enable_quality_check
        self.config.enable_tagging = settings.enable_tagging
        self.config.enable_recommendation = settings.enable_recommendation
        self.config.summary_length = settings.summary_length
    
    def get_current_config(self) -> LLMConfig:
        """获取当前配置"""
        return self.config
    
    def save_config(self, config: LLMConfig):
        """保存配置到 .env 文件"""
        self.config = config
        
        # 读取现有 .env 内容
        env_content = {}
        if self.ENV_FILE_PATH.exists():
            with open(self.ENV_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key] = value
        
        # 更新 LLM 相关配置
        if config.provider == "skip":
            # 删除 LLM 配置
            for key in ["LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL",
                       "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"]:
                env_content.pop(key, None)
        else:
            # 使用新的配置格式
            env_content["LLM_PROVIDER"] = config.provider
            env_content["LLM_API_KEY"] = config.api_key or ""
            env_content["LLM_MODEL"] = config.model or ""
            
            if config.base_url:
                env_content["LLM_BASE_URL"] = config.base_url
            elif "LLM_BASE_URL" in env_content:
                del env_content["LLM_BASE_URL"]
            
            # 同时保留兼容旧版的配置
            env_content["OPENAI_API_KEY"] = config.api_key or ""
            env_content["OPENAI_MODEL"] = config.model or ""
            if config.base_url:
                env_content["OPENAI_BASE_URL"] = config.base_url
            elif "OPENAI_BASE_URL" in env_content:
                del env_content["OPENAI_BASE_URL"]
            
            # 保存功能开关配置
            env_content["ENABLE_SUMMARY"] = str(config.enable_summary).lower()
            env_content["ENABLE_QUALITY_CHECK"] = str(config.enable_quality_check).lower()
            env_content["ENABLE_TAGGING"] = str(config.enable_tagging).lower()
            env_content["ENABLE_RECOMMENDATION"] = str(config.enable_recommendation).lower()
            env_content["SUMMARY_LENGTH"] = config.summary_length
        
        # 写入文件
        with open(self.ENV_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("# =====================================\n")
            f.write("# Daily Agent 环境变量配置\n")
            f.write("# =====================================\n\n")
            
            # 分组写入
            groups = {
                "服务配置": ["APP_NAME", "DEBUG", "LOG_LEVEL", "HOST", "PORT"],
                "数据库配置": ["DATABASE_URL"],
                "LLM 配置": ["LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", 
                            "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"],
                "LLM 功能开关": ["ENABLE_SUMMARY", "ENABLE_QUALITY_CHECK", "ENABLE_TAGGING", 
                                "ENABLE_RECOMMENDATION", "SUMMARY_LENGTH"],
                "采集配置": ["MAX_CONCURRENT_COLLECTORS", "REQUEST_DELAY", "CONTENT_RETENTION_DAYS"],
                "推送配置": ["DEFAULT_PUSH_TIME", "TIMEZONE"],
                "Telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
                "Slack": ["SLACK_BOT_TOKEN", "SLACK_CHANNEL"],
                "Discord": ["DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID"],
                "邮件": ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"],
                "安全": ["API_SECRET_KEY"],
            }
            
            written_keys = set()
            for group_name, keys in groups.items():
                f.write(f"# ===== {group_name} =====\n")
                for key in keys:
                    if key in env_content:
                        f.write(f"{key}={env_content[key]}\n")
                        written_keys.add(key)
                f.write("\n")
            
            # 写入其他未分组的配置
            other_keys = set(env_content.keys()) - written_keys
            if other_keys:
                f.write("# ===== 其他配置 =====\n")
                for key in sorted(other_keys):
                    f.write(f"{key}={env_content[key]}\n")
        
        # 设置文件权限（仅限 Unix）
        try:
            os.chmod(self.ENV_FILE_PATH, 0o600)
        except Exception:
            pass
        
        # 清除 settings 缓存，确保重新加载配置
        from src.config import get_settings
        get_settings.cache_clear()
    
    async def test_connection(self, config: Optional[LLMConfig] = None) -> Tuple[bool, str]:
        """测试 LLM 连接"""
        test_config = config or self.config
        
        if not test_config.is_configured():
            return False, "未配置 LLM"
        
        if test_config.provider == "skip":
            return True, "已跳过 LLM 配置"
        
        if test_config.provider == "ollama":
            return await self._test_ollama(test_config)
        
        return await self._test_openai_compatible(test_config)
    
    async def _test_ollama(self, config: LLMConfig) -> Tuple[bool, str]:
        """测试 Ollama 连接"""
        base_url = config.base_url or "http://localhost:11434"
        
        console.print(f"  [dim]→ 连接地址: {base_url}[/dim]")
        console.print(f"  [dim]→ 测试模型: {config.model}[/dim]")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                console.print("  [dim]→ 获取模型列表...[/dim]")
                
                # 测试服务是否运行
                response = await client.get(f"{base_url}/api/tags")
                console.print(f"  [dim]→ 响应状态: {response.status_code}[/dim]")
                
                if response.status_code != 200:
                    return False, f"Ollama 服务返回错误: {response.status_code}"
                
                # 检查模型是否存在
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                console.print(f"  [dim]→ 已安装模型: {', '.join(models[:5])}[/dim]")
                
                if config.model not in models:
                    return False, f"模型 {config.model} 未找到。已安装模型: {', '.join(models[:5])}"
                
                console.print("  [dim]→ 测试模型生成...[/dim]")
                
                # 简单测试生成
                test_response = await client.post(
                    f"{base_url}/api/generate",
                    json={"model": config.model, "prompt": "Hi", "stream": False},
                    timeout=30.0
                )
                
                console.print(f"  [dim]→ 生成测试状态: {test_response.status_code}[/dim]")
                
                if test_response.status_code == 200:
                    return True, f"Ollama 连接正常，模型 {config.model} 可用"
                else:
                    return False, f"模型测试失败: {test_response.status_code}"
                    
        except httpx.ConnectError as e:
            console.print(f"  [dim]→ 连接失败: {e}[/dim]")
            return False, f"无法连接到 Ollama 服务 ({base_url})，请确认服务已启动"
        except Exception as e:
            console.print(f"  [dim]→ 异常: {type(e).__name__}: {e}[/dim]")
            return False, f"测试失败: {str(e)}"
    
    async def _test_openai_compatible(self, config: LLMConfig) -> Tuple[bool, str]:
        """测试 OpenAI 兼容 API"""
        if not config.api_key:
            return False, "未设置 API Key"
        
        base_url = config.base_url or "https://api.openai.com/v1"
        
        console.print(f"  [dim]→ 使用 API 地址: {base_url}[/dim]")
        console.print(f"  [dim]→ 测试模型: {config.model}[/dim]")
        console.print(f"  [dim]→ 提供商: {config.provider}[/dim]")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {config.api_key}"}
                
                # Azure 特殊处理
                if config.provider == "azure":
                    headers["api-key"] = config.api_key
                    url = f"{base_url}/openai/deployments/{config.deployment}/chat/completions?api-version={config.api_version or '2024-02-15-preview'}"
                else:
                    url = f"{base_url}/chat/completions"
                
                console.print(f"  [dim]→ 请求 URL: {url}[/dim]")
                
                # 构建请求体
                request_body = {
                    "model": config.model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 5
                }
                console.print(f"  [dim]→ 请求体: {request_body}[/dim]")
                console.print("  [dim]→ 发送请求...[/dim]")
                
                response = await client.post(
                    url,
                    headers=headers,
                    json=request_body
                )
                
                console.print(f"  [dim]→ 响应状态: {response.status_code}[/dim]")
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0].get("message", {}).get("content", "")
                        console.print(f"  [dim]→ 响应内容: {content[:50]}...[/dim]")
                    return True, f"API 连接正常，模型 {config.model} 可用"
                elif response.status_code == 401:
                    console.print("  [dim]→ 错误: API Key 认证失败[/dim]")
                    return False, "API Key 无效或已过期"
                elif response.status_code == 404:
                    console.print(f"  [dim]→ 错误: 模型未找到[/dim]")
                    console.print(f"  [dim]→ 响应详情: {response.text[:200]}[/dim]")
                    return False, f"模型 {config.model} 不存在"
                else:
                    error_msg = response.text[:200]
                    console.print(f"  [dim]→ 错误响应: {error_msg}[/dim]")
                    return False, f"API 错误 ({response.status_code}): {error_msg}"
                    
        except httpx.ConnectError as e:
            console.print(f"  [dim]→ 连接失败: {e}[/dim]")
            return False, f"无法连接到 API 服务 ({base_url})"
        except httpx.TimeoutException:
            console.print("  [dim]→ 请求超时[/dim]")
            return False, "请求超时，请检查网络连接"
        except Exception as e:
            console.print(f"  [dim]→ 异常: {type(e).__name__}: {e}[/dim]")
            return False, f"测试失败: {str(e)}"


class LLMSetupWizard:
    """LLM 配置向导"""
    
    def __init__(self):
        self.manager = LLMConfigManager()
        self.config = LLMConfig()
    
    async def run_setup(self):
        """运行配置向导"""
        self._print_welcome()
        
        # 步骤 1: 选择提供商
        provider = await self._select_provider()
        if provider == LLMProvider.SKIP:
            self.config.provider = "skip"
            self.config.model = ""
            await self._save_and_finish()
            return
        
        self.config.provider = provider.value
        
        # 步骤 2: 配置 API
        success = await self._configure_api(provider)
        if not success:
            console.print("\n[yellow]⚠️ 配置已取消[/yellow]")
            return
        
        # 步骤 3: 功能配置
        await self._configure_features()
        
        # 保存配置
        await self._save_and_finish()
    
    def _print_welcome(self):
        """打印欢迎信息"""
        console.print(Panel(
            "[bold green]🤖 LLM 配置向导[/bold green]\n\n"
            "本向导将帮助您配置大语言模型，用于:\n"
            "  • 智能内容摘要生成\n"
            "  • 内容质量评估\n"
            "  • 个性化推荐优化\n\n"
            "[dim]支持: OpenAI, Gemini, Kimi, Qwen, GLM, OpenRouter, Ollama 等[/dim]",
            title="LLM 配置",
            border_style="blue"
        ))
        
        Prompt.ask("\n按 Enter 开始配置")
    
    # 在向导中显示的提供商（排除 Ollama, Azure, Baidu, 旧版 Aliyun/Zhipu）
    WIZARD_PROVIDERS = [
        LLMProvider.OPENAI,
        LLMProvider.GEMINI,
        LLMProvider.MOONSHOT,
        LLMProvider.QWEN,
        LLMProvider.GLM,
        LLMProvider.OPENROUTER,
    ]
    
    async def _select_provider(self) -> LLMProvider:
        """选择 LLM 提供商"""
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]步骤 1/3: 选择 LLM 提供商[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        
        console.print("[bold]📝 选择 LLM 提供商：[/bold]\n")
        
        providers = self.WIZARD_PROVIDERS
        for i, provider in enumerate(providers, 1):
            config = PROVIDER_CONFIGS[provider]
            marker = "★" if i <= 3 else " "
            console.print(f"   [{marker}] [{i}] {config.emoji} {config.display_name}")
            console.print(f"       [dim]{config.description}[/dim]\n")
        
        console.print(f"   [ ] [{len(providers) + 1}] ⏭️  跳过 - 暂不配置 LLM")
        console.print("       [dim]将使用规则摘要（功能受限）[/dim]\n")
        
        choice = IntPrompt.ask(
            "请选择",
            choices=[str(i) for i in range(1, len(providers) + 2)],
            default=1
        )
        
        if choice == len(providers) + 1:
            return LLMProvider.SKIP
        
        return providers[choice - 1]
    
    async def _configure_api(self, provider: LLMProvider) -> bool:
        """配置 API"""
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]步骤 2/3: 配置 API[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        
        config = PROVIDER_CONFIGS[provider]
        
        console.print(f"[bold]📝 您选择了 [{config.display_name}][/bold]\n")
        console.print(f"[dim]{config.help_text}[/dim]\n")
        
        # API Key
        if config.requires_api_key:
            console.print("[yellow]⚠️  提示：密钥仅保存在本地 .env 文件，不会上传[/yellow]\n")
            
            api_key = Prompt.ask(f"请输入 {config.display_name} API Key")
            
            if not api_key or not api_key.strip():
                console.print("[red]✗ API Key 不能为空[/red]")
                return False
            
            api_key = api_key.strip()
            
            # 简单验证格式
            if not self._validate_api_key_format(provider, api_key):
                if not Confirm.ask("API Key 格式看起来不正确，是否继续？", default=False):
                    return False
            
            self.config.api_key = api_key
            console.print("[green]✅ API Key 格式验证通过[/green]\n")
        
        # Base URL 配置 - 所有提供商都可自定义
        default_url = config.base_url_hint or ""
        
        console.print("\n[bold]📝 配置 API 地址：[/bold]\n")
        console.print(f"[dim]默认地址: {default_url}[/dim]\n")
        
        custom_url = Prompt.ask("请输入 API 地址", default=default_url)
        if custom_url and custom_url != default_url:
            self.config.base_url = custom_url
        else:
            self.config.base_url = default_url
        
        console.print(f"[green]✅ 已配置 API 地址: {self.config.base_url}[/green]")
        
        # 输入模型名称
        console.print("\n[bold]📝 配置模型：[/bold]\n")
        
        # 显示推荐的模型作为参考
        console.print("[dim]推荐的模型:[/dim]")
        for model in config.models[:3]:
            rec = " ★推荐" if model.recommended else ""
            console.print(f"  • {model.id} - {model.description}{rec}")
        console.print("")
        
        # 让用户自行填入模型名称
        default_model = config.models[0].id if config.models else ""
        model_input = Prompt.ask("请输入模型名称", default=default_model)
        
        self.config.model = model_input.strip()
        console.print(f"[green]✅ 已配置模型: {self.config.model}[/green]")
        
        return True
    
    def _validate_api_key_format(self, provider: LLMProvider, api_key: str) -> bool:
        """验证 API Key 格式"""
        if provider == LLMProvider.OPENAI:
            # OpenAI key 通常以 sk- 开头
            return api_key.startswith("sk-") and len(api_key) > 20
        elif provider == LLMProvider.OPENROUTER:
            # OpenRouter key 通常以 sk-or- 开头
            return api_key.startswith("sk-or-") and len(api_key) > 20
        elif provider == LLMProvider.AZURE:
            # Azure key 是 32 位十六进制
            return len(api_key) == 32 and all(c in "0123456789abcdef" for c in api_key.lower())
        elif provider == LLMProvider.GEMINI:
            # Gemini key 通常以 AIza 开头
            return api_key.startswith("AIza") and len(api_key) > 20
        elif provider == LLMProvider.MOONSHOT:
            # Moonshot key 通常以 sk- 开头
            return api_key.startswith("sk-") and len(api_key) > 20
        elif provider == LLMProvider.QWEN:
            # Qwen key 通常以 sk- 开头
            return api_key.startswith("sk-") and len(api_key) > 20
        elif provider == LLMProvider.GLM:
            # GLM key 通常是一串较长的字母数字混合
            return len(api_key) >= 16
        return True  # 其他提供商不做严格验证
    
    async def _configure_features(self):
        """配置功能开关"""
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]步骤 3/3: 功能配置[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        
        console.print("[bold]📝 启用 LLM 增强功能：[/bold]\n")
        
        self.config.enable_summary = Confirm.ask(
            "   [x] 智能摘要生成\n       [dim]使用 LLM 生成高质量内容摘要[/dim]",
            default=True
        )
        
        self.config.enable_quality_check = Confirm.ask(
            "\n   [x] 内容质量评估\n       [dim]自动评估文章原创性、深度[/dim]",
            default=True
        )
        
        self.config.enable_tagging = Confirm.ask(
            "\n   [ ] 智能标签提取\n       [dim]自动提取精准内容标签[/dim]",
            default=False
        )
        
        self.config.enable_recommendation = Confirm.ask(
            "\n   [ ] 个性化推荐优化\n       [dim]基于 LLM 的个性化排序[/dim]",
            default=False
        )
        
        # 摘要长度
        console.print("\n[bold]📝 摘要长度偏好：[/bold]")
        console.print("   [1] 简洁 - 一句话摘要")
        console.print("   [2] 标准 - 3-5个要点 [dim](推荐)[/dim]")
        console.print("   [3] 详细 - 完整段落摘要")
        
        length_choice = IntPrompt.ask("请选择", choices=["1", "2", "3"], default=2)
        self.config.summary_length = {1: "short", 2: "medium", 3: "long"}[length_choice]
    
    async def _save_and_finish(self):
        """保存配置并完成"""
        # 显示配置预览
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]配置预览[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        
        if self.config.provider == "skip":
            console.print("  配置: [yellow]跳过 LLM 配置[/yellow]")
            console.print("  说明: 将使用规则摘要（功能受限）\n")
        else:
            provider_config = PROVIDER_CONFIGS.get(LLMProvider(self.config.provider))
            if provider_config:
                console.print(f"  提供商: {provider_config.emoji} {provider_config.display_name}")
            
            console.print(f"  模型: {self.config.model}")
            console.print(f"  API Key: {self.config.get_masked_api_key()}")
            
            if self.config.base_url and self.config.provider != "ollama":
                console.print(f"  自定义地址: {self.config.base_url}")
            
            features = []
            if self.config.enable_summary:
                features.append("智能摘要")
            if self.config.enable_quality_check:
                features.append("质量评估")
            if self.config.enable_tagging:
                features.append("智能标签")
            if self.config.enable_recommendation:
                features.append("推荐优化")
            
            console.print(f"  功能: {', '.join(features) if features else '无'}")
            
            length_map = {"short": "简洁", "medium": "标准", "long": "详细"}
            console.print(f"  摘要长度: {length_map.get(self.config.summary_length, '标准')}")
        
        console.print("")
        
        if not Confirm.ask("是否保存配置?", default=True):
            console.print("\n[yellow]⚠️ 配置未保存[/yellow]")
            return
        
        # 保存配置
        self.manager.save_config(self.config)
        
        # 测试连接
        if self.config.provider != "skip":
            console.print("\n[bold]🧪 正在测试 API 连接...[/bold]")
            
            success, message = await self.manager.test_connection(self.config)
            
            if success:
                console.print(f"[green]✅ {message}[/green]")
            else:
                console.print(f"[yellow]⚠️ {message}[/yellow]")
                console.print("[yellow]   配置已保存，但可能无法正常使用，请检查配置[/yellow]")
        
        # 完成信息
        console.print("\n[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
        console.print("[bold green]✅ LLM 配置完成！[/bold green]")
        console.print("[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]\n")
        
        console.print("配置已保存到 .env 文件\n")
        
        console.print("[bold]💡 提示：[/bold]")
        console.print("  • 运行 [cyan]python -m src.cli llm status[/cyan] 查看配置状态")
        console.print("  • 运行 [cyan]python -m src.cli llm test[/cyan] 测试连接")
        console.print("  • 如需更改配置，重新运行 [cyan]python -m src.cli llm setup[/cyan]")
    
    async def switch_model(self):
        """切换模型"""
        current_config = self.manager.get_current_config()
        
        if not current_config.is_configured():
            console.print("[yellow]⚠️ 尚未配置 LLM，请先运行: python -m src.cli llm setup[/yellow]")
            return
        
        provider = LLMProvider(current_config.provider)
        provider_config = PROVIDER_CONFIGS.get(provider)
        
        if not provider_config:
            console.print("[red]✗ 当前提供商不支持切换模型[/red]")
            return
        
        console.print(f"\n[bold]📝 选择要使用的模型：[/bold]\n")
        console.print(f"当前: {current_config.model}\n")
        
        models = provider_config.models
        for i, model in enumerate(models, 1):
            marker = "✓" if model.id == current_config.model else " "
            console.print(f"   [{marker}] [{i}] {model.name} - {model.description}")
        
        console.print(f"   [ ] [{len(models) + 1}] 配置新模型...")
        
        choice = IntPrompt.ask(
            "\n请选择",
            choices=[str(i) for i in range(1, len(models) + 2)],
            default=1
        )
        
        if choice == len(models) + 1:
            # 重新运行配置向导
            await self.run_setup()
            return
        
        new_model = models[choice - 1]
        current_config.model = new_model.id
        
        self.manager.save_config(current_config)
        console.print(f"\n[green]✅ 已切换到 {new_model.name}[/green]")
        
        # 测试新模型
        console.print("\n[bold]🧪 测试新模型...[/bold]")
        success, message = await self.manager.test_connection(current_config)
        
        if success:
            console.print(f"[green]✅ {message}[/green]")
        else:
            console.print(f"[yellow]⚠️ {message}[/yellow]")
    
    def print_status(self):
        """打印配置状态"""
        config = self.manager.get_current_config()
        
        console.print("\n[bold blue]🤖 LLM 配置状态[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        
        if not config.is_configured():
            console.print("  状态: [yellow]⚠️ 未配置[/yellow]\n")
            console.print("  运行 [cyan]python -m src.cli llm setup[/cyan] 进行配置")
            return
        
        if config.provider == "skip":
            console.print("  配置: [yellow]已跳过 LLM 配置[/yellow]")
            console.print("  说明: 使用规则摘要（功能受限）\n")
            return
        
        # 提供商信息
        provider = LLMProvider(config.provider)
        provider_config = PROVIDER_CONFIGS.get(provider)
        
        if provider_config:
            console.print(f"  提供商:   {provider_config.emoji} {provider_config.display_name}")
        else:
            console.print(f"  提供商:   {config.provider}")
        
        console.print(f"  模型:     {config.model}")
        console.print(f"  API Key:  {config.get_masked_api_key()}")
        
        # 测试连接
        import asyncio
        success, message = asyncio.run(self.manager.test_connection())
        
        if success:
            console.print(f"  状态:     [green]✅ 正常[/green]")
        else:
            console.print(f"  状态:     [red]✗ {message}[/red]")
        
        console.print("")
        
        # 功能状态
        console.print("[bold]功能状态：[/bold]")
        summary_status = "✅ 已启用" if config.enable_summary else "⚪ 未启用"
        quality_status = "✅ 已启用" if config.enable_quality_check else "⚪ 未启用"
        tagging_status = "✅ 已启用" if config.enable_tagging else "⚪ 未启用"
        rec_status = "✅ 已启用" if config.enable_recommendation else "⚪ 未启用"
        
        console.print(f"  智能摘要:   {summary_status}")
        console.print(f"  质量评估:   {quality_status}")
        console.print(f"  智能标签:   {tagging_status}")
        console.print(f"  推荐优化:   {rec_status}")
        
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
    
    def print_models(self):
        """打印支持的模型列表"""
        console.print("\n[bold blue]支持的 LLM 提供商和模型[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        
        for provider in LLMProvider:
            if provider == LLMProvider.SKIP:
                continue
            
            config = PROVIDER_CONFIGS[provider]
            
            console.print(Panel(
                f"[bold]{config.emoji} {config.display_name}[/bold]\n"
                f"[dim]{config.description}[/dim]\n\n"
                f"[bold]可用模型：[/bold]\n" +
                "\n".join([
                    f"  • {m.name} - {m.description} [dim]({m.price_hint})[/dim]"
                    for m in config.models
                ]),
                border_style="green"
            ))


# 全局管理器实例
_llm_manager: Optional[LLMConfigManager] = None


def get_llm_manager() -> LLMConfigManager:
    """获取 LLM 配置管理器单例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMConfigManager()
    return _llm_manager
