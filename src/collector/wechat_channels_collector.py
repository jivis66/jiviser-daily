"""
微信视频号采集器
支持采集视频号内容
视频号在微信生态中，社交推荐+直播知识内容

注意：视频号采集难度很高，因为：
1. 完全在微信生态内，没有公开的网页版
2. 需要登录微信账号
3. 反爬机制严格

建议通过以下方式获取视频号内容：
1. 关注视频号后通过微信公众号 RSS 获取
2. 使用第三方服务
3. 手动配置 RSS 源
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class WechatChannelsCollector(BaseCollector):
    """
    微信视频号采集器（基础框架）
    
    特点：
    - 微信生态，社交推荐
    - 直播知识内容
    - 反爬极其严格
    
    采集方式：
    - 目前主要依赖用户提供的 RSS 源
    - 或使用第三方服务
    
    建议配置：
    - 通过公众号文章间接获取视频号内容
    - 或使用视频号助手 API（需企业资质）
    """
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.VIDEO, config)
        
        # 视频号ID（微信号）
        self.channel_id = config.get("channel_id")
        
        # 替代方案：使用 RSS 源
        self.feed_url = config.get("feed_url")
        
        # 或使用第三方服务
        self.third_party_service = config.get("third_party_service")
        
        self.limit = config.get("limit", 10)
        
        if not any([self.channel_id, self.feed_url, self.third_party_service]):
            raise ValueError("视频号采集器需要提供 channel_id、feed_url 或 third_party_service")
    
    async def collect(self) -> CollectorResult:
        """采集视频号内容"""
        result = CollectorResult()
        
        try:
            if self.feed_url:
                items = await self._collect_from_rss()
            elif self.third_party_service:
                items = await self._collect_from_third_party()
            else:
                items = await self._collect_direct()
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条视频号内容"
            
        except Exception as e:
            result.success = False
            result.message = f"视频号采集失败: {str(e)}"
        
        return result
    
    async def _collect_from_rss(self) -> List[ContentItem]:
        """从 RSS 源采集"""
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
        author = entry.get("author", "视频号")
        
        # 发布时间
        publish_time = None
        if "published_parsed" in entry:
            try:
                parsed = entry["published_parsed"]
                publish_time = datetime(*parsed[:6])
            except:
                pass
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content[:300] + "..." if len(content) > 300 else content,
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            source="视频号",
            keywords=["视频号", "微信"],
            extra={
                "channel_id": self.channel_id,
                "is_video": True,
                "platform": "wechat_channels"
            }
        )
    
    async def _collect_from_third_party(self) -> List[ContentItem]:
        """从第三方服务采集"""
        # 这里可以集成第三方视频号数据服务
        # 例如某些提供视频号 RSS 的服务
        
        items = []
        
        # 示例：调用第三方 API
        # response = await self.fetch_url(self.third_party_service)
        # data = response.json()
        # ...
        
        return items
    
    async def _collect_direct(self) -> List[ContentItem]:
        """直接采集（需要特殊处理）"""
        # 视频号没有公开的网页版
        # 需要使用 Playwright 模拟微信环境
        # 或使用微信开放平台的 API（需企业资质）
        
        items = []
        
        # 如果配置了 Playwright，可以尝试
        # 但成功率不高，且容易被封
        
        return items


class WechatChannelsRSSCollector(WechatChannelsCollector):
    """
    视频号 RSS 采集器
    通过配置的 RSS 源采集视频号内容
    
    使用示例：
    - 某些第三方服务可以将视频号转换为 RSS
    - 用户手动维护的 RSS 源
    """
    
    def __init__(self, name: str, config: Dict):
        if not config.get("feed_url"):
            raise ValueError("必须配置 feed_url")
        super().__init__(name, config)
