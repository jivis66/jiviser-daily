"""
界面新闻采集器
支持采集界面新闻 RSS 和网页内容
界面新闻以商业人物报道出色著称
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class JiemianCollector(BaseCollector):
    """
    界面新闻采集器
    
    特点：
    - 商业人物报道出色
    - 原创财经新闻
    - 深度调查报道
    
    采集方式：RSS 订阅
    """
    
    # 界面新闻 RSS 订阅源
    RSS_FEEDS = {
        "首页": "https://www.jiemian.com/rss.xml",
        "科技": "https://www.jiemian.com/rss/tech.xml",
        "财经": "https://www.jiemian.com/rss/finance.xml",
        "商业": "https://www.jiemian.com/rss/business.xml",
        "消费": "https://www.jiemian.com/rss/consumption.xml",
        "工业": "https://www.jiemian.com/rss/industry.xml",
        "汽车": "https://www.jiemian.com/rss/car.xml",
        "地产": "https://www.jiemian.com/rss/estate.xml",
        "金融": "https://www.jiemian.com/rss/financial.xml",
        "投资": "https://www.jiemian.com/rss/investment.xml",
        "股市": "https://www.jiemian.com/rss/stock.xml",
        "宏观": "https://www.jiemian.com/rss/macro.xml",
        "金融圈": "https://www.jiemian.com/rss/financialpeople.xml",
        "天下": "https://www.jiemian.com/rss/world.xml",
        "天下新闻": "https://www.jiemian.com/rss/worldnews.xml",
        "正午": "https://www.jiemian.com/rss/noon.xml",
        "医药": "https://www.jiemian.com/rss/medical.xml",
        "传媒": "https://www.jiemian.com/rss/media.xml",
        "城市": "https://www.jiemian.com/rss/city.xml",
        "文化": "https://www.jiemian.com/rss/culture.xml",
        "旅行": "https://www.jiemian.com/rss/travel.xml",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_category = config.get("category", "首页")
        self.feed_url = config.get("url") or self.RSS_FEEDS.get(self.feed_category, self.RSS_FEEDS["首页"])
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集界面新闻内容"""
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
            result.message = f"成功采集 {len(result.items)} 条界面新闻内容"
            
        except Exception as e:
            result.success = False
            result.message = f"界面新闻采集失败: {str(e)}"
        
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
            author = entry.get("dc:creator", "界面新闻")
        
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
        
        # 判断是否为人物报道
        is_profile = any(keyword in title for keyword in ["人物", "专访", "对话", "老板", "创始人", "CEO"])
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            keywords=tags,
            image_url=image_url,
            source=f"界面新闻-{self.feed_category}",
            extra={
                "category": self.feed_category,
                "is_profile": is_profile,
                "content_type": "profile" if is_profile else "news"
            }
        )


class JiemianProfileCollector(JiemianCollector):
    """
    界面新闻人物报道专集采集器
    专注于采集商业人物、企业家专访等内容
    """
    
    def __init__(self, name: str, config: Dict):
        # 强制使用商业或金融圈栏目
        config["category"] = config.get("category", "商业")
        super().__init__(name, config)
        
        # 关键词过滤，只保留人物相关
        if "filter" not in config:
            config["filter"] = {}
        config["filter"]["keywords"] = config["filter"].get("keywords", []) + [
            "人物", "专访", "对话", "老板", "创始人", "CEO", "董事长", "总裁"
        ]
