"""
知乎采集器
支持采集知乎热榜、推荐回答、专栏文章等
知乎是专业问答社区，有大量深度长文
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class ZhihuCollector(BaseCollector):
    """
    知乎采集器
    
    特点：
    - 专业问答社区
    - 深度长文
    - 多领域覆盖
    
    采集方式：官方 API（部分）+ 网页解析
    注意：知乎 API 需要处理反爬
    """
    
    BASE_URL = "https://www.zhihu.com"
    API_URL = "https://www.zhihu.com/api/v4"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.SOCIAL, config)
        self.collect_type = config.get("collect_type", "hot")  # hot, recommend, search, column
        self.keyword = config.get("keyword")
        self.column_id = config.get("column_id")
        self.topic_id = config.get("topic_id")
        self.limit = config.get("limit", 10)
        
        # 知乎需要特殊的请求头
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.zhihu.com/",
            "x-requested-with": "fetch",
        }
        
        # 可选：登录 cookie
        self.cookie = config.get("cookie")
        if self.cookie:
            self._headers["Cookie"] = self.cookie
    
    async def collect(self) -> CollectorResult:
        """采集知乎内容"""
        result = CollectorResult()
        
        try:
            if self.collect_type == "hot":
                items = await self._collect_hot()
            elif self.collect_type == "recommend":
                items = await self._collect_recommend()
            elif self.collect_type == "search" and self.keyword:
                items = await self._collect_search()
            elif self.collect_type == "column" and self.column_id:
                items = await self._collect_column()
            elif self.collect_type == "topic" and self.topic_id:
                items = await self._collect_topic()
            else:
                result.success = False
                result.message = "配置错误：请提供有效的 collect_type 和对应参数"
                return result
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条知乎内容"
            
        except Exception as e:
            result.success = False
            result.message = f"知乎采集失败: {str(e)}"
        
        return result
    
    async def _collect_hot(self) -> List[ContentItem]:
        """采集知乎热榜"""
        url = f"{self.API_URL}/feed/topstory/hot-list-web"
        
        response = await self.fetch_url(url, headers=self._headers)
        data = response.json()
        
        items = []
        if data.get("data"):
            for item_data in data["data"][:self.limit]:
                item = self._parse_hot_item(item_data)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_recommend(self) -> List[ContentItem]:
        """采集推荐内容"""
        # 推荐内容需要登录
        if not self.cookie:
            return await self._collect_hot()  # 降级为热榜
        
        url = f"{self.API_URL}/feed/topstory/recommend"
        params = {
            "session_token": "",
            "desktop": "true",
            "page_number": 1,
            "limit": self.limit
        }
        
        response = await self.fetch_url(url, params=params, headers=self._headers)
        data = response.json()
        
        items = []
        if data.get("data"):
            for item_data in data["data"][:self.limit]:
                item = self._parse_feed_item(item_data)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_search(self) -> List[ContentItem]:
        """搜索内容"""
        url = f"{self.API_URL}/search_v3"
        params = {
            "q": self.keyword,
            "t": "general",
            "correction": 1,
            "offset": 0,
            "limit": self.limit,
        }
        
        response = await self.fetch_url(url, params=params, headers=self._headers)
        data = response.json()
        
        items = []
        if data.get("data"):
            for item_data in data["data"][:self.limit]:
                item = self._parse_search_item(item_data)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_column(self) -> List[ContentItem]:
        """采集专栏文章"""
        url = f"{self.API_URL}/columns/{self.column_id}/items"
        params = {
            "offset": 0,
            "limit": self.limit
        }
        
        response = await self.fetch_url(url, params=params, headers=self._headers)
        data = response.json()
        
        items = []
        if data.get("data"):
            for item_data in data["data"][:self.limit]:
                item = self._parse_article(item_data)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_topic(self) -> List[ContentItem]:
        """采集话题下的内容"""
        url = f"{self.API_URL}/topics/{self.topic_id}/feeds/essence"
        params = {
            "offset": 0,
            "limit": self.limit
        }
        
        response = await self.fetch_url(url, params=params, headers=self._headers)
        data = response.json()
        
        items = []
        if data.get("data"):
            for item_data in data["data"][:self.limit]:
                item = self._parse_feed_item(item_data)
                if item:
                    items.append(item)
        
        return items
    
    def _parse_hot_item(self, data: Dict) -> Optional[ContentItem]:
        """解析热榜条目"""
        target = data.get("target", {})
        if not target:
            return None
        
        title = target.get("title", "无标题")
        url = target.get("url", "")
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = f"{self.BASE_URL}{url}"
        
        # 问题ID
        question_id = target.get("id")
        if not url and question_id:
            url = f"{self.BASE_URL}/question/{question_id}"
        
        # 热度
        heat = data.get("detail_text", "")
        
        # 回答数
        answer_count = target.get("answer_count", 0)
        
        # 热度指数
        popularity = 0
        try:
            if "万" in heat:
                popularity = float(heat.replace("万热度", "")) * 10000
            else:
                popularity = float(heat.replace("热度", ""))
        except:
            pass
        
        content_parts = [
            f"热度: {heat}",
            f"回答数: {answer_count}",
        ]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            source="知乎热榜",
            popularity_score=float(popularity),
            keywords=["知乎", "热榜"],
            extra={
                "question_id": question_id,
                "heat": heat,
                "answer_count": answer_count,
                "is_hot": True,
                "platform": "zhihu"
            }
        )
    
    def _parse_feed_item(self, data: Dict) -> Optional[ContentItem]:
        """解析推荐流条目"""
        target = data.get("target", {})
        if not target:
            return None
        
        # 判断类型
        target_type = target.get("type", "")
        
        if "article" in target_type:
            return self._parse_article(target)
        elif "answer" in target_type:
            return self._parse_answer(target)
        elif "question" in target_type:
            return self._parse_question(target)
        
        return None
    
    def _parse_article(self, data: Dict) -> Optional[ContentItem]:
        """解析文章"""
        title = data.get("title", "无标题")
        url = data.get("url", "")
        if not url:
            article_id = data.get("id")
            if article_id:
                url = f"{self.BASE_URL}/p/{article_id}"
        
        # 内容摘要
        excerpt = data.get("excerpt", "")
        content = data.get("content", "")  # HTML 格式
        
        # 作者
        author = ""
        author_data = data.get("author", {})
        if author_data:
            author = author_data.get("name", "")
        
        # 发布时间
        publish_time = None
        created_time = data.get("created_time") or data.get("created")
        if created_time:
            try:
                publish_time = datetime.fromtimestamp(created_time)
            except:
                pass
        
        # 点赞数
        voteup_count = data.get("voteup_count", 0) or data.get("votes_count", 0)
        
        # 评论数
        comment_count = data.get("comment_count", 0)
        
        # 封面图
        image_url = None
        if data.get("image_url"):
            image_url = data["image_url"]
        elif data.get("thumbnail"):
            image_url = data["thumbnail"]
        
        content_parts = [
            f"作者: {author}",
            f"点赞: {voteup_count}",
            f"评论: {comment_count}",
            "",
            excerpt or (content[:200] + "..." if len(content) > 200 else content)
        ]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(filter(None, content_parts)),
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            popularity_score=float(voteup_count),
            keywords=["知乎", "文章"],
            extra={
                "article_id": data.get("id"),
                "voteup_count": voteup_count,
                "comment_count": comment_count,
                "is_article": True,
                "platform": "zhihu"
            }
        )
    
    def _parse_answer(self, data: Dict) -> Optional[ContentItem]:
        """解析回答"""
        question = data.get("question", {})
        question_title = question.get("title", "无标题问题")
        
        # 回答链接
        answer_id = data.get("id")
        question_id = question.get("id")
        url = f"{self.BASE_URL}/question/{question_id}/answer/{answer_id}" if question_id and answer_id else ""
        
        # 内容
        content = data.get("content", "")  # HTML
        excerpt = data.get("excerpt", "")
        
        # 作者
        author = ""
        author_data = data.get("author", {})
        if author_data:
            author = author_data.get("name", "")
        
        # 发布时间
        publish_time = None
        created_time = data.get("created_time")
        if created_time:
            try:
                publish_time = datetime.fromtimestamp(created_time)
            except:
                pass
        
        # 点赞数
        voteup_count = data.get("voteup_count", 0)
        
        # 评论数
        comment_count = data.get("comment_count", 0)
        
        content_parts = [
            f"问题: {question_title}",
            f"作者: {author}",
            f"点赞: {voteup_count}",
            f"评论: {comment_count}",
            "",
            excerpt or (content[:200] + "..." if len(content) > 200 else content)
        ]
        
        return self.create_content_item(
            title=f"回答: {question_title}",
            url=url,
            content="\n".join(filter(None, content_parts)),
            author=author,
            publish_time=publish_time,
            popularity_score=float(voteup_count),
            keywords=["知乎", "回答"],
            extra={
                "answer_id": answer_id,
                "question_id": question_id,
                "question_title": question_title,
                "voteup_count": voteup_count,
                "comment_count": comment_count,
                "is_answer": True,
                "platform": "zhihu"
            }
        )
    
    def _parse_question(self, data: Dict) -> Optional[ContentItem]:
        """解析问题"""
        title = data.get("title", "无标题")
        url = data.get("url", "")
        if not url:
            question_id = data.get("id")
            if question_id:
                url = f"{self.BASE_URL}/question/{question_id}"
        
        answer_count = data.get("answer_count", 0)
        follower_count = data.get("follower_count", 0)
        
        return self.create_content_item(
            title=title,
            url=url,
            content=f"回答数: {answer_count}\n关注者: {follower_count}",
            popularity_score=float(answer_count),
            keywords=["知乎", "问题"],
            extra={
                "question_id": data.get("id"),
                "answer_count": answer_count,
                "follower_count": follower_count,
                "is_question": True,
                "platform": "zhihu"
            }
        )
    
    def _parse_search_item(self, data: Dict) -> Optional[ContentItem]:
        """解析搜索结果"""
        object_data = data.get("object", {})
        if not object_data:
            return None
        
        object_type = object_data.get("type", "")
        
        if "article" in object_type:
            return self._parse_article(object_data)
        elif "answer" in object_type:
            return self._parse_answer(object_data)
        elif "question" in object_type:
            return self._parse_question(object_data)
        
        return None


class ZhihuHotCollector(ZhihuCollector):
    """
    知乎热榜采集器（简化版）
    """
    
    def __init__(self, name: str, config: Dict):
        config["collect_type"] = "hot"
        super().__init__(name, config)
