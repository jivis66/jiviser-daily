"""
国际新闻媒体采集器
支持采集 Bloomberg、Reuters、The Economist、The New York Times 等国际主流媒体
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class BloombergCollector(BaseCollector):
    """
    Bloomberg 采集器
    
    特点：
    - 金融从业者标配
    - 全球财经新闻领先
    - 部分内容需要订阅
    
    采集方式：RSS + API
    RSS 是免费的，但有限制；API 需要付费订阅
    """
    
    RSS_FEEDS = {
        "top": "https://feeds.bloomberg.com/news.rss",
        "markets": "https://feeds.bloomberg.com/markets/news.rss",
        "technology": "https://feeds.bloomberg.com/technology/news.rss",
        "politics": "https://feeds.bloomberg.com/politics/news.rss",
        "economy": "https://feeds.bloomberg.com/economy/news.rss",
        "business": "https://feeds.bloomberg.com/business/news.rss",
        "opinion": "https://feeds.bloomberg.com/opinion/news.rss",
        "green": "https://feeds.bloomberg.com/green/news.rss",
        "crypto": "https://feeds.bloomberg.com/crypto/news.rss",
        "wealth": "https://feeds.bloomberg.com/wealth/news.rss",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_category = config.get("category", "top")
        self.feed_url = config.get("url") or self.RSS_FEEDS.get(self.feed_category, self.RSS_FEEDS["top"])
        self.limit = config.get("limit", 10)
        
        # API 配置（可选，用于获取更完整内容）
        self.api_key = config.get("api_key")
    
    async def collect(self) -> CollectorResult:
        """采集 Bloomberg 内容"""
        result = CollectorResult()
        
        try:
            if self.api_key:
                items = await self._collect_via_api()
            else:
                items = await self._collect_via_rss()
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条 Bloomberg 内容"
            
        except Exception as e:
            result.success = False
            result.message = f"Bloomberg 采集失败: {str(e)}"
        
        return result
    
    async def _collect_via_rss(self) -> List[ContentItem]:
        """通过 RSS 采集"""
        import feedparser
        from bs4 import BeautifulSoup
        
        items = []
        
        loop = __import__('asyncio').get_event_loop()
        feed = await loop.run_in_executor(None, lambda: feedparser.parse(self.feed_url))
        
        for entry in feed.entries[:self.limit]:
            try:
                item = self._parse_rss_entry(entry)
                if item:
                    items.append(item)
            except Exception as e:
                continue
        
        return items
    
    async def _collect_via_api(self) -> List[ContentItem]:
        """通过 API 采集（需要 API Key）"""
        # Bloomberg API 需要付费订阅
        # 这里提供框架，实际实现需要参考 Bloomberg API 文档
        
        url = "https://api.bloomberg.com/v1/news"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        response = await self.fetch_url(url, headers=headers)
        data = response.json()
        
        items = []
        # 解析 API 响应...
        
        return items
    
    def _parse_rss_entry(self, entry: Dict) -> Optional[ContentItem]:
        """解析 RSS 条目"""
        from bs4 import BeautifulSoup
        
        title = entry.get("title", "无标题")
        url = entry.get("link", "")
        
        # 提取内容
        content = ""
        if "content" in entry and entry["content"]:
            content = entry["content"][0].get("value", "")
        elif "description" in entry:
            content = entry["description"]
        elif "summary" in entry:
            content = entry["summary"]
        
        # 清理 HTML
        image_url = None
        if content:
            soup = BeautifulSoup(content, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                image_url = img["src"]
            content = soup.get_text(strip=True)
        
        # 作者
        author = entry.get("author", "")
        if not author:
            author = "Bloomberg"
        
        # 发布时间
        publish_time = None
        if "published_parsed" in entry:
            try:
                parsed = entry["published_parsed"]
                publish_time = datetime(*parsed[:6])
            except:
                pass
        
        # 标签
        tags = []
        if "tags" in entry:
            tags = [tag.get("term", "") for tag in entry["tags"]]
        tags.append(self.feed_category)
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            source=f"Bloomberg-{self.feed_category}",
            keywords=list(set(tags)),
            extra={
                "category": self.feed_category,
                "publisher": "Bloomberg L.P.",
                "is_premium": "subscribe" in content.lower(),
                "platform": "bloomberg"
            }
        )


class ReutersCollector(BaseCollector):
    """
    Reuters 路透社采集器
    
    特点：
    - 全球新闻网络最广
    - 中立客观的新闻报道
    - 免费 RSS 订阅
    
    采集方式：RSS
    """
    
    RSS_FEEDS = {
        "top": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
        "business": "https://www.reutersagency.com/feed/?taxonomy=business-summit&post_type=reuters-best",
        "markets": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
        "world": "https://www.reutersagency.com/feed/?taxonomy=world&post_type=reuters-best",
        "politics": "https://www.reutersagency.com/feed/?taxonomy=politics&post_type=reuters-best",
        "tech": "https://www.reutersagency.com/feed/?taxonomy=technology&post_type=reuters-best",
        "sustainability": "https://www.reutersagency.com/feed/?taxonomy=sustainability&post_type=reuters-best",
    }
    
    # 备用 RSS 源
    RSS_FEEDS_ALT = {
        "top": "https://www.reuters.com/rssFeed/worldNews",
        "business": "https://www.reuters.com/rssFeed/businessNews",
        "markets": "https://www.reuters.com/rssFeed/marketsNews",
        "tech": "https://www.reuters.com/rssFeed/technologyNews",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_category = config.get("category", "top")
        self.feed_url = config.get("url") or self.RSS_FEEDS.get(
            self.feed_category, self.RSS_FEEDS["top"]
        )
        self.use_alt_feed = config.get("use_alt_feed", False)
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集 Reuters 内容"""
        result = CollectorResult()
        
        try:
            items = await self._collect_via_rss()
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条 Reuters 内容"
            
        except Exception as e:
            result.success = False
            result.message = f"Reuters 采集失败: {str(e)}"
        
        return result
    
    async def _collect_via_rss(self) -> List[ContentItem]:
        """通过 RSS 采集"""
        import feedparser
        from bs4 import BeautifulSoup
        
        items = []
        
        feed_url = self.feed_url
        if self.use_alt_feed and self.feed_category in self.RSS_FEEDS_ALT:
            feed_url = self.RSS_FEEDS_ALT[self.feed_category]
        
        loop = __import__('asyncio').get_event_loop()
        feed = await loop.run_in_executor(None, lambda: feedparser.parse(feed_url))
        
        for entry in feed.entries[:self.limit]:
            try:
                item = self._parse_rss_entry(entry)
                if item:
                    items.append(item)
            except Exception as e:
                continue
        
        return items
    
    def _parse_rss_entry(self, entry: Dict) -> Optional[ContentItem]:
        """解析 RSS 条目"""
        from bs4 import BeautifulSoup
        
        title = entry.get("title", "无标题")
        url = entry.get("link", "")
        
        # 提取内容
        content = ""
        if "content" in entry and entry["content"]:
            content = entry["content"][0].get("value", "")
        elif "description" in entry:
            content = entry["description"]
        elif "summary" in entry:
            content = entry["summary"]
        
        # 清理 HTML
        image_url = None
        if content:
            soup = BeautifulSoup(content, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                image_url = img["src"]
            content = soup.get_text(strip=True)
        
        # 作者
        author = entry.get("author", "")
        if not author:
            author = "Reuters"
        
        # 发布时间
        publish_time = None
        if "published_parsed" in entry:
            try:
                parsed = entry["published_parsed"]
                publish_time = datetime(*parsed[:6])
            except:
                pass
        
        # 标签
        tags = []
        if "tags" in entry:
            tags = [tag.get("term", "") for tag in entry["tags"]]
        tags.append(self.feed_category)
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            source=f"Reuters-{self.feed_category}",
            keywords=list(set(tags)),
            extra={
                "category": self.feed_category,
                "publisher": "Thomson Reuters",
                "platform": "reuters"
            }
        )


