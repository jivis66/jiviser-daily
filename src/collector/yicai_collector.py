"""
第一财经采集器
支持采集第一财经 RSS 和 API 内容
第一财经是财经视频+图文深度结合的媒体平台
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class YicaiCollector(BaseCollector):
    """
    第一财经采集器
    
    特点：
    - 实时财经新闻
    - 深度分析报道
    - 视频+图文结合
    
    采集方式：RSS 订阅 + 网页解析
    """
    
    # 第一财经 RSS 订阅源
    RSS_FEEDS = {
        "最新": "https://www.yicai.com/rss/",
        "要闻": "https://www.yicai.com/rss/news.xml",
        "宏观": "https://www.yicai.com/rss/macro.xml",
        "股市": "https://www.yicai.com/rss/stock.xml",
        "金融": "https://www.yicai.com/rss/finance.xml",
        "公司": "https://www.yicai.com/rss/company.xml",
        "产业": "https://www.yicai.com/rss/industry.xml",
        "科技": "https://www.yicai.com/rss/tech.xml",
        "国际": "https://www.yicai.com/rss/global.xml",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_category = config.get("category", "最新")
        self.feed_url = config.get("url") or self.RSS_FEEDS.get(self.feed_category, self.RSS_FEEDS["最新"])
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集第一财经内容"""
        result = CollectorResult()
        
        try:
            import feedparser
            from bs4 import BeautifulSoup
            
            loop = __import__('asyncio').get_event_loop()
            feed = await loop.run_in_executor(None, lambda: feedparser.parse(self.feed_url))
            
            result.total_found = len(feed.entries)
            
            for entry in feed.entries[:self.limit]:
                try:
                    item = self._parse_entry(entry)
                    if self.should_include(item):
                        result.items.append(item)
                    else:
                        result.total_filtered += 1
                except Exception as e:
                    continue
            
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条第一财经内容"
            
        except Exception as e:
            result.success = False
            result.message = f"第一财经采集失败: {str(e)}"
        
        return result
    
    def _parse_entry(self, entry: Dict) -> ContentItem:
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
        
        # 提取图片
        image_url = None
        if content:
            soup = BeautifulSoup(content, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                image_url = img["src"]
            # 清理 HTML
            content = soup.get_text(strip=True)
        
        # 作者
        author = entry.get("author", "")
        if not author:
            author = "第一财经"
        
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
        
        # 判断是否为视频内容
        is_video = "video" in url.lower() or "视频" in title
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            keywords=tags,
            image_url=image_url,
            source=f"第一财经-{self.feed_category}",
            extra={
                "category": self.feed_category,
                "is_video": is_video,
                "media_type": "video" if is_video else "article"
            }
        )


class YicaiVideoCollector(BaseCollector):
    """
    第一财经视频内容采集器
    采集第一财经的视频节目
    """
    
    BASE_URL = "https://www.yicai.com"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.VIDEO, config)
        self.category = config.get("category", "最新")
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集第一财经视频"""
        result = CollectorResult()
        
        try:
            from bs4 import BeautifulSoup
            
            # 视频栏目页面
            video_urls = {
                "最新": f"{self.BASE_URL}/video/latest",
                "财经": f"{self.BASE_URL}/video/finance",
                "股市": f"{self.BASE_URL}/video/stock",
                "宏观": f"{self.BASE_URL}/video/macro",
            }
            
            url = video_urls.get(self.category, video_urls["最新"])
            response = await self.fetch_url(url)
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 解析视频列表
            video_items = soup.find_all("div", class_="video-item")
            result.total_found = len(video_items)
            
            for item in video_items[:self.limit]:
                try:
                    content_item = self._parse_video_item(item)
                    if content_item and self.should_include(content_item):
                        result.items.append(content_item)
                    else:
                        result.total_filtered += 1
                except Exception as e:
                    continue
            
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条第一财经视频"
            
        except Exception as e:
            result.success = False
            result.message = f"第一财经视频采集失败: {str(e)}"
        
        return result
    
    def _parse_video_item(self, item) -> Optional[ContentItem]:
        """解析视频条目"""
        from bs4 import BeautifulSoup
        
        # 标题和链接
        a_tag = item.find("a")
        if not a_tag:
            return None
        
        url = a_tag.get("href", "")
        if url.startswith("/"):
            url = f"{self.BASE_URL}{url}"
        
        title_tag = a_tag.find("img")
        title = title_tag.get("alt", "无标题") if title_tag else "无标题"
        
        # 封面图
        image_url = title_tag.get("src") if title_tag else None
        
        # 时长
        duration_tag = item.find("span", class_="duration")
        duration = duration_tag.get_text(strip=True) if duration_tag else ""
        
        return self.create_content_item(
            title=title,
            url=url,
            content=f"视频时长: {duration}",
            source=f"第一财经视频-{self.category}",
            image_url=image_url,
            extra={
                "category": self.category,
                "duration": duration,
                "is_video": True,
                "media_type": "video"
            }
        )
