"""
小红书交互式鉴权模块
提供基于 Playwright 的自动化浏览器登录功能

使用方式:
    auth_helper = XiaohongshuAuthHelper()
    await auth_helper.interactive_login()  # 启动交互式登录
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Callable, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from src.auth_manager import (
    AuthConfig, 
    encrypt_credentials, 
    get_auth_manager,
    AUTH_CONFIGS
)
from src.database import get_session


class XHSAuthError(Exception):
    """小红书鉴权错误"""
    pass


class XHSLoginTimeoutError(XHSAuthError):
    """登录超时错误"""
    pass


class XHSLoginFailedError(XHSAuthError):
    """登录失败错误"""
    pass


@dataclass
class XHSAuthData:
    """小红书鉴权数据结构"""
    cookies: list
    local_storage: list
    session_storage: list
    user_agent: str
    timestamp: float
    user_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cookies": self.cookies,
            "local_storage": self.local_storage,
            "session_storage": self.session_storage,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp,
            "user_info": self.user_info,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XHSAuthData":
        """从字典创建实例"""
        return cls(
            cookies=data.get("cookies", []),
            local_storage=data.get("local_storage", []),
            session_storage=data.get("session_storage", []),
            user_agent=data.get("user_agent", ""),
            timestamp=data.get("timestamp", 0),
            user_info=data.get("user_info"),
        )
    
    def get_cookie_dict(self) -> Dict[str, str]:
        """获取 Cookie 字典"""
        return {c["name"]: c["value"] for c in self.cookies}
    
    def get_cookie_string(self) -> str:
        """获取 Cookie 字符串"""
        return "; ".join([f"{c['name']}={c['value']}" for c in self.cookies])


class XiaohongshuAuthHelper:
    """
    小红书交互式鉴权助手
    
    提供基于 Playwright 的自动化浏览器登录，支持：
    - 扫码登录
    - 手机号登录
    - 验证码登录
    - 自动检测登录状态
    - 加密持久化存储
    
    Attributes:
        config: 认证配置
        headless: 是否无头模式
        timeout: 登录超时时间（秒）
        on_status: 状态回调函数
    """
    
    # 小红书登录态关键 Cookie 字段
    AUTH_COOKIES = ["webId", "xhsTrackerId", "web_session", "session.EDITH"]
    
    # 默认浏览器配置
    DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        headless: bool = False,
        timeout: int = 300,
        on_status: Optional[Callable[[str], None]] = None
    ):
        """
        初始化鉴权助手
        
        Args:
            headless: 是否使用无头模式（默认 False，方便用户交互）
            timeout: 登录超时时间（秒），默认 5 分钟
            on_status: 状态回调函数，接收状态消息字符串
        """
        self.config = AUTH_CONFIGS.get("xiaohongshu")
        if not self.config:
            raise XHSAuthError("未找到小红书认证配置")
        
        self.headless = headless
        self.timeout = timeout
        self.on_status = on_status or self._default_status_handler
        
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
    
    def _default_status_handler(self, message: str) -> None:
        """默认状态处理器（打印到控制台）"""
        print(f"[小红书鉴权] {message}")
    
    def _notify(self, message: str) -> None:
        """发送状态通知"""
        self.on_status(message)
    
    async def _launch_browser(self) -> tuple[Browser, BrowserContext]:
        """
        启动带反检测配置的浏览器
        
        Returns:
            (Browser, BrowserContext) 实例
        """
        playwright = await async_playwright().start()
        
        # 启动浏览器（带反检测参数）
        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
            ]
        )
        
        # 创建浏览器上下文（带指纹伪装）
        context = await browser.new_context(
            viewport=self.DEFAULT_VIEWPORT,
            user_agent=self.DEFAULT_USER_AGENT,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            geolocation={"latitude": 31.2304, "longitude": 121.4737},  # 上海
            permissions=["geolocation"],
            color_scheme="light",
        )
        
        # 注入反检测脚本
        await self._inject_anti_detect_scripts(context)
        
        self._browser = browser
        self._context = context
        
        return browser, context
    
    async def _inject_anti_detect_scripts(self, context: BrowserContext) -> None:
        """
        注入反检测脚本，隐藏自动化特征
        
        Args:
            context: 浏览器上下文
        """
        anti_detect_script = """
        // 隐藏 webdriver 标记
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // 伪装 plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: 'Portable Document Format'},
                {name: 'Native Client', filename: 'internal-nacl-plugin', description: 'Native Client module'},
                {name: 'Widevine Content Decryption Module', filename: 'widevinecdmadapter.dll', description: 'Widevine Content Decryption Module'}
            ]
        });
        
        // 伪装 languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        
        // 伪装 chrome 对象
        window.chrome = {
            runtime: {
                OnInstalledReason: {CHROME_UPDATE: "chrome_update", INSTALL: "install", SHARED_MODULE_UPDATE: "shared_module_update", UPDATE: "update"},
                OnRestartRequiredReason: {APP_UPDATE: "app_update", OS_UPDATE: "os_update", PERIODIC: "periodic"},
                PlatformArch: {ARM: "arm", ARM64: "arm64", MIPS: "mips", MIPS64: "mips64", MIPS64EL: "mips64el", MIPSEL: "mipsel", X86_32: "x86-32", X86_64: "x86-64"},
                PlatformNaclArch: {ARM: "arm", MIPS: "mips", MIPS64: "mips64", MIPS64EL: "mips64el", MIPSEL: "mipsel", MIPSEL64: "mipsel64", X86_32: "x86-32", X86_64: "x86-64"},
                PlatformOs: {ANDROID: "android", CROS: "cros", LINUX: "linux", MAC: "mac", OPENBSD: "openbsd", WIN: "win"},
                RequestUpdateCheckStatus: {NO_UPDATE: "no_update", THROTTLED: "throttled", UPDATE_AVAILABLE: "update_available"}
            },
            loadTimes: () => {},
            csi: () => {},
            app: {
                isInstalled: false,
                InstallState: {DISABLED: "disabled", INSTALLED: "installed", NOT_INSTALLED: "not_installed"},
                RunningState: {CANNOT_RUN: "cannot_run", READY_TO_RUN: "ready_to_run", RUNNING: "running"}
            }
        };
        
        // 伪装 permission 查询
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' 
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters)
        );
        
        // 检测并移除 automation 标记
        delete navigator.__proto__.webdriver;
        """
        
        await context.add_init_script(anti_detect_script)
    
    async def _wait_for_login(self, page: Page) -> bool:
        """
        等待用户完成登录
        
        检测逻辑：
        1. 检查关键 Cookie 是否存在（webId, xhsTrackerId）
        2. 检查用户头像是否加载（确认真正登录）
        3. 检查登录按钮是否消失
        
        Args:
            page: Playwright 页面对象
            
        Returns:
            是否登录成功
            
        Raises:
            XHSLoginTimeoutError: 登录超时
        """
        start_time = asyncio.get_event_loop().time()
        check_interval = 2  # 每 2 秒检查一次
        
        self._notify("等待登录完成，请在浏览器中操作（支持扫码/手机号/验证码）...")
        
        while True:
            # 检查是否超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > self.timeout:
                raise XHSLoginTimeoutError(f"登录超时（{self.timeout}秒），请重试")
            
            # 获取当前 Cookie
            cookies = await page.context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            
            # 检查关键登录态字段
            has_webid = "webId" in cookie_dict
            has_tracker = "xhsTrackerId" in cookie_dict
            has_session = any(key in cookie_dict for key in ["web_session", "session.EDITH"])
            
            if has_webid and has_tracker:
                # 额外检查：确认用户已登录（头像加载）
                try:
                    # 检查是否存在用户头像或用户相关元素
                    avatar_selectors = [
                        'img[class*="avatar"]',
                        'img[class*="user-avatar"]',
                        '[class*="user-info"]',
                        '[class*="logged-in"]',
                    ]
                    
                    for selector in avatar_selectors:
                        element = await page.query_selector(selector)
                        if element and await element.is_visible():
                            self._notify(f"检测到登录成功标记（元素: {selector}）")
                            return True
                    
                    # 如果没有找到头像，但 session cookie 存在，也认为是登录成功
                    if has_session:
                        self._notify("检测到登录态 Cookie，登录成功")
                        return True
                        
                except Exception:
                    pass
            
            # 检查是否还在登录页面（登录按钮是否存在）
            try:
                login_btn = await page.query_selector('div[class*="login"], button[class*="login"]')
                if not login_btn or not await login_btn.is_visible():
                    # 登录按钮消失，可能是登录成功
                    if has_webid:
                        self._notify("登录界面已关闭，检测到登录态")
                        return True
            except Exception:
                pass
            
            # 显示剩余时间
            remaining = int(self.timeout - elapsed)
            if remaining % 10 == 0:  # 每 10 秒提醒一次
                self._notify(f"等待登录中... 剩余 {remaining} 秒")
            
            await asyncio.sleep(check_interval)
    
    async def _extract_user_info(self, page: Page) -> Optional[Dict[str, Any]]:
        """
        提取用户信息
        
        Args:
            page: Playwright 页面对象
            
        Returns:
            用户信息字典，或 None
        """
        try:
            # 尝试从页面中提取用户信息
            user_info = await page.evaluate("""() => {
                // 尝试多种方式获取用户信息
                const result = { nickname: null, user_id: null };
                
                // 方式1：从 window.__INITIAL_STATE__ 获取
                if (window.__INITIAL_STATE__) {
                    const state = window.__INITIAL_STATE__;
                    if (state.user && state.user.userInfo) {
                        result.nickname = state.user.userInfo.nickname;
                        result.user_id = state.user.userInfo.userId;
                    }
                }
                
                // 方式2：从页面元素获取昵称
                if (!result.nickname) {
                    const nickElements = document.querySelectorAll('[class*="nickname"], [class*="user-name"]');
                    for (const el of nickElements) {
                        if (el.textContent && el.textContent.trim()) {
                            result.nickname = el.textContent.trim();
                            break;
                        }
                    }
                }
                
                return result;
            }""")
            
            if user_info and user_info.get("nickname"):
                return user_info
                
        except Exception as e:
            self._notify(f"提取用户信息失败: {e}")
        
        return None
    
    async def interactive_login(self) -> XHSAuthData:
        """
        执行交互式浏览器登录
        
        流程：
        1. 启动带反检测的浏览器
        2. 打开小红书登录页
        3. 等待用户完成登录
        4. 提取并加密保存鉴权信息
        
        Returns:
            XHSAuthData: 鉴权数据
            
        Raises:
            XHSLoginTimeoutError: 登录超时
            XHSLoginFailedError: 登录失败
            XHSAuthError: 其他鉴权错误
        """
        self._notify("启动浏览器...")
        
        try:
            # 启动浏览器
            browser, context = await self._launch_browser()
            
            # 创建新页面
            page = await context.new_page()
            self._page = page
            
            # 访问小红书
            self._notify(f"正在打开 {self.config.login_url} ...")
            await page.goto(self.config.login_url, wait_until="networkidle", timeout=60000)
            
            # 等待页面加载完成
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # 额外等待确保页面完全渲染
            
            # 等待用户登录
            await self._wait_for_login(page)
            
            self._notify("登录成功，正在提取鉴权信息...")
            
            # 获取存储状态
            storage_state = await context.storage_state()
            cookies = await context.cookies()
            user_agent = await page.evaluate("() => navigator.userAgent")
            
            # 提取用户信息
            user_info = await self._extract_user_info(page)
            if user_info:
                self._notify(f"检测到用户: {user_info.get('nickname', '未知')}")
            
            # 构建鉴权数据
            auth_data = XHSAuthData(
                cookies=cookies,
                local_storage=storage_state.get("origins", []),
                session_storage=[],  # Playwright 的 storage_state 包含在 origins 中
                user_agent=user_agent,
                timestamp=datetime.now(timezone.utc).timestamp(),
                user_info=user_info,
            )
            
            self._notify("鉴权信息提取完成")
            return auth_data
            
        except XHSLoginTimeoutError:
            raise
        except Exception as e:
            raise XHSLoginFailedError(f"登录过程出错: {str(e)}")
        finally:
            await self.close()
    
    async def close(self) -> None:
        """关闭浏览器资源"""
        if self._browser:
            try:
                await self._browser.close()
                self._notify("浏览器已关闭")
            except Exception:
                pass
            finally:
                self._browser = None
                self._context = None
                self._page = None
    
    async def __aenter__(self) -> "XiaohongshuAuthHelper":
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.close()


class XiaohongshuAuthManager:
    """
    小红书鉴权管理器
    
    整合交互式登录和数据库存储，提供完整的鉴权管理功能。
    
    使用示例:
        # 方式1：交互式登录（推荐首次使用）
        manager = XiaohongshuAuthManager()
        success = await manager.login_interactive()
        
        # 方式2：保存鉴权数据到数据库
        auth_data = await manager.login_interactive()
        await manager.save_to_database(auth_data)
        
        # 方式3：验证现有鉴权
        is_valid = await manager.verify_auth()
    """
    
    def __init__(self):
        self.auth_helper = XiaohongshuAuthHelper()
        self.auth_manager = get_auth_manager()
    
    async def login_interactive(
        self,
        headless: bool = False,
        timeout: int = 300,
        on_status: Optional[Callable[[str], None]] = None
    ) -> Optional[XHSAuthData]:
        """
        执行交互式登录
        
        Args:
            headless: 是否无头模式
            timeout: 超时时间（秒）
            on_status: 状态回调函数
            
        Returns:
            XHSAuthData 或 None（失败时）
        """
        helper = XiaohongshuAuthHelper(
            headless=headless,
            timeout=timeout,
            on_status=on_status
        )
        
        try:
            auth_data = await helper.interactive_login()
            return auth_data
        except Exception as e:
            if on_status:
                on_status(f"登录失败: {e}")
            else:
                print(f"❌ 登录失败: {e}")
            return None
    
    async def save_to_database(self, auth_data: XHSAuthData) -> bool:
        """
        保存鉴权数据到数据库
        
        Args:
            auth_data: 鉴权数据
            
        Returns:
            是否保存成功
        """
        try:
            # 转换为 cURL 格式存储（兼容现有 AuthManager）
            cookie_str = auth_data.get_cookie_string()
            
            # 构建模拟的 cURL 命令
            curl_command = f'curl -H "Cookie: {cookie_str}" -H "User-Agent: {auth_data.user_agent}" https://www.xiaohongshu.com'
            
            # 使用 AuthManager 保存
            success, message = await self.auth_manager.add_auth(
                source_name="xiaohongshu",
                curl_command=curl_command,
                username=auth_data.user_info.get("nickname") if auth_data.user_info else None
            )
            
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ 保存失败: {message}")
            
            return success
            
        except Exception as e:
            print(f"❌ 保存鉴权数据失败: {e}")
            return False
    
    async def verify_auth(self) -> tuple[bool, str]:
        """
        验证现有鉴权是否有效
        
        Returns:
            (是否有效, 消息)
        """
        return await self.auth_manager.test_auth("xiaohongshu")
    
    async def get_auth_data(self) -> Optional[XHSAuthData]:
        """
        从数据库加载鉴权数据
        
        Returns:
            XHSAuthData 或 None
        """
        try:
            async with get_session() as session:
                from src.database import AuthCredentialRepository
                repo = AuthCredentialRepository(session)
                credential = await repo.get_by_source("xiaohongshu")
            
            if not credential:
                return None
            
            # 解密凭证
            from src.auth_manager import decrypt_credentials
            cookie_str = decrypt_credentials(credential.credentials)
            headers = json.loads(credential.headers or "{}")
            
            # 解析 Cookie 字符串
            cookies = []
            for item in cookie_str.split(";"):
                item = item.strip()
                if "=" in item:
                    name, value = item.split("=", 1)
                    cookies.append({
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": ".xiaohongshu.com",
                        "path": "/"
                    })
            
            return XHSAuthData(
                cookies=cookies,
                local_storage=[],
                session_storage=[],
                user_agent=headers.get("User-Agent", ""),
                timestamp=credential.created_at.timestamp() if credential.created_at else 0,
            )
            
        except Exception as e:
            print(f"加载鉴权数据失败: {e}")
            return None


# 便捷函数
async def xhs_login_interactive(
    headless: bool = False,
    timeout: int = 300,
    save_to_db: bool = True
) -> bool:
    """
    小红书交互式登录便捷函数
    
    Args:
        headless: 是否无头模式
        timeout: 超时时间（秒）
        save_to_db: 是否自动保存到数据库
        
    Returns:
        是否登录成功
    """
    manager = XiaohongshuAuthManager()
    
    auth_data = await manager.login_interactive(
        headless=headless,
        timeout=timeout,
        on_status=lambda msg: print(f"[小红书登录] {msg}")
    )
    
    if not auth_data:
        return False
    
    if save_to_db:
        return await manager.save_to_database(auth_data)
    
    return True


# CLI 支持
if __name__ == "__main__":
    import sys
    
    async def main():
        """命令行入口"""
        headless = "--headless" in sys.argv
        
        print("=" * 50)
        print("小红书交互式登录工具")
        print("=" * 50)
        print("\n将打开浏览器，请在浏览器中完成登录操作。")
        print("支持：扫码登录 / 手机号登录 / 验证码登录\n")
        
        success = await xhs_login_interactive(headless=headless)
        
        if success:
            print("\n✅ 登录成功！鉴权信息已保存到数据库。")
            sys.exit(0)
        else:
            print("\n❌ 登录失败。")
            sys.exit(1)
    
    asyncio.run(main())