class EconomistCollector(BaseCollector):
    """
    The Economist 经济学人采集器
    
    特点：
    - 深度分析+独特观点
    - 英国视角的国际新闻
    - 部分内容需要订阅
    
    采集方式：RSS（摘要）
    注意：全文需要订阅，RSS 只提供摘要
    """
    
    RSS_FEEDS = {
        "top": "https://www.economist.com/rss/leaders_rss.xml",
        "leaders": "https://www.economist.com/rss/leaders_rss.xml",
        "briefing": "https://www.economist.com/rss/briefing_rss.xml",
        "business": "https://www.economist.com/rss/business_rss.xml",
        "finance": "https://www.economist.com/rss/finance-and-economics_rss.xml",
        "science": "https://www.economist.com/rss/science-and-technology_rss.xml",
        "international": "https://www.economist.com/rss/international_rss.xml",
        "britain": "https://www.economist.com/rss/britain_rss.xml",
        "europe": "https://www.economist.com/rss/europe_rss.xml",
        "americas": "https://www.economist.com/rss/americas_rss.xml",
        "asia": "https://www.economist.com/rss/asia_rss.xml",
        "china": "https://www.economist.com/rss/china_rss.xml",
        "obituary": "https://www.economist.com/rss/obituary_rss.xml",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_category = config.get("category", "top")
        self.feed_url = config.get("url") or self.RSS_FEEDS.get(
            self.feed_category, self.RSS_FEEDS["top"]
        )
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集 The Economist 内容"""
        result = CollectorResult()
        
        try:
            items = await self._collect_via_rss()
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条 The Economist 内容"
            
        except Exception as e:
            result.success = False
            result.message = f"The Economist 采集失败: {str(e)}"
        
        return result
    
    async def _collect_via_rss(self) -> List[ContentItem]:
        """通过 RSS 采集"""
        import feedparser
        from bs4 import BeautifulSoup
        
        items = []
        
        loop = __import__('asyncio').get_event_loop()
        feed = await loop.run_in_executor(None, lambda: feedparser.parse(self.feed_url))
        
        for entry in feed.entries[:self.limit]:
            try:
                item = self._parse_rss_entry(entry)
                if item:
                    items.append(item)
            except Exception as e:
                continue
        
        return items
    
    def _parse_rss_entry(self, entry: Dict) -> Optional[ContentItem]:
        """解析 RSS 条目"""
        from bs4 import BeautifulSoup
        
        title = entry.get("title", "无标题")
        url = entry.get("link", "")
        
        # 提取内容（通常是摘要）
        content = ""
        if "content" in entry and entry["content"]:
            content = entry["content"][0].get("value", "")
        elif "description" in entry:
            content = entry["description"]
        elif "summary" in entry:
            content = entry["summary"]
        
        # 清理 HTML
        image_url = None
        if content:
            soup = BeautifulSoup(content, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                image_url = img["src"]
            content = soup.get_text(strip=True)
        
        # 作者
        author = entry.get("author", "")
        if not author:
            author = "The Economist"
        
        # 发布时间
        publish_time = None
        if "published_parsed" in entry:
            try:
                parsed = entry["published_parsed"]
                publish_time = datetime(*parsed[:6])
            except:
                pass
        
        # 标签
        tags = []
        if "tags" in entry:
            tags = [tag.get("term", "") for tag in entry["tags"]]
        tags.extend([self.feed_category, "Economist"])
        
        # 判断是否为免费内容
        is_free = "free" in url or "free" in content.lower()
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            source=f"The Economist-{self.feed_category}",
            keywords=list(set(tags)),
            extra={
                "category": self.feed_category,
                "publisher": "The Economist Group",
                "is_free": is_free,
                "is_premium": not is_free,
                "platform": "economist"
            }
        )


class NYTCollector(BaseCollector):
    """
    The New York Times 纽约时报采集器
    
    特点：
    - 调查报道标杆
    - 普利策奖常客
    - 需要 API Key 获取内容
    
    采集方式：API（需要 Key）
    RSS 只提供摘要
    """
    
    API_BASE = "https://api.nytimes.com/svc"
    RSS_FEEDS = {
        "home": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "world": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "us": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
        "business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "science": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
        "health": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "sports": "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
        "arts": "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml",
        "opinion": "https://rss.nytimes.com/services/xml/rss/nyt/Opinion.xml",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.API, config)
        self.feed_category = config.get("category", "home")
        self.api_key = config.get("api_key")
        self.limit = config.get("limit", 10)
        
        # 如果没有 API Key，使用 RSS
        self.use_rss = config.get("use_rss", not bool(self.api_key))
        
        if self.use_rss:
            self.feed_url = config.get("url") or self.RSS_FEEDS.get(
                self.feed_category, self.RSS_FEEDS["home"]
            )
    
    async def collect(self) -> CollectorResult:
        """采集 NYT 内容"""
        result = CollectorResult()
        
        try:
            if self.use_rss or not self.api_key:
                items = await self._collect_via_rss()
            else:
                items = await self._collect_via_api()
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条 NYT 内容"
            
        except Exception as e:
            result.success = False
            result.message = f"NYT 采集失败: {str(e)}"
        
        return result
    
    async def _collect_via_rss(self) -> List[ContentItem]:
        """通过 RSS 采集"""
        import feedparser
        from bs4 import BeautifulSoup
        
        items = []
        
        loop = __import__('asyncio').get_event_loop()
        feed = await loop.run_in_executor(None, lambda: feedparser.parse(self.feed_url))
        
        for entry in feed.entries[:self.limit]:
            try:
                item = self._parse_rss_entry(entry)
                if item:
                    items.append(item)
            except Exception as e:
                continue
        
        return items
    
    async def _collect_via_api(self) -> List[ContentItem]:
        """通过 API 采集"""
        # NYT Article Search API
        url = f"{self.API_BASE}/search/v2/articlesearch.json"
        params = {
            "api-key": self.api_key,
            "fq": f"section:{self.feed_category}" if self.feed_category != "home" else "",
            "sort": "newest",
            "page": 0,
        }
        
        response = await self.fetch_url(url, params=params)
        data = response.json()
        
        items = []
        if data.get("response", {}).get("docs"):
            for doc in data["response"]["docs"][:self.limit]:
                item = self._parse_api_doc(doc)
                if item:
                    items.append(item)
        
        return items
    
    def _parse_rss_entry(self, entry: Dict) -> Optional[ContentItem]:
        """解析 RSS 条目"""
        from bs4 import BeautifulSoup
        
        title = entry.get("title", "无标题")
        url = entry.get("link", "")
        
        # 提取内容
        content = ""
        if "content" in entry and entry["content"]:
            content = entry["content"][0].get("value", "")
        elif "description" in entry:
            content = entry["description"]
        elif "summary" in entry:
            content = entry["summary"]
        
        # 清理 HTML
        image_url = None
        if content:
            soup = BeautifulSoup(content, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                image_url = img["src"]
            content = soup.get_text(strip=True)
        
        # 作者
        author = entry.get("author", "")
        if not author:
            author = entry.get("dc:creator", "The New York Times")
        
        # 发布时间
        publish_time = None
        if "published_parsed" in entry:
            try:
                parsed = entry["published_parsed"]
                publish_time = datetime(*parsed[:6])
            except:
                pass
        
        # 标签
        tags = []
        if "tags" in entry:
            tags = [tag.get("term", "") for tag in entry["tags"]]
        tags.append(self.feed_category)
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            source=f"NYT-{self.feed_category}",
            keywords=list(set(tags)),
            extra={
                "category": self.feed_category,
                "publisher": "The New York Times Company",
                "platform": "nytimes"
            }
        )
    
    def _parse_api_doc(self, doc: Dict) -> Optional[ContentItem]:
        """解析 API 文档"""
        headline = doc.get("headline", {})
        title = headline.get("main", "无标题")
        
        url = doc.get("web_url", "")
        
        # 摘要
        abstract = doc.get("abstract", "")
        lead_paragraph = doc.get("lead_paragraph", "")
        content = abstract or lead_paragraph
        
        # 作者
        byline = doc.get("byline", {})
        author = byline.get("original", "The New York Times")
        
        # 发布时间
        publish_time = None
        pub_date = doc.get("pub_date")
        if pub_date:
            try:
                publish_time = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except:
                pass
        
        # 图片
        image_url = None
        multimedia = doc.get("multimedia", [])
        if multimedia and len(multimedia) > 0:
            image_url = f"https://www.nytimes.com/{multimedia[0].get('url', '')}"
        
        # 标签
        keywords = [kw.get("value", "") for kw in doc.get("keywords", [])]
        keywords.append(self.feed_category)
        
        # 版块
        section = doc.get("section_name", "")
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            source=f"NYT-{section or self.feed_category}",
            keywords=list(set(keywords)),
            extra={
                "category": section or self.feed_category,
                "document_id": doc.get("_id"),
                "news_desk": doc.get("news_desk"),
                "word_count": doc.get("word_count"),
                "platform": "nytimes"
            }
        )
