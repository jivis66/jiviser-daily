"""
小红书采集器
支持采集小红书热门笔记、搜索关键词、用户关注流
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.collector.base import BaseCollector, CollectorResult
from src.collector.base_auth_collector import (
    AuthenticatedCollector, 
    AuthError, 
    AuthExpiredError,
    AuthRequiredError
)
from src.models import ContentItem, SourceType


class XiaohongshuBaseCollector:
    """小红书采集器工具基类（提供通用解析方法）"""
    
    BASE_URL = "https://www.xiaohongshu.com"
    API_URL = "https://edith.xiaohongshu.com/api/sns/web/v1"
    
    def _parse_notes_from_html(self, html: str) -> List[ContentItem]:
        """从 HTML 中解析笔记数据"""
        items = []
        
        # 尝试从 window.__INITIAL_STATE__ 中提取数据
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.+?});'
        match = re.search(pattern, html)
        
        if match:
            try:
                data = json.loads(match.group(1))
                notes = self._extract_notes_from_state(data)
                for note_data in notes:
                    item = self._parse_note_item(note_data)
                    if item:
                        items.append(item)
            except Exception as e:
                print(f"[Xiaohongshu] 解析初始状态失败: {e}")
        
        # 如果上面的方法失败，尝试从 SSR 数据中提取
        if not items:
            pattern = r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.+?})</script>'
            match = re.search(pattern, html)
            if match:
                try:
                    data = json.loads(match.group(1))
                    notes = self._extract_notes_from_ssr(data)
                    for note_data in notes:
                        item = self._parse_note_item(note_data)
                        if item:
                            items.append(item)
                except Exception as e:
                    print(f"[Xiaohongshu] 解析 SSR 数据失败: {e}")
        
        return items
    
    def _extract_notes_from_state(self, data: Dict) -> List[Dict]:
        """从初始状态中提取笔记列表"""
        notes = []
        
        # 尝试不同的数据路径
        if "explore" in data and "notes" in data["explore"]:
            notes.extend(data["explore"]["notes"])
        
        if "search" in data and "notes" in data["search"]:
            notes.extend(data["search"]["notes"])
        
        # 通用提取
        for key in data:
            if isinstance(data[key], dict):
                if "notes" in data[key] and isinstance(data[key]["notes"], list):
                    notes.extend(data[key]["notes"])
        
        return notes
    
    def _extract_notes_from_ssr(self, data: Dict) -> List[Dict]:
        """从 SSR 数据中提取笔记"""
        notes = []
        
        def find_notes(obj):
            if isinstance(obj, dict):
                if "noteCard" in obj or ("id" in obj and "title" in obj):
                    notes.append(obj)
                for v in obj.values():
                    find_notes(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_notes(item)
        
        find_notes(data)
        return notes
    
    def _parse_note_item(self, note: Dict) -> Optional[ContentItem]:
        """解析单条笔记为 ContentItem"""
        # 处理不同格式的数据
        if "noteCard" in note:
            note = note["noteCard"]
        
        note_id = note.get("id") or note.get("noteId")
        if not note_id:
            return None
        
        title = note.get("title", "")
        desc = note.get("desc", "") or note.get("content", "")
        
        # 如果没有标题，使用内容前30字
        if not title and desc:
            title = desc[:30] + "..." if len(desc) > 30 else desc
        elif not title:
            title = "无标题笔记"
        
        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        
        # 作者信息
        author = "未知作者"
        user = note.get("user") or note.get("userInfo")
        if user:
            author = user.get("nickname", "未知作者")
        
        # 互动数据
        likes = note.get("likes", 0) or note.get("interactInfo", {}).get("likedCount", 0)
        collects = note.get("collects", 0) or note.get("interactInfo", {}).get("collectedCount", 0)
        comments = note.get("comments", 0) or note.get("interactInfo", {}).get("commentCount", 0)
        
        # 构建内容
        content_parts = [
            f"作者: {author}",
            f"点赞: {likes}",
            f"收藏: {collects}",
            f"评论: {comments}",
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
                else:
                    publish_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            except:
                pass
        
        # 图片
        image_url = None
        if note.get("cover"):
            image_url = note["cover"].get("url") or note["cover"].get("urlDefault")
        elif note.get("imageList") and len(note["imageList"]) > 0:
            image_url = note["imageList"][0].get("url")
        
        # 关键词/标签
        keywords = []
        if note.get("tags"):
            keywords = [tag.get("name", "") for tag in note["tags"] if tag.get("name")]
        
        # 计算热度分数
        popularity = min((likes + collects * 2 + comments * 3) / 100, 10)
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            author=author,
            publish_time=publish_time,
            keywords=keywords,
            image_url=image_url,
            popularity_score=popularity,
            raw_data=note,
            extra={
                "note_id": note_id,
                "likes": likes,
                "collects": collects,
                "comments": comments,
                "type": note.get("type", "normal"),
                "source": "小红书"
            }
        )
    
    def create_content_item(self, **kwargs) -> ContentItem:
        """
        创建 ContentItem 实例
        
        子类需要实现此方法或继承自 BaseCollector
        """
        raise NotImplementedError("子类必须实现 create_content_item 方法")


class XiaohongshuCollector(BaseCollector, XiaohongshuBaseCollector):
    """
    小红书公开内容采集器
    
    采集公开访问的小红书内容（热门、搜索），不需要登录
    """
    
    def __init__(self, name: str, config: Dict):
        BaseCollector.__init__(self, name, SourceType.SOCIAL, config)
        XiaohongshuBaseCollector.__init__(self)
        
        self.collect_type = config.get("collect_type", "hot")  # hot, search
        self.keyword = config.get("keyword", "")
        self.category = config.get("category", "technology")
        self.limit = config.get("limit", 10)
        
        # 小红书需要特定的请求头
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
        }
    
    async def collect(self) -> CollectorResult:
        """采集小红书内容"""
        result = CollectorResult()
        
        try:
            if self.collect_type == "hot":
                items = await self._collect_hot()
            elif self.collect_type == "search" and self.keyword:
                items = await self._collect_search()
            else:
                result.success = False
                result.message = "配置错误：请提供正确的 collect_type 和对应参数"
                return result
            
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
            result.message = f"小红书采集失败: {str(e)}"
        
        return result
    
    async def _collect_hot(self) -> List[ContentItem]:
        """采集热门笔记（通过网页端）"""
        url = f"{self.BASE_URL}/explore"
        
        try:
            response = await self.fetch_url(url, headers=self._headers)
            html = response.text
            
            # 尝试从页面中提取笔记数据
            items = self._parse_notes_from_html(html)
            return items[:self.limit]
            
        except Exception as e:
            print(f"[Xiaohongshu] 热门采集失败: {e}")
            return []
    
    async def _collect_search(self) -> List[ContentItem]:
        """按关键词搜索笔记"""
        search_url = f"{self.BASE_URL}/search_result?keyword={self.keyword}&type=51"
        
        try:
            response = await self.fetch_url(search_url, headers=self._headers)
            html = response.text
            
            # 从搜索结果页面解析
            items = self._parse_notes_from_html(html)
            return items[:self.limit]
            
        except Exception as e:
            print(f"[Xiaonghongshu] 搜索采集失败: {e}")
            return []


class XiaohongshuAuthenticatedCollector(AuthenticatedCollector, XiaohongshuBaseCollector):
    """
    小红书认证采集器（支持登录态）
    
    采集用户关注流、推荐内容等需要登录的内容
    
    使用新的 xiaohongshu_auth 模块获取登录态：
        from src.collector.xiaohongshu_auth import xhs_login_interactive
        await xhs_login_interactive()
    """
    
    def __init__(self, config: Optional[Dict] = None):
        AuthenticatedCollector.__init__(self, "xiaohongshu_feed", SourceType.SOCIAL, config)
        XiaohongshuBaseCollector.__init__(self)
        
        self.auth_source = "xiaohongshu"
        self.api_base = "https://edith.xiaohongshu.com"
        self.collect_type = config.get("collect_type", "following") if config else "following"
        self.limit = config.get("limit", 20) if config else 20
    
    async def collect_with_auth(self) -> CollectorResult:
        """
        执行认证采集
        
        根据 collect_type 选择不同的采集策略：
        - following: 关注流
        - recommend: 推荐内容
        - home: 首页内容
        """
        items = []
        
        try:
            if self.collect_type == "following":
                items = await self._collect_following()
            elif self.collect_type == "recommend":
                items = await self._collect_recommend()
            else:
                # 默认采集关注流
                items = await self._collect_following()
            
            return CollectorResult(
                success=True,
                items=items,
                total_found=len(items) + self.total_filtered,
                total_filtered=self.total_filtered,
                message=f"成功采集 {len(items)} 条小红书内容"
            )
            
        except Exception as e:
            return CollectorResult(
                success=False,
                message=f"小红书认证采集失败: {str(e)}",
                items=items
            )
    
    async def _collect_following(self) -> List[ContentItem]:
        """采集关注流"""
        items = []
        
        # 小红书 API 需要动态签名（X-S, X-T）
        # 这里使用简化版本，实际需要逆向或模拟签名
        api_url = f"{self.api_base}/api/sns/web/v1/feed"
        
        # 构建请求数据
        payload = {
            "cursor": "",
            "feed_type": "following",
            "page_size": self.limit
        }
        
        # 构建请求头
        extra_headers = {
            "Content-Type": "application/json",
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "X-B3-TraceId": self._generate_trace_id(),
        }
        
        try:
            # 注意：小红书 API 有严格的反爬机制，可能需要额外处理
            response = await self.fetch_with_auth(
                api_url,
                method="POST",
                json=payload,
                extra_headers=extra_headers
            )
            
            data = response.json()
            notes = data.get("data", {}).get("items", [])
            
            for note in notes:
                item = self._parse_api_note(note)
                if item and self.should_include(item):
                    items.append(item)
                else:
                    self.total_filtered += 1
            
        except Exception as e:
            print(f"[Xiaohongshu] 关注流采集失败: {e}")
            # 失败时尝试使用备用方法
            items = await self._collect_following_fallback()
        
        return items
    
    async def _collect_recommend(self) -> List[ContentItem]:
        """采集推荐内容"""
        # 推荐内容的 API 端点可能不同
        api_url = f"{self.api_base}/api/sns/web/v1/homefeed"
        
        payload = {
            "cursor": "",
            "feed_type": "recommend",
            "page_size": self.limit
        }
        
        extra_headers = {
            "Content-Type": "application/json",
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
        }
        
        try:
            response = await self.fetch_with_auth(
                api_url,
                method="POST",
                json=payload,
                extra_headers=extra_headers
            )
            
            data = response.json()
            notes = data.get("data", {}).get("items", [])
            
            items = []
            for note in notes:
                item = self._parse_api_note(note)
                if item and self.should_include(item):
                    items.append(item)
            
            return items
            
        except Exception as e:
            print(f"[Xiaohongshu] 推荐采集失败: {e}")
            return []
    
    async def _collect_following_fallback(self) -> List[ContentItem]:
        """关注流采集备用方案（通过网页端）"""
        # 当 API 调用失败时，尝试通过网页端获取
        url = "https://www.xiaohongshu.com"
        
        try:
            headers = self.get_auth_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            })
            
            response = await self.client.get(url, headers=headers, follow_redirects=True)
            html = response.text
            
            items = self._parse_notes_from_html(html)
            filtered_items = []
            for item in items:
                if self.should_include(item):
                    filtered_items.append(item)
                else:
                    self.total_filtered += 1
            
            return filtered_items[:self.limit]
            
        except Exception as e:
            print(f"[Xiaohongshu] 备用采集也失败: {e}")
            return []
    
    def _parse_api_note(self, note: Dict) -> Optional[ContentItem]:
        """解析 API 返回的笔记数据"""
        note_card = note.get("note_card", {}) or note.get("noteCard", {})
        
        if not note_card:
            # 尝试直接解析
            note_card = note
        
        note_id = note_card.get("note_id") or note_card.get("id")
        if not note_id:
            return None
        
        title = note_card.get("title", "")
        desc = note_card.get("desc", "") or note_card.get("content", "")
        
        if not title and desc:
            title = desc[:30] + "..." if len(desc) > 30 else desc
        elif not title:
            title = "无标题笔记"
        
        # 作者信息
        user = note_card.get("user", {}) or note_card.get("userInfo", {})
        author = user.get("nickname", "未知作者")
        
        # 互动数据
        interact = note_card.get("interact_info", {}) or note_card.get("interactInfo", {})
        likes = interact.get("liked_count", 0) or interact.get("likedCount", 0)
        collects = interact.get("collected_count", 0) or interact.get("collectedCount", 0)
        comments = interact.get("comment_count", 0) or interact.get("commentCount", 0)
        
        # 图片
        image_url = ""
        if note_card.get("cover"):
            image_url = note_card["cover"].get("url", "")
        elif note_card.get("imageList"):
            image_url = note_card["imageList"][0].get("url", "")
        
        # 标签
        tags = note_card.get("tag_list", []) or note_card.get("tagList", [])
        keywords = [tag.get("name", "") for tag in tags if tag.get("name")]
        
        # 计算热度
        popularity = min((likes + collects * 2 + comments * 3) / 100, 10)
        
        return self.create_content_item(
            title=title,
            url=f"https://www.xiaohongshu.com/explore/{note_id}",
            content=desc,
            author=author,
            image_url=image_url,
            keywords=keywords,
            popularity_score=popularity,
            extra={
                "note_id": note_id,
                "likes": likes,
                "collects": collects,
                "comments": comments,
                "source": "小红书-关注",
                "user_id": user.get("user_id", "")
            }
        )
    
    def _generate_trace_id(self) -> str:
        """生成追踪 ID（小红书 API 需要）"""
        import random
        import string
        return ''.join(random.choices(string.hexdigits.lower(), k=16))


class XiaohongshuSearchCollector(XiaohongshuCollector):
    """小红书搜索采集器"""
    
    def __init__(self, name: str, config: Dict):
        config["collect_type"] = "search"
        super().__init__(name, config)


# 便捷函数
def create_xiaohongshu_collector(name: str, config: Dict) -> BaseCollector:
    """
    创建小红书采集器工厂函数
    
    根据配置自动选择公开采集器或认证采集器
    
    Args:
        name: 采集器名称
        config: 配置字典
        
    Returns:
        BaseCollector 实例
    """
    # 如果需要登录态，使用认证采集器
    if config.get("require_auth", False) or config.get("collect_type") in ["following", "recommend"]:
        return XiaohongshuAuthenticatedCollector(config)
    
    # 否则使用公开采集器
    return XiaohongshuCollector(name, config)
