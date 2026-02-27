"""
抖音采集器
支持采集抖音热门视频、搜索内容
抖音是泛知识内容占比20%的短视频平台，拥有1.5亿知识创作者
"""
from datetime import datetime
from typing import Dict, List, Optional
import json
import re

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class DouyinCollector(BaseCollector):
    """
    抖音采集器
    
    特点：
    - 泛知识内容占比20%
    - 1.5亿知识创作者
    - 短视频为主，也有中视频
    
    采集方式：网页版 API（需处理反爬）
    注意：抖音反爬严格，建议使用 Playwright 或无头浏览器
    """
    
    BASE_URL = "https://www.douyin.com"
    API_URL = "https://www.douyin.com/aweme/v1/web"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.VIDEO, config)
        self.keyword = config.get("keyword")  # 搜索关键词
        self.user_id = config.get("user_id")  # 用户ID
        self.category = config.get("category", "hot")  # hot, search, user
        self.limit = config.get("limit", 10)
        
        # 反爬处理
        self.use_playwright = config.get("use_playwright", False)
        self.ms_token = config.get("ms_token")  # 抖音的验证 token
        
        # 自定义请求头
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        
        if self.ms_token:
            self._headers["Cookie"] = f"msToken={self.ms_token}"
    
    async def collect(self) -> CollectorResult:
        """采集抖音内容"""
        result = CollectorResult()
        
        try:
            if self.category == "search" and self.keyword:
                items = await self._collect_search()
            elif self.category == "user" and self.user_id:
                items = await self._collect_by_user()
            elif self.category == "hot":
                items = await self._collect_hot()
            else:
                result.success = False
                result.message = "配置错误：请提供有效的 category 和对应参数"
                return result
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条抖音内容"
            
        except Exception as e:
            result.success = False
            result.message = f"抖音采集失败: {str(e)}"
        
        return result
    
    async def _collect_search(self) -> List[ContentItem]:
        """搜索视频"""
        url = f"{self.API_URL}/search/item/"
        params = {
            "keyword": self.keyword,
            "search_source": "normal_search",
            "query_correct_type": 1,
            "is_filter_search": 0,
            "offset": 0,
            "count": self.limit,
        }
        
        if self.ms_token:
            params["msToken"] = self.ms_token
        
        response = await self.fetch_url(url, params=params, headers=self._headers)
        data = response.json()
        
        items = []
        if data.get("status_code") == 0 and data.get("data"):
            for item_data in data["data"][:self.limit]:
                item = self._parse_video(item_data)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_by_user(self) -> List[ContentItem]:
        """采集指定用户视频"""
        url = f"{self.API_URL}/aweme/post/"
        params = {
            "sec_user_id": self.user_id,
            "max_cursor": 0,
            "count": self.limit,
        }
        
        if self.ms_token:
            params["msToken"] = self.ms_token
        
        response = await self.fetch_url(url, params=params, headers=self._headers)
        data = response.json()
        
        items = []
        if data.get("status_code") == 0 and data.get("aweme_list"):
            for item_data in data["aweme_list"][:self.limit]:
                item = self._parse_video(item_data)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_hot(self) -> List[ContentItem]:
        """采集热门视频（从网页版解析）"""
        # 热门页面
        url = f"{self.BASE_URL}/hot"
        
        response = await self.fetch_url(url, headers=self._headers)
        html = response.text
        
        # 从 HTML 中提取渲染数据
        return self._parse_from_html(html)
    
    def _parse_video(self, data: Dict) -> Optional[ContentItem]:
        """解析视频数据"""
        aweme_id = data.get("aweme_id")
        if not aweme_id:
            return None
        
        # 标题/描述
        title = data.get("desc", "")
        if not title:
            title = "无标题视频"
        
        # 链接
        url = f"https://www.douyin.com/video/{aweme_id}"
        
        # 作者信息
        author = ""
        author_data = data.get("author", {})
        if author_data:
            author = author_data.get("nickname", "")
        
        # 统计数据
        stats = data.get("statistics", {})
        digg_count = stats.get("digg_count", 0)  # 点赞
        comment_count = stats.get("comment_count", 0)  # 评论
        share_count = stats.get("share_count", 0)  # 分享
        view_count = stats.get("play_count", 0)  # 播放
        
        # 发布时间
        publish_time = None
        create_time = data.get("create_time")
        if create_time:
            try:
                publish_time = datetime.fromtimestamp(create_time)
            except:
                pass
        
        # 封面图
        image_url = None
        video_data = data.get("video", {})
        if video_data:
            cover = video_data.get("cover", {})
            image_url = cover.get("url_list", [None])[0] if cover else None
            if not image_url:
                dynamic_cover = video_data.get("dynamic_cover", {})
                image_url = dynamic_cover.get("url_list", [None])[0] if dynamic_cover else None
        
        # 标签/话题
        keywords = []
        text_extra = data.get("text_extra", [])
        for extra in text_extra:
            if extra.get("hashtag_name"):
                keywords.append(extra["hashtag_name"])
        
        # 时长
        duration = video_data.get("duration", 0) // 1000  # 毫秒转秒
        
        # 内容类型判断
        content_type = self._classify_content(keywords, title)
        
        content_parts = [
            f"作者: @{author}",
            f"点赞: {self._format_number(digg_count)}",
            f"评论: {self._format_number(comment_count)}",
            f"分享: {self._format_number(share_count)}",
            f"时长: {duration}秒" if duration > 0 else "",
            "",
            f"话题: {' '.join(['#' + k for k in keywords[:5]])}" if keywords else ""
        ]
        
        return self.create_content_item(
            title=title[:100] + "..." if len(title) > 100 else title,
            url=url,
            content="\n".join(filter(None, content_parts)),
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            keywords=keywords + [content_type],
            popularity_score=float(digg_count),
            extra={
                "video_id": aweme_id,
                "author_id": author_data.get("sec_uid", ""),
                "author_unique_id": author_data.get("unique_id", ""),
                "duration": duration,
                "digg_count": digg_count,
                "comment_count": comment_count,
                "share_count": share_count,
                "view_count": view_count,
                "is_video": True,
                "content_type": content_type,
                "platform": "douyin"
            }
        )
    
    def _parse_from_html(self, html: str) -> List[ContentItem]:
        """从 HTML 解析视频列表"""
        from bs4 import BeautifulSoup
        
        items = []
        
        # 尝试从 SSR 数据中提取
        pattern = r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.+?})</script>'
        match = re.search(pattern, html)
        
        if match:
            try:
                data = json.loads(match.group(1))
                # 遍历数据结构查找视频
                videos = self._extract_videos_from_ssr(data)
                for video_data in videos[:self.limit]:
                    item = self._parse_video(video_data)
                    if item:
                        items.append(item)
            except Exception as e:
                print(f"[Douyin] 解析 SSR 数据失败: {e}")
        
        return items
    
    def _extract_videos_from_ssr(self, data: Dict) -> List[Dict]:
        """从 SSR 数据中提取视频列表"""
        videos = []
        
        def find_videos(obj):
            if isinstance(obj, dict):
                if "aweme_id" in obj and "desc" in obj:
                    videos.append(obj)
                for v in obj.values():
                    find_videos(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_videos(item)
        
        find_videos(data)
        return videos
    
    def _classify_content(self, keywords: List[str], title: str) -> str:
        """根据关键词和标题分类内容类型"""
        text = " ".join(keywords) + " " + title
        text = text.lower()
        
        knowledge_keywords = ["知识", "科普", "教程", "学习", "教育", "干货", "技巧", "方法"]
        if any(kw in text for kw in knowledge_keywords):
            return "知识"
        
        business_keywords = ["商业", "财经", "投资", "创业", "职场", "管理", "营销"]
        if any(kw in text for kw in business_keywords):
            return "商业"
        
        tech_keywords = ["科技", "数码", "AI", "人工智能", "互联网", "编程", "软件"]
        if any(kw in text for kw in tech_keywords):
            return "科技"
        
        life_keywords = ["生活", "美食", "旅行", "家居", "健康", "时尚"]
        if any(kw in text for kw in life_keywords):
            return "生活"
        
        return "其他"
    
    def _format_number(self, num: int) -> str:
        """格式化数字"""
        if num >= 100000000:
            return f"{num / 100000000:.1f}亿"
        elif num >= 10000:
            return f"{num / 10000:.1f}万"
        return str(num)


class DouyinKnowledgeCollector(DouyinCollector):
    """
    抖音知识内容专集采集器
    专注于采集知识类、教育类内容
    """
    
    KNOWLEDGE_KEYWORDS = [
        "知识", "科普", "干货", "教程", "学习", "教育",
        "财经", "商业", "职场", "科技", "历史", "文化"
    ]
    
    def __init__(self, name: str, config: Dict):
        # 如果没有指定关键词，使用知识关键词
        if not config.get("keyword"):
            config["keyword"] = "知识科普"
        super().__init__(name, config)
        
        # 设置内容类型过滤
        if "filter" not in config:
            config["filter"] = {}
        config["filter"]["keywords"] = config["filter"].get("keywords", []) + self.KNOWLEDGE_KEYWORDS
