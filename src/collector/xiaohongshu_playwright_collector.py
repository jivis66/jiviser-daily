"""
小红书 Playwright 采集器
使用真实浏览器绕过反爬机制
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class XiaohongshuPlaywrightCollector(BaseCollector):
    """
    小红书 Playwright 采集器
    
    使用真实浏览器访问小红书，绕过反爬限制
    需要已配置的小红书认证信息
    """
    
    BASE_URL = "https://www.xiaohongshu.com"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.SOCIAL, config)
        self.collect_type = config.get("collect_type", "feed")  # feed, search, user
        self.keyword = config.get("keyword", "")
        self.user_id = config.get("user_id", "")
        self.limit = config.get("limit", 10)
        self.headless = config.get("headless", True)  # 是否无头模式
        self.timeout = config.get("timeout", 30)
        
        self._browser = None
        self._context = None
        self._page = None
    
    async def _init_browser(self):
        """初始化浏览器"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("请先安装 Playwright: pip install playwright")
        
        self._playwright = await async_playwright().start()
        
        # 尝试启动浏览器
        browser = None
        
        # 尝试系统 Chrome
        import os
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chrome.app/Contents/MacOS/Chrome",
            "/usr/bin/google-chrome",
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    browser = await self._playwright.chromium.launch(
                        headless=self.headless,
                        executable_path=chrome_path
                    )
                    break
                except:
                    pass
        
        # 使用 Playwright 自带浏览器
        if not browser:
            browser = await self._playwright.chromium.launch(headless=self.headless)
        
        self._browser = browser
        self._context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        self._page = await self._context.new_page()
    
    async def _close_browser(self):
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def _load_auth(self):
        """加载认证信息"""
        from src.database import get_session, AuthCredentialRepository
        
        async with get_session() as session:
            repo = AuthCredentialRepository(session)
            auth_data = await repo.get_by_source('xiaohongshu')
            
            if not auth_data:
                raise ValueError("未找到小红书认证信息，请先运行: python -m src.cli auth add xiaohongshu")
            
            # 解密 cookie
            from src.auth_manager import decrypt_credentials
            cookie_str = decrypt_credentials(auth_data.credentials)
            
            # 解析 cookie
            cookies = []
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.xiaohongshu.com',
                        'path': '/'
                    })
            
            # 添加 cookie 到上下文
            await self._context.add_cookies(cookies)
            return True
    
    async def collect(self) -> CollectorResult:
        """采集内容"""
        result = CollectorResult()
        
        try:
            # 初始化浏览器
            await self._init_browser()
            
            # 加载认证
            try:
                await self._load_auth()
            except ValueError as e:
                result.success = False
                result.message = str(e)
                await self._close_browser()
                return result
            
            # 根据类型采集
            if self.collect_type == "feed":
                items = await self._collect_feed()
            elif self.collect_type == "search":
                items = await self._collect_search()
            elif self.collect_type == "user":
                items = await self._collect_user_notes()
            else:
                items = []
            
            # 过滤
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条小红书内容"
            
        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"
        finally:
            await self._close_browser()
        
        return result
    
    async def _collect_feed(self) -> List[ContentItem]:
        """采集推荐流"""
        await self._page.goto("https://www.xiaohongshu.com/explore")
        await asyncio.sleep(3)  # 等待加载
        
        # 滚动加载更多
        for _ in range(3):
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        
        # 提取数据
        notes = await self._page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            if (state && state.explore && state.explore.notes) {
                return state.explore.notes;
            }
            // 尝试从 DOM 提取
            const items = [];
            document.querySelectorAll('.feeds-page > div > div').forEach(el => {
                const title = el.querySelector('a')?.textContent || '';
                const link = el.querySelector('a')?.href || '';
                if (title && link) {
                    items.push({ title, link, fromDOM: true });
                }
            });
            return items;
        }""")
        
        if not notes:
            return []
        
        items = []
        for note_data in notes[:self.limit]:
            item = self._parse_note_data(note_data)
            if item:
                items.append(item)
        
        return items
    
    async def _collect_search(self) -> List[ContentItem]:
        """搜索采集"""
        if not self.keyword:
            return []
        
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={self.keyword}&type=51"
        await self._page.goto(search_url)
        await asyncio.sleep(3)
        
        # 提取搜索结果
        notes = await self._page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            if (state && state.search && state.search.notes) {
                return state.search.notes;
            }
            return [];
        }""")
        
        items = []
        for note_data in notes[:self.limit]:
            item = self._parse_note_data(note_data)
            if item:
                items.append(item)
        
        return items
    
    async def _collect_user_notes(self) -> List[ContentItem]:
        """采集指定用户的笔记"""
        if not self.user_id:
            return []
        
        user_url = f"https://www.xiaohongshu.com/user/profile/{self.user_id}"
        await self._page.goto(user_url)
        await asyncio.sleep(3)
        
        # 滚动加载
        for _ in range(3):
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        
        notes = await self._page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            if (state && state.user && state.user.notes) {
                return state.user.notes;
            }
            return [];
        }""")
        
        items = []
        for note_data in notes[:self.limit]:
            item = self._parse_note_data(note_data)
            if item:
                items.append(item)
        
        return items
    
    def _parse_note_data(self, note: Dict) -> Optional[ContentItem]:
        """解析笔记数据"""
        # 处理嵌套格式
        if "noteCard" in note:
            note = note["noteCard"]
        
        note_id = note.get("id") or note.get("noteId")
        if not note_id:
            return None
        
        title = note.get("title", "")
        desc = note.get("desc", "") or note.get("content", "")
        
        if not title and desc:
            title = desc[:30] + "..." if len(desc) > 30 else desc
        elif not title:
            title = "无标题笔记"
        
        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        
        # 作者
        author = "未知作者"
        user = note.get("user") or note.get("userInfo")
        if user:
            author = user.get("nickname", "未知作者")
        
        # 互动数据
        likes = note.get("likes", 0) or note.get("interactInfo", {}).get("likedCount", 0)
        collects = note.get("collects", 0) or note.get("interactInfo", {}).get("collectedCount", 0)
        comments = note.get("comments", 0) or note.get("interactInfo", {}).get("commentCount", 0)
        
        content_parts = [
            f"作者: {author}",
            f"点赞: {likes}  收藏: {collects}  评论: {comments}",
            "",
            desc
        ]
        
        # 发布时间
        publish_time = None
        time_str = note.get("time") or note.get("createTime")
        if time_str:
            try:
                if isinstance(time_str, int):
                    publish_time = datetime.fromtimestamp(time_str)
            except:
                pass
        
        # 图片
        image_url = None
        if note.get("cover"):
            image_url = note["cover"].get("url") or note["cover"].get("urlDefault")
        
        # 关键词
        keywords = []
        if note.get("tags"):
            keywords = [tag.get("name", "") for tag in note["tags"] if tag.get("name")]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            author=author,
            publish_time=publish_time,
            keywords=keywords,
            image_url=image_url,
            raw_data=note
        )
