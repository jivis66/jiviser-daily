"""
B站采集器
支持采集 B站热门视频、指定 UP 主视频
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class BilibiliCollector(BaseCollector):
    """B站采集器"""
    
    BASE_URL = "https://api.bilibili.com"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.VIDEO, config)
        self.collect_type = config.get("collect_type", "popular")  # popular, mid, search
        self.mid = config.get("mid")  # UP主ID
        self.keyword = config.get("keyword")  # 搜索关键词
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集 B站内容"""
        result = CollectorResult()
        
        try:
            if self.collect_type == "popular":
                items = await self._collect_popular()
            elif self.collect_type == "mid" and self.mid:
                items = await self._collect_by_mid()
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
            result.message = f"成功采集 {len(result.items)} 条 B站内容"
            
        except Exception as e:
            result.success = False
            result.message = f"B站采集失败: {str(e)}"
        
        return result
    
    async def _collect_popular(self) -> List[ContentItem]:
        """采集热门视频"""
        url = f"{self.BASE_URL}/x/web-interface/popular"
        params = {"ps": min(self.limit, 50)}
        
        response = await self.fetch_url(url, params=params)
        data = response.json()
        
        items = []
        if data.get("data", {}).get("list"):
            for video in data["data"]["list"][:self.limit]:
                item = self._parse_video(video)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_by_mid(self) -> List[ContentItem]:
        """采集指定 UP 主的视频"""
        url = f"{self.BASE_URL}/x/space/wbi/arc/search"
        params = {
            "mid": self.mid,
            "ps": min(self.limit, 50),
            "pn": 1
        }
        
        response = await self.fetch_url(url, params=params)
        data = response.json()
        
        items = []
        if data.get("data", {}).get("list", {}).get("vlist"):
            for video in data["data"]["list"]["vlist"][:self.limit]:
                item = self._parse_space_video(video)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_search(self) -> List[ContentItem]:
        """按关键词搜索视频"""
        url = f"{self.BASE_URL}/x/web-interface/search/type"
        params = {
            "keyword": self.keyword,
            "search_type": "video",
            "page": 1,
            "page_size": min(self.limit, 50)
        }
        
        response = await self.fetch_url(url, params=params)
        data = response.json()
        
        items = []
        if data.get("data", {}).get("result"):
            for video in data["data"]["result"][:self.limit]:
                item = self._parse_search_video(video)
                if item:
                    items.append(item)
        
        return items
    
    def _parse_video(self, video: Dict) -> Optional[ContentItem]:
        """解析热门视频数据"""
        bvid = video.get("bvid")
        if not bvid:
            return None
        
        title = video.get("title", "无标题")
        # 移除 HTML 标签
        title = title.replace("<em class=\"keyword\">", "").replace("</em>", "")
        
        url = f"https://www.bilibili.com/video/{bvid}"
        
        # 构建内容描述
        desc = video.get("desc", "")
        owner = video.get("owner", {}).get("name", "未知UP主")
        stat = video.get("stat", {})
        
        content_parts = [
            f"UP主: {owner}",
            f"播放量: {self._format_number(stat.get('view', 0))}",
            f"点赞: {self._format_number(stat.get('like', 0))}",
            f"投币: {self._format_number(stat.get('coin', 0))}",
            f"收藏: {self._format_number(stat.get('favorite', 0))}",
            "",
            f"简介: {desc}" if desc else ""
        ]
        
        # 发布时间
        publish_time = None
        if video.get("pubdate"):
            try:
                publish_time = datetime.fromtimestamp(video["pubdate"])
            except:
                pass
        
        # 关键词
        keywords = []
        if video.get("rcmd_reason"):
            keywords.append(video["rcmd_reason"])
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            author=owner,
            publish_time=publish_time,
            keywords=keywords,
            image_url=video.get("pic"),
            raw_data=video,
            extra={
                "bvid": bvid,
                "cid": video.get("cid"),
                "duration": video.get("duration"),
                "view_count": stat.get("view", 0),
                "like_count": stat.get("like", 0),
                "coin_count": stat.get("coin", 0),
                "favorite_count": stat.get("favorite", 0)
            }
        )
    
    def _parse_space_video(self, video: Dict) -> Optional[ContentItem]:
        """解析空间视频数据"""
        bvid = video.get("bvid")
        if not bvid:
            return None
        
        title = video.get("title", "无标题")
        url = f"https://www.bilibili.com/video/{bvid}"
        
        content_parts = [
            f"UP主: {video.get('author', '未知')}",
            f"播放量: {self._format_number(video.get('play', 0))}",
            f"评论: {self._format_number(video.get('video_review', 0))}",
            "",
            f"简介: {video.get('description', '')}"
        ]
        
        publish_time = None
        if video.get("created"):
            try:
                publish_time = datetime.fromtimestamp(video["created"])
            except:
                pass
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            author=video.get("author", ""),
            publish_time=publish_time,
            image_url=video.get("pic"),
            raw_data=video,
            extra={
                "bvid": bvid,
                "view_count": video.get("play", 0),
                "comment_count": video.get("video_review", 0)
            }
        )
    
    def _parse_search_video(self, video: Dict) -> Optional[ContentItem]:
        """解析搜索结果视频"""
        bvid = video.get("bvid")
        if not bvid:
            return None
        
        title = video.get("title", "无标题")
        # 移除高亮标签
        title = title.replace("<em class=\"keyword\">", "").replace("</em>", "")
        
        url = f"https://www.bilibili.com/video/{bvid}"
        
        content_parts = [
            f"UP主: {video.get('author', '未知')}",
            f"播放量: {self._format_number(video.get('play', 0))}",
            f"时长: {video.get('duration', '未知')}",
            "",
            f"简介: {video.get('description', '')}"
        ]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            author=video.get("author", ""),
            image_url=video.get("pic"),
            raw_data=video,
            extra={
                "bvid": bvid,
                "view_count": video.get("play", 0),
                "senddate": video.get("senddate")
            }
        )
    
    def _format_number(self, num: int) -> str:
        """格式化数字"""
        if num >= 10000:
            return f"{num / 10000:.1f}万"
        return str(num)


class BilibiliHotCollector(BilibiliCollector):
    """B站热门视频采集器（简化版）"""
    
    def __init__(self, name: str, config: Dict):
        config["collect_type"] = "popular"
        super().__init__(name, config)
