"""
小红书采集器
支持采集小红书热门笔记、搜索关键词
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class XiaohongshuCollector(BaseCollector):
    """小红书采集器"""
    
    BASE_URL = "https://www.xiaohongshu.com"
    API_URL = "https://edith.xiaohongshu.com/api/sns/web/v1"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.SOCIAL, config)
        self.collect_type = config.get("collect_type", "hot")  # hot, search
        self.keyword = config.get("keyword", "")
        self.category = config.get("category", "technology")  # technology, lifestyle, etc.
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
        # 由于小红书有反爬机制，这里使用简化版本
        # 实际使用时可能需要 Playwright 或更复杂的反爬处理
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
        # 构建搜索 URL
        search_url = f"{self.BASE_URL}/search_result?keyword={self.keyword}&type=51"
        
        try:
            response = await self.fetch_url(search_url, headers=self._headers)
            html = response.text
            
            # 从搜索结果页面解析
            items = self._parse_notes_from_html(html)
            return items[:self.limit]
            
        except Exception as e:
            print(f"[Xiaohongshu] 搜索采集失败: {e}")
            return []
    
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
                    item = self._parse_note(note_data)
                    if item:
                        items.append(item)
            except Exception as e:
                print(f"[Xiaohongshu] 解析初始状态失败: {e}")
        
        # 如果上面的方法失败，尝试从其他位置提取
        if not items:
            # 尝试从 SSR 数据中提取
            pattern = r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.+?})</script>'
            match = re.search(pattern, html)
            if match:
                try:
                    data = json.loads(match.group(1))
                    notes = self._extract_notes_from_ssr(data)
                    for note_data in notes:
                        item = self._parse_note(note_data)
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
        
        # 遍历数据结构查找笔记
        def find_notes(obj):
            if isinstance(obj, dict):
                if "noteCard" in obj or "id" in obj and "title" in obj:
                    notes.append(obj)
                for v in obj.values():
                    find_notes(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_notes(item)
        
        find_notes(data)
        return notes
    
    def _parse_note(self, note: Dict) -> Optional[ContentItem]:
        """解析单条笔记"""
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
                # 尝试多种时间格式
                if isinstance(time_str, int):
                    publish_time = datetime.fromtimestamp(time_str)
                else:
                    # 处理字符串格式
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
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            author=author,
            publish_time=publish_time,
            keywords=keywords,
            image_url=image_url,
            raw_data=note,
            extra={
                "note_id": note_id,
                "likes": likes,
                "collects": collects,
                "comments": comments,
                "type": note.get("type", "normal")
            }
        )


class XiaohongshuSearchCollector(XiaohongshuCollector):
    """小红书搜索采集器（简化版）"""
    
    def __init__(self, name: str, config: Dict):
        config["collect_type"] = "search"
        super().__init__(name, config)
