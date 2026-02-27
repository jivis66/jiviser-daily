"""
认证管理模块
提供交互式 Cookie/Token 获取、加密存储和验证功能
"""
import json
import re
import shlex
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import httpx
from cryptography.fernet import Fernet

from src.config import get_settings
from src.database import AuthCredentialDB, get_session

settings = get_settings()


# 加密密钥（从配置获取或使用默认）
def get_encryption_key() -> bytes:
    """获取加密密钥"""
    # 使用 API_SECRET_KEY 生成稳定的密钥
    import base64
    import hashlib
    
    key_base = settings.api_secret_key
    key_hash = hashlib.sha256(key_base.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_credentials(data: str) -> str:
    """加密凭证数据"""
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()


def decrypt_credentials(encrypted_data: str) -> str:
    """解密凭证数据"""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_data.encode()).decode()


@dataclass
class AuthConfig:
    """认证配置"""
    source_name: str
    display_name: str
    auth_type: str  # cookie, token, oauth
    login_url: str
    cookie_domains: list = field(default_factory=list)
    required_headers: list = field(default_factory=list)
    help_text: str = ""
    test_endpoint: str = ""
    test_method: str = "GET"
    expires_days: int = 30


# 预定义的认证配置
AUTH_CONFIGS: Dict[str, AuthConfig] = {
    "jike": AuthConfig(
        source_name="jike",
        display_name="即刻",
        auth_type="cookie",
        login_url="https://web.okjike.com",
        cookie_domains=[".okjike.com", "web.okjike.com"],
        required_headers=["cookie", "user-agent"],
        help_text="""
📖 即刻 Cookie 获取步骤：
   1. 使用 Chrome/Edge 浏览器登录即刻网页版 (https://web.okjike.com)
   2. 按 F12 打开开发者工具，切换到 Network (网络) 标签
   3. 刷新页面，找到任意 API 请求（如 /api/users/me 或 /api/users/profile）
   4. 点击请求，在 Headers 中找到 Request Headers 的 cookie 字段
   5. 右键点击请求 → Copy → Copy as cURL (bash)
   6. 粘贴完整的 cURL 命令
        """.strip(),
        test_endpoint="https://web.okjike.com/api/users/me",
        expires_days=30
    ),
    "xiaohongshu": AuthConfig(
        source_name="xiaohongshu",
        display_name="小红书",
        auth_type="cookie",
        login_url="https://www.xiaohongshu.com",
        cookie_domains=[".xiaohongshu.com", "www.xiaohongshu.com"],
        required_headers=["cookie", "user-agent", "referer"],
        help_text="""
📖 小红书 Cookie 获取步骤：
   1. 使用 Chrome/Edge 浏览器登录小红书网页版 (https://www.xiaohongshu.com)
   2. 按 F12 打开开发者工具，切换到 Network (网络) 标签
   3. 刷新页面，找到 API 请求（如 /api/sns/web/v1/feed 或 /api/sns/web/v1/user/selfinfo）
   4. 右键点击请求 → Copy → Copy as cURL (bash)
   5. 粘贴完整的 cURL 命令
        """.strip(),
        test_endpoint="https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo",
        expires_days=7
    ),
    "zhihu": AuthConfig(
        source_name="zhihu",
        display_name="知乎",
        auth_type="cookie",
        login_url="https://www.zhihu.com",
        cookie_domains=[".zhihu.com", "www.zhihu.com"],
        required_headers=["cookie", "user-agent"],
        help_text="""
📖 知乎 Cookie 获取步骤：
   1. 使用 Chrome/Edge 浏览器登录知乎 (https://www.zhihu.com)
   2. 按 F12 打开开发者工具，切换到 Network (网络) 标签
   3. 刷新页面，找到 API 请求（如 /api/v4/me 或 /api/v4/members/self）
   4. 右键点击请求 → Copy → Copy as cURL (bash)
   5. 粘贴完整的 cURL 命令
        """.strip(),
        test_endpoint="https://www.zhihu.com/api/v4/me",
        expires_days=30
    ),
    "bilibili": AuthConfig(
        source_name="bilibili",
        display_name="B站",
        auth_type="cookie",
        login_url="https://www.bilibili.com",
        cookie_domains=[".bilibili.com", "www.bilibili.com"],
        required_headers=["cookie", "user-agent", "referer"],
        help_text="""
📖 B站 Cookie 获取步骤：
   1. 使用 Chrome/Edge 浏览器登录 B站 (https://www.bilibili.com)
   2. 按 F12 打开开发者工具，切换到 Network (网络) 标签
   3. 刷新页面，找到 API 请求（如 /x/web-interface/nav）
   4. 右键点击请求 → Copy → Copy as cURL (bash)
   5. 粘贴完整的 cURL 命令
        """.strip(),
        test_endpoint="https://api.bilibili.com/x/web-interface/nav",
        expires_days=30
    ),
    "weibo": AuthConfig(
        source_name="weibo",
        display_name="微博",
        auth_type="cookie",
        login_url="https://weibo.com",
        cookie_domains=[".weibo.com", "weibo.com", ".weibo.cn"],
        required_headers=["cookie", "user-agent", "referer"],
        help_text="""
📖 微博 Cookie 获取步骤：
   1. 使用 Chrome/Edge 浏览器登录微博 (https://weibo.com)
   2. 按 F12 打开开发者工具，切换到 Network (网络) 标签
   3. 刷新页面，找到 API 请求（如 /ajax/statuses/mymblog）
   4. 右键点击请求 → Copy → Copy as cURL (bash)
   5. 粘贴完整的 cURL 命令
        """.strip(),
        test_endpoint="https://weibo.com/ajax/statuses/mymblog",
        expires_days=7
    ),
    "douyin": AuthConfig(
        source_name="douyin",
        display_name="抖音",
        auth_type="cookie",
        login_url="https://www.douyin.com",
        cookie_domains=[".douyin.com", "www.douyin.com"],
        required_headers=["cookie", "user-agent", "referer"],
        help_text="""
📖 抖音 Cookie 获取步骤：
   1. 使用 Chrome/Edge 浏览器登录抖音网页版 (https://www.douyin.com)
   2. 按 F12 打开开发者工具，切换到 Network (网络) 标签
   3. 刷新页面，找到 API 请求（如 /aweme/v1/web/feed/fresh/）
   4. 右键点击请求 → Copy → Copy as cURL (bash)
   5. 粘贴完整的 cURL 命令
        """.strip(),
        test_endpoint="https://www.douyin.com/aweme/v1/web/feed/fresh/",
        expires_days=7
    ),
}


