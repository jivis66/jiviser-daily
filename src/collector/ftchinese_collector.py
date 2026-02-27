"""
FT中文网采集器
支持采集 Financial Times 中文版 RSS 内容
FT中文网提供国际视野+本土洞察的财经报道
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class FTChineseCollector(BaseCollector):
    """
    FT中文网采集器
    
    特点：
    - 国际视野+本土洞察
    - 深度分析报道
    - 双语内容（中英文对照）
    
    采集方式：RSS 订阅
    """
    
    # FT中文网 RSS 订阅源
    RSS_FEEDS = {
        "首页": "https://www.ftchinese.com/rss/feed",
        "今日焦点": "https://www.ftchinese.com/rss/news",
        "每日英语": "https://www.ftchinese.com/rss/diglossia",
        "专栏": "https://www.ftchinese.com/rss/column",
        "热点观察": "https://www.ftchinese.com/rss/hotstoryby7day",
        "生活时尚": "https://www.ftchinese.com/rss/lifestyle",
        "金融": "https://www.ftchinese.com/rss/markets",
        "商业": "https://www.ftchinese.com/rss/business",
        "管理": "https://www.ftchinese.com/rss/management",
        "经济": "https://www.ftchinese.com/rss/economy",
        "科技": "https://www.ftchinese.com/rss/technology",
        "政经": "https://www.ftchinese.com/rss/china",
        "教育": "https://www.ftchinese.com/rss/education",
        "高端视野": "https://www.ftchinese.com/rss/view",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_category = config.get("category", "首页")
        self.feed_url = config.get("url") or self.RSS_FEEDS.get(self.feed_category, self.RSS_FEEDS["首页"])
        self.limit = config.get("limit", 10)
        
        # 是否提取英文原文
        self.include_english = config.get("include_english", False)
    
    async def collect(self) -> CollectorResult:
        """采集 FT中文网内容"""
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
            result.message = f"成功采集 {len(result.items)} 条 FT中文网内容"
            
        except Exception as e:
            result.success = False
            result.message = f"FT中文网采集失败: {str(e)}"
        
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
        
        # 清理 HTML 并提取图片
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
            author = "FT中文网"
        
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
        tags.extend(["FT", "财经", self.feed_category])
        
        # 判断是否为双语内容
        is_bilingual = "每日英语" in self.feed_category or "双语" in title
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            keywords=list(set(tags)),  # 去重
            image_url=image_url,
            source=f"FT中文网-{self.feed_category}",
            extra={
                "category": self.feed_category,
                "is_bilingual": is_bilingual,
                "has_english_version": is_bilingual or self.include_english,
                "publisher": "Financial Times"
            }
        )


class FTChineseEnglishCollector(FTChineseCollector):
    """
    FT中文网双语内容采集器
    专注于采集带有英文原文对照的内容
    """
    
    def __init__(self, name: str, config: Dict):
        # 强制使用每日英语栏目
        config["category"] = "每日英语"
        super().__init__(name, config)
        self.include_english = True
