"""
财新网采集器
支持采集财新网 RSS 订阅内容
财新网是中文财经调查报道的标杆媒体
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class CaixinCollector(BaseCollector):
    """
    财新网采集器
    
    特点：
    - 深度调查报道
    - 付费内容质量高
    - 财经、政经、社会全覆盖
    
    采集方式：RSS 订阅
    注意：部分内容需要付费订阅才能阅读全文
    """
    
    # 财新网 RSS 订阅源
    RSS_FEEDS = {
        "首页": "https://www.caixin.com/search/rss.xml",
        "经济": "https://economy.caixin.com/rss.xml",
        "金融": "https://finance.caixin.com/rss.xml",
        "公司": "https://companies.caixin.com/rss.xml",
        "政经": "https://china.caixin.com/rss.xml",
        "世界": "https://international.caixin.com/rss.xml",
        "科技": "https://science.caixin.com/rss.xml",
        "文化": "https://culture.caixin.com/rss.xml",
    }
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_category = config.get("category", "首页")
        self.feed_url = config.get("url") or self.RSS_FEEDS.get(self.feed_category, self.RSS_FEEDS["首页"])
        self.limit = config.get("limit", 10)
        
        # 是否需要登录获取付费内容
        self.require_auth = config.get("require_auth", False)
        self.auth_cookie = config.get("auth_cookie")
    
    async def collect(self) -> CollectorResult:
        """采集财新网内容"""
        result = CollectorResult()
        
        try:
            import feedparser
            
            # 设置请求头
            headers = {}
            if self.auth_cookie:
                headers["Cookie"] = self.auth_cookie
            
            # 解析 RSS
            loop = __import__('asyncio').get_event_loop()
            feed = await loop.run_in_executor(None, lambda: feedparser.parse(self.feed_url))
            
            if feed.bozo:
                result.message = f"警告: RSS解析可能存在问题"
            
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
            result.message = f"成功采集 {len(result.items)} 条财新网内容"
            
        except Exception as e:
            result.success = False
            result.message = f"财新网采集失败: {str(e)}"
        
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
        
        # 清理 HTML
        if content:
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(strip=True)
        
        # 作者
        author = entry.get("author", "")
        if not author:
            author = entry.get("dc:creator", "财新网")
        
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
        
        # 是否为付费内容（根据内容长度或特定标记判断）
        is_premium = "财新通" in title or "付费" in content[:100]
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:500] + "..." if len(content) > 500 else content,
            author=author,
            publish_time=publish_time,
            keywords=tags,
            source=f"财新网-{self.feed_category}",
            extra={
                "category": self.feed_category,
                "is_premium": is_premium,
                "full_content_available": not is_premium or self.auth_cookie is not None
            }
        )


class CaixinPremiumCollector(CaixinCollector):
    """
    财新网付费内容采集器
    需要登录凭证才能获取完整内容
    """
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.require_auth = True
        if not config.get("auth_cookie"):
            raise ValueError("财新网付费内容采集需要提供 auth_cookie")