class CURLParser:
    """cURL 命令解析器"""
    
    @staticmethod
    def parse(curl_command: str) -> Dict[str, Any]:
        """
        解析 cURL 命令，提取 headers、cookie 等信息
        
        支持格式：
        - Bash cURL: curl -H "Cookie: xxx" https://...
        - PowerShell: curl -Headers @{"Cookie"="xxx"} -Uri https://...
        - 纯 Cookie 字符串: a=1;b=2
        
        Args:
            curl_command: cURL 命令字符串
            
        Returns:
            解析结果字典
        """
        result = {
            "url": "",
            "method": "GET",
            "headers": {},
            "cookies": {},
            "data": None,
            "raw_cookies": ""
        }
        
        # 清理命令：统一换行符、去除多余空格
        curl_command = curl_command.strip()
        curl_command = curl_command.replace('\r\n', '\n').replace('\\\n', '')
        curl_command = curl_command.replace('\\n', '')
        
        # 去除行首的 curl
        if curl_command.startswith("curl "):
            curl_command = curl_command[5:]
        
        # 尝试直接提取 cookie 字符串（如果不是完整 cURL）
        if " -H " not in curl_command and " -b " not in curl_command and " --cookie " not in curl_command:
            # 可能是纯 cookie 字符串
            if "=" in curl_command and ";" in curl_command:
                result["raw_cookies"] = curl_command.strip().strip('"\'')
                result["cookies"] = CURLParser._parse_cookie_string(result["raw_cookies"])
                return result
        
        # 检测 PowerShell 格式
        if "-Headers @{" in curl_command or "-Uri " in curl_command:
            return CURLParser._parse_powershell_curl(curl_command, result)
        
        # 使用 shlex 分割命令（处理引号）
        try:
            parts = shlex.split(curl_command)
        except ValueError as e:
            # 分割失败，可能是引号不匹配，尝试修复
            parts = CURLParser._fallback_split(curl_command)
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            if part in ("-H", "--header"):
                i += 1
                if i < len(parts):
                    header = parts[i]
                    if ":" in header:
                        key, value = header.split(":", 1)
                        result["headers"][key.strip().lower()] = value.strip()
            
            elif part in ("-b", "--cookie"):
                i += 1
                if i < len(parts):
                    result["raw_cookies"] = parts[i].strip('"\'')
                    result["cookies"] = CURLParser._parse_cookie_string(result["raw_cookies"])
            
            elif part in ("-d", "--data", "--data-raw"):
                i += 1
                if i < len(parts):
                    result["data"] = parts[i].strip('"\'')
                    result["method"] = "POST"
            
            elif part in ("-X", "--request"):
                i += 1
                if i < len(parts):
                    result["method"] = parts[i].upper()
            
            elif part.startswith("http://") or part.startswith("https://"):
                result["url"] = part.strip('"\'')
            
            i += 1
        
        # 从 headers 中提取 cookie
        if "cookie" in result["headers"]:
            result["raw_cookies"] = result["headers"]["cookie"]
            result["cookies"] = CURLParser._parse_cookie_string(result["raw_cookies"])
            del result["headers"]["cookie"]
        
        return result
    
    @staticmethod
    def _parse_powershell_curl(curl_command: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """解析 PowerShell 格式的 cURL 命令"""
        import re
        
        # 提取 Headers
        headers_match = re.search(r'-Headers @\{([^}]+)\}', curl_command)
        if headers_match:
            headers_str = headers_match.group(1)
            # 解析 "Key"="Value" 格式
            for match in re.finditer(r'"([^"]+)"\s*=\s*"([^"]*)"', headers_str):
                key, value = match.groups()
                key_lower = key.lower()
                if key_lower == "cookie":
                    result["raw_cookies"] = value
                    result["cookies"] = CURLParser._parse_cookie_string(value)
                else:
                    result["headers"][key_lower] = value
        
        # 提取 URI/URL
        uri_match = re.search(r'-(?:Uri|Url)\s+"([^"]+)"', curl_command)
        if uri_match:
            result["url"] = uri_match.group(1)
        
        # 提取 Method
        method_match = re.search(r'-Method\s+(\w+)', curl_command)
        if method_match:
            result["method"] = method_match.group(1).upper()
        
        return result
    
    @staticmethod
    def _fallback_split(curl_command: str) -> list:
        """当 shlex 分割失败时的备用分割方法"""
        parts = []
        current = ""
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(curl_command):
            char = curl_command[i]
            
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                    if current:
                        parts.append(current)
                        current = ""
                elif quote_char == char:
                    in_quotes = False
                    quote_char = None
                    parts.append(current)
                    current = ""
                else:
                    current += char
            elif char.isspace() and not in_quotes:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
            
            i += 1
        
        if current:
            parts.append(current)
        
        return parts
    
    @staticmethod
    def _parse_cookie_string(cookie_str: str) -> Dict[str, str]:
        """解析 cookie 字符串为字典"""
        cookies = {}
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key.strip()] = value.strip()
        return cookies
    
    @staticmethod
    def extract_essential_headers(parsed: Dict[str, Any], config: AuthConfig) -> Dict[str, str]:
        """提取必要的 headers"""
        headers = {}
        
        # 必须包含的 headers
        if "user-agent" in config.required_headers:
            headers["User-Agent"] = parsed["headers"].get("user-agent", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        if "referer" in config.required_headers:
            headers["Referer"] = parsed["headers"].get("referer", config.login_url)
        
        # 保留其他有用的 headers
        for key in ["accept", "accept-language", "accept-encoding"]:
            if key in parsed["headers"]:
                headers[key.title()] = parsed["headers"][key]
        
        return headers


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.configs = AUTH_CONFIGS
    
    def get_supported_sources(self) -> Dict[str, AuthConfig]:
        """获取支持的认证渠道"""
        return self.configs
    
    def get_config(self, source_name: str) -> Optional[AuthConfig]:
        """获取指定渠道的配置"""
        return self.configs.get(source_name)
    
    async def add_auth(
        self, 
        source_name: str, 
        curl_command: str,
        username: str = None
    ) -> Tuple[bool, str]:
        """
        添加认证信息
        
        Args:
            source_name: 渠道名称
            curl_command: cURL 命令或 cookie 字符串
            username: 用户名（可选）
            
        Returns:
            (成功状态, 消息)
        """
        config = self.get_config(source_name)
        if not config:
            return False, f"不支持的渠道: {source_name}"
        
        # 解析 cURL
        parsed = CURLParser.parse(curl_command)
        
        if not parsed["cookies"] and not parsed["raw_cookies"]:
            return False, "无法解析 Cookie，请检查输入是否为有效的 cURL 命令或 Cookie 字符串"
        
        # 提取必要 headers
        headers = CURLParser.extract_essential_headers(parsed, config)
        
        # 加密存储
        credentials = encrypt_credentials(parsed["raw_cookies"])
        
        # 创建数据库记录
        expires_at = datetime.now(timezone.utc) + timedelta(days=config.expires_days)
        
        credential = AuthCredentialDB(
            source_name=source_name,
            auth_type=config.auth_type,
            credentials=credentials,
            headers=json.dumps(headers, ensure_ascii=False),
            username=username,
            expires_at=expires_at,
            is_valid=True
        )
        
        async with get_session() as session:
            from src.database import AuthCredentialRepository
            repo = AuthCredentialRepository(session)
            await repo.create_or_update(credential)
        
        return True, f"✅ [{config.display_name}] 认证配置已保存，过期时间: {expires_at.strftime('%Y-%m-%d %H:%M')}"
    
    async def test_auth(self, source_name: str) -> Tuple[bool, str, Optional[dict]]:
        """
        测试认证是否有效
        
        Args:
            source_name: 渠道名称
            
        Returns:
            (是否有效, 消息, 用户信息)
        """
        config = self.get_config(source_name)
        if not config:
            return False, f"不支持的渠道: {source_name}", None
        
        # 获取凭证
        async with get_session() as session:
            from src.database import AuthCredentialRepository
            repo = AuthCredentialRepository(session)
            credential = await repo.get_by_source(source_name)
        
        if not credential:
            return False, f"未找到 [{config.display_name}] 的认证配置，请先运行: auth add {source_name}", None
        
        if not credential.is_valid:
            return False, f"[{config.display_name}] 认证已失效，请更新: auth update {source_name}", None
        
        try:
            # 解密凭证
            cookie_str = decrypt_credentials(credential.credentials)
            headers = json.loads(credential.headers or "{}")
            headers["Cookie"] = cookie_str
            
            # 发送测试请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=config.test_method,
                    url=config.test_endpoint,
                    headers=headers,
                    follow_redirects=True
                )
                
                # 检查响应
                if response.status_code == 200:
                    # 更新最后验证时间
                    async with get_session() as session:
                        from src.database import AuthCredentialRepository
                        repo = AuthCredentialRepository(session)
                        await repo.update_last_verified(source_name)
                    
                    # 尝试解析用户信息
                    user_info = await self._parse_user_info(source_name, response)
                    return True, f"认证有效", user_info
                
                elif response.status_code in (401, 403):
                    # 认证失效
                    async with get_session() as session:
                        from src.database import AuthCredentialRepository
                        repo = AuthCredentialRepository(session)
                        await repo.mark_invalid(source_name, f"HTTP {response.status_code}")
                    return False, f"认证已失效 (HTTP {response.status_code})，请更新", None
                
                else:
                    return False, f"请求失败 (HTTP {response.status_code})", None
                    
        except Exception as e:
            return False, f"测试失败: {str(e)}", None
    
    async def _parse_user_info(self, source_name: str, response: httpx.Response) -> Optional[dict]:
        """解析用户信息"""
        try:
            data = response.json()
            
            if source_name == "jike":
                user = data.get("user", {})
                return {
                    "username": user.get("screenName"),
                    "user_id": user.get("id"),
                    "avatar": user.get("avatarImage", {}).get("thumbnailUrl")
                }
            
            elif source_name == "xiaohongshu":
                user = data.get("data", {})
                return {
                    "username": user.get("nickname"),
                    "user_id": user.get("user_id"),
                    "avatar": user.get("images")
                }
            
            elif source_name == "zhihu":
                return {
                    "username": data.get("name"),
                    "user_id": data.get("url_token"),
                    "avatar": data.get("avatar_url")
                }
            
            elif source_name == "bilibili":
                user = data.get("data", {})
                return {
                    "username": user.get("uname"),
                    "user_id": user.get("mid"),
                    "avatar": user.get("face")
                }
            
            elif source_name == "weibo":
                user = data.get("data", {}).get("user", {})
                return {
                    "username": user.get("screen_name"),
                    "user_id": user.get("id"),
                    "avatar": user.get("profile_image_url")
                }
            
        except Exception:
            pass
        
        return None
    
    async def remove_auth(self, source_name: str) -> Tuple[bool, str]:
        """删除认证配置"""
        config = self.get_config(source_name)
        display_name = config.display_name if config else source_name
        
        async with get_session() as session:
            from src.database import AuthCredentialRepository
            repo = AuthCredentialRepository(session)
            success = await repo.delete(source_name)
        
        if success:
            return True, f"✅ [{display_name}] 认证配置已删除"
        else:
            return False, f"未找到 [{display_name}] 的认证配置"
    
    async def list_auth(self) -> list:
        """列出所有认证配置"""
        async with get_session() as session:
            from src.database import AuthCredentialRepository
            repo = AuthCredentialRepository(session)
            credentials = await repo.get_all()
        
        result = []
        for cred in credentials:
            config = self.get_config(cred.source_name)
            result.append({
                "source_name": cred.source_name,
                "display_name": config.display_name if config else cred.source_name,
                "auth_type": cred.auth_type,
                "username": cred.username,
                "expires_at": cred.expires_at,
                "is_valid": cred.is_valid,
                "last_verified": cred.last_verified,
                "created_at": cred.created_at
            })
        
        return result
    
    async def get_expiring_soon(self, hours: int = 72) -> list:
        """获取即将过期的认证"""
        async with get_session() as session:
            from src.database import AuthCredentialRepository
            repo = AuthCredentialRepository(session)
            credentials = await repo.get_expiring_soon(hours)
        
        result = []
        for cred in credentials:
            config = self.get_config(cred.source_name)
            result.append({
                "source_name": cred.source_name,
                "display_name": config.display_name if config else cred.source_name,
                "expires_at": cred.expires_at,
                "hours_remaining": (cred.expires_at - datetime.now(timezone.utc)).total_seconds() / 3600
            })
        
        return result


# 全局认证管理器实例
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """获取认证管理器单例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
