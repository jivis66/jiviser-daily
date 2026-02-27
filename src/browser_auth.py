"""
浏览器自动化认证模块
使用 Playwright 自动获取 Cookie
"""
import asyncio
from typing import Dict, Optional, Tuple


# Playwright 延迟导入，避免未安装时报错
def _get_playwright():
    try:
        from playwright.async_api import async_playwright, Page
        return async_playwright, Page
    except ImportError:
        raise ImportError(
            "Playwright 未安装，请运行:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        )


from src.auth_manager import get_auth_manager, AUTH_CONFIGS


class BrowserAuthHelper:
    """浏览器认证助手"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.config = AUTH_CONFIGS.get(source_name)
        self.cookie_str: Optional[str] = None
        self.headers: Dict[str, str] = {}
        
    async def get_cookie_interactive(self) -> Tuple[bool, str]:
        """
        交互式获取 Cookie
        
        Returns:
            (成功, cookie字符串或错误信息)
        """
        if not self.config:
            return False, f"不支持的渠道: {self.source_name}"
        
        # 延迟导入 Playwright
        try:
            async_playwright, Page = _get_playwright()
        except ImportError as e:
            return False, str(e)
        
        async with async_playwright() as p:
            # 启动浏览器 - 优先使用系统 Chrome
            browser = None
            launch_errors = []
            
            # 尝试 1: 使用系统 Chrome (Mac)
            import os
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Chrome",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    try:
                        browser = await p.chromium.launch(
                            headless=False,
                            executable_path=chrome_path
                        )
                        break
                    except Exception as e:
                        launch_errors.append(f"{chrome_path}: {e}")
            
            # 尝试 2: 使用 Playwright 自带的 Chromium
            if not browser:
                try:
                    browser = await p.chromium.launch(headless=False)
                except Exception as e:
                    error_msg = str(e)
                    if "Executable doesn't exist" in error_msg:
                        return False, (
                            "未找到 Chrome 浏览器\n\n"
                            "方案 1 - 安装 Google Chrome:\n"
                            "  下载: https://www.google.com/chrome/\n\n"
                            "方案 2 - 使用 Playwright 自带浏览器:\n"
                            "  python -m playwright install chromium\n\n"
                            "安装后即可使用浏览器自动获取功能。"
                        )
                    launch_errors.append(f"Playwright Chromium: {e}")
            
            if not browser:
                return False, f"无法启动浏览器:\n" + "\n".join(launch_errors)
            
            # 设置请求拦截，捕获请求头
            captured_request = {}
            
            async def handle_route(route, request):
                """拦截请求并捕获 headers"""
                if self.config.test_endpoint in request.url:
                    captured_request['headers'] = await request.all_headers()
                    captured_request['url'] = request.url
                await route.continue_()
            
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            
            # 启用请求拦截
            await page.route("**/*", handle_route)
            
            print(f"\n{'='*60}")
            print(f"正在为 [{self.config.display_name}] 获取认证信息")
            print(f"{'='*60}\n")
            print(f"1. 浏览器已启动，请登录您的账号")
            print(f"2. 登录成功后，返回终端并按 Enter 确认")
            print(f"3. 系统将自动提取 Cookie 和请求信息\n")
            
            # 打开登录页面
            await page.goto(self.config.login_url)
            
            # 等待用户登录完成
            input("登录完成后请按 Enter 键...")
            
            try:
                # 访问测试接口以捕获请求头
                print("\n正在捕获请求信息...")
                try:
                    await page.goto(self.config.test_endpoint)
                    await asyncio.sleep(2)
                except:
                    pass
                
                # 提取 cookie
                cookies = await context.cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                if not cookie_dict:
                    await browser.close()
                    return False, "未能获取到 Cookie，请检查是否已登录"
                
                # 转换为字符串格式
                self.cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                
                # 优先使用捕获的请求头，否则使用页面 headers
                if captured_request.get('headers'):
                    self.headers = captured_request['headers']
                    # 移除不需要的头
                    for key in ['cookie', 'content-length', 'host']:
                        self.headers.pop(key, None)
                else:
                    self.headers = await self._get_page_headers(page)
                
                # 尝试获取用户信息
                user_info = await self._try_get_user_info(page)
                
                await browser.close()
                
                if user_info:
                    print(f"\n检测到用户信息: {user_info}")
                
                if captured_request.get('headers'):
                    print("✓ 已捕获完整请求头")
                
                return True, self.cookie_str
                
            except Exception as e:
                await browser.close()
                return False, f"获取 Cookie 失败: {e}"
    
    async def _get_page_headers(self, page) -> Dict[str, str]:
        """获取页面请求头信息"""
        headers = {}
        try:
            # 获取 User-Agent
            headers['User-Agent'] = await page.evaluate('() => navigator.userAgent')
        except:
            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # 通用 headers
        headers['Accept'] = 'application/json, text/plain, */*'
        headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'
        headers['Sec-Fetch-Dest'] = 'empty'
        headers['Sec-Fetch-Mode'] = 'cors'
        headers['Sec-Fetch-Site'] = 'same-site'
        
        # 根据平台添加特定 headers
        if self.source_name == 'xiaohongshu':
            headers['Referer'] = 'https://www.xiaohongshu.com/'
            headers['Origin'] = 'https://www.xiaohongshu.com'
            # 小红书特定的 headers
            headers['X-Sign'] = ''  # 可能需要动态生成
            headers['X-Timestamp'] = str(int(asyncio.get_event_loop().time() * 1000))
        elif self.source_name == 'zhihu':
            headers['Referer'] = 'https://www.zhihu.com/'
            headers['x-requested-with'] = 'fetch'
        elif self.source_name == 'jike':
            headers['Referer'] = 'https://web.okjike.com/'
            headers['Origin'] = 'https://web.okjike.com'
        
        return headers
    
    async def _try_get_user_info(self, page) -> Optional[str]:
        """尝试获取用户昵称"""
        try:
            # 小红书
            if self.source_name == "xiaohongshu":
                # 尝试从页面获取用户信息
                try:
                    await page.goto("https://www.xiaohongshu.com/user/profile")
                    await asyncio.sleep(1)
                    nickname = await page.locator(".nickname").first.text_content(timeout=3000)
                    return nickname
                except:
                    pass
            
            # 知乎
            elif self.source_name == "zhihu":
                try:
                    await page.goto("https://www.zhihu.com/people/me")
                    await asyncio.sleep(1)
                    name = await page.locator(".ProfileHeader-name").first.text_content(timeout=3000)
                    return name
                except:
                    pass
            
            # 即刻
            elif self.source_name == "jike":
                try:
                    await page.goto("https://web.okjike.com/")
                    await asyncio.sleep(1)
                    name = await page.locator(".user-name").first.text_content(timeout=3000)
                    return name
                except:
                    pass
                    
        except:
            pass
        
        return None
    
    def get_curl_command(self) -> str:
        """生成完整的 cURL 命令"""
        if not self.cookie_str:
            return ""
        
        url = self.config.test_endpoint if self.config else "https://example.com"
        
        # 构建完整的 cURL 命令
        cmd_parts = [f"curl '{url}'"]
        
        # 添加 headers
        for key, value in self.headers.items():
            cmd_parts.append(f"-H '{key}: {value}'")
        
        # 添加 Cookie
        cmd_parts.append(f"-H 'Cookie: {self.cookie_str}'")
        
        return " ".join(cmd_parts)


async def interactive_auth(source_name: str, username: str = None) -> Tuple[bool, str]:
    """
    交互式认证入口
    
    Args:
        source_name: 渠道名称
        username: 用户名（可选）
        
    Returns:
        (成功, 消息)
    """
    helper = BrowserAuthHelper(source_name)
    
    # 获取 cookie
    success, result = await helper.get_cookie_interactive()
    
    if not success:
        return False, result
    
    # 保存到数据库
    from src.auth_manager import get_auth_manager
    manager = get_auth_manager()
    
    # 构造 cURL 命令
    curl_cmd = helper.get_curl_command()
    
    # 添加认证
    success, message = await manager.add_auth(source_name, curl_cmd, username)
    
    if success:
        # 对于小红书等有严格反爬机制的平台，跳过 HTTP 测试
        # 因为需要动态签名，无法通过简单 cURL 验证
        if source_name in ['xiaohongshu', 'douyin']:
            return True, "认证信息已保存（浏览器自动获取的 Cookie 通常可直接使用）"
        
        # 其他平台尝试 HTTP 测试
        is_valid, test_msg, user_info = await manager.test_auth(source_name)
        if is_valid:
            return True, f"认证成功并已保存。{test_msg}"
        else:
            return True, f"Cookie 已保存，但测试未通过: {test_msg}"
    else:
        return False, message
