"""
中国商业科技媒体采集器
支持虎嗅、雷锋网、品玩、极客公园等
"""
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class HuxiuCollector(BaseCollector):
    """虎嗅 - 商业科技媒体"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_type = config.get("feed_type", "all")

    async def collect(self) -> CollectorResult:
        """采集虎嗅 RSS"""
        result = CollectorResult()

        try:
            # 虎嗅 RSS 源
            rss_url = "https://www.huxiu.com/rss/0.xml"

            import feedparser
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_url)

            result.total_found = len(feed.entries)

            for entry in feed.entries:
                try:
                    title = entry.get("title", "")
                    url = entry.get("link", "")
                    content = entry.get("summary", "")[:500]

                    # 发布时间
                    publish_time = None
                    if "published_parsed" in entry:
                        try:
                            parsed = entry["published_parsed"]
                            publish_time = datetime(*parsed[:6])
                        except:
                            pass

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=entry.get("author", ""),
                        publish_time=publish_time,
                        extra={"source": "huxiu", "type": "business"}
                    )

                    if self.should_include(content_item):
                        result.items.append(content_item)
                    else:
                        result.total_filtered += 1

                except Exception as e:
                    continue

            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"

        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"

        return result


class LeiphoneCollector(BaseCollector):
    """雷锋网 - AI 和科技"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.category = config.get("category", "ai")

    async def collect(self) -> CollectorResult:
        """采集雷锋网 RSS"""
        result = CollectorResult()

        # 雷锋网分类 RSS
        rss_urls = {
            "ai": "https://www.leiphone.com/category/ai/rss",
            "transportation": "https://www.leiphone.com/category/transportation/rss",
            "aiot": "https://www.leiphone.com/category/aiot/rss",
        }

        feed_url = rss_urls.get(self.category, rss_urls["ai"])

        try:
            import feedparser
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, feed_url)

            result.total_found = len(feed.entries)

            for entry in feed.entries:
                try:
                    title = entry.get("title", "")
                    url = entry.get("link", "")
                    content = entry.get("summary", "")[:500]

                    publish_time = None
                    if "published_parsed" in entry:
                        try:
                            parsed = entry["published_parsed"]
                            publish_time = datetime(*parsed[:6])
                        except:
                            pass

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=entry.get("author", ""),
                        publish_time=publish_time,
                        keywords=["AI", "人工智能", "科技"],
                        extra={"source": "leiphone", "category": self.category}
                    )

                    if self.should_include(content_item):
                        result.items.append(content_item)
                    else:
                        result.total_filtered += 1

                except Exception as e:
                    continue

            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"

        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"

        return result


class PingWestCollector(BaseCollector):
    """品玩 - 科技媒体"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集品玩 RSS"""
        result = CollectorResult()

        try:
            rss_url = "https://www.pingwest.com/feed"

            import feedparser
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_url)

            result.total_found = len(feed.entries)

            for entry in feed.entries:
                try:
                    title = entry.get("title", "")
                    url = entry.get("link", "")
                    content = entry.get("summary", "")[:500]

                    publish_time = None
                    if "published_parsed" in entry:
                        try:
                            parsed = entry["published_parsed"]
                            publish_time = datetime(*parsed[:6])
                        except:
                            pass

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=entry.get("author", ""),
                        publish_time=publish_time,
                        extra={"source": "pingwest"}
                    )

                    if self.should_include(content_item):
                        result.items.append(content_item)
                    else:
                        result.total_filtered += 1

                except Exception as e:
                    continue

            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"

        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"

        return result


class GeekParkCollector(BaseCollector):
    """极客公园"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集极客公园 RSS"""
        result = CollectorResult()

        try:
            rss_url = "https://www.geekpark.net/rss"

            import feedparser
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_url)

            result.total_found = len(feed.entries)

            for entry in feed.entries:
                try:
                    title = entry.get("title", "")
                    url = entry.get("link", "")
                    content = entry.get("summary", "")[:500]

                    publish_time = None
                    if "published_parsed" in entry:
                        try:
                            parsed = entry["published_parsed"]
                            publish_time = datetime(*parsed[:6])
                        except:
                            pass

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=entry.get("author", ""),
                        publish_time=publish_time,
                        extra={"source": "geekpark"}
                    )

                    if self.should_include(content_item):
                        result.items.append(content_item)
                    else:
                        result.total_filtered += 1

                except Exception as e:
                    continue

            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"

        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"

        return result


class SinaTechCollector(BaseCollector):
    """新浪科技"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集新浪科技 RSS"""
        result = CollectorResult()

        try:
            # 新浪科技 RSS
            rss_url = "https://feed.sina.com.cn/tech/rollnews/doclist.xml"

            import feedparser
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_url)

            result.total_found = len(feed.entries)

            for entry in feed.entries:
                try:
                    title = entry.get("title", "")
                    url = entry.get("link", "")
                    content = entry.get("summary", "")[:400]

                    # 清理新浪的特殊标记
                    content = content.replace("新浪科技讯", "").strip()

                    publish_time = None
                    if "published_parsed" in entry:
                        try:
                            parsed = entry["published_parsed"]
                            publish_time = datetime(*parsed[:6])
                        except:
                            pass

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=entry.get("author", "新浪科技"),
                        publish_time=publish_time,
                        extra={"source": "sina_tech"}
                    )

                    if self.should_include(content_item):
                        result.items.append(content_item)
                    else:
                        result.total_filtered += 1

                except Exception as e:
                    continue

            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"

        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"

        return result


class NetEaseTechCollector(BaseCollector):
    """网易科技"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集网易科技 RSS"""
        result = CollectorResult()

        try:
            # 网易科技 RSS
            rss_url = "https://tech.163.com/special/000944N7/rss_digi.xml"

            import feedparser
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_url)

            result.total_found = len(feed.entries)

            for entry in feed.entries:
                try:
                    title = entry.get("title", "")
                    url = entry.get("link", "")
                    content = entry.get("summary", "")[:400]

                    publish_time = None
                    if "published_parsed" in entry:
                        try:
                            parsed = entry["published_parsed"]
                            publish_time = datetime(*parsed[:6])
                        except:
                            pass

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=entry.get("author", "网易科技"),
                        publish_time=publish_time,
                        extra={"source": "netease_tech"}
                    )

                    if self.should_include(content_item):
                        result.items.append(content_item)
                    else:
                        result.total_filtered += 1

                except Exception as e:
                    continue

            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"

        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"

        return result
