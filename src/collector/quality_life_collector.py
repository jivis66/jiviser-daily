"""
优质生活方式/效率工具类媒体采集器
支持少数派、数字尾巴、爱范儿、小众软件等
"""
from datetime import datetime
from typing import Dict, Optional

from bs4 import BeautifulSoup

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class SspaiCollector(BaseCollector):
    """少数派 - 高效工作，品质生活"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.matrix = config.get("matrix", "home")  # home, matrix(社区)

    async def collect(self) -> CollectorResult:
        """采集少数派 RSS"""
        result = CollectorResult()

        try:
            # 少数派 RSS
            rss_urls = {
                "home": "https://sspai.com/feed",
                "matrix": "https://sspai.com/feed/matrix",
            }

            feed_url = rss_urls.get(self.matrix, rss_urls["home"])

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

                    # 发布时间
                    publish_time = None
                    if "published_parsed" in entry:
                        try:
                            parsed = entry["published_parsed"]
                            publish_time = datetime(*parsed[:6])
                        except:
                            pass

                    # 作者
                    author = entry.get("author", "")
                    # RSS中没有作者时尝试从内容提取
                    if not author:
                        # 尝试从 RSS 扩展字段获取
                        author = entry.get("dc_creator", "")

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=author,
                        publish_time=publish_time,
                        keywords=["效率", "工具", "生活方式", "数字"],
                        extra={"source": "sspai", "matrix": self.matrix}
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


class IfanrCollector(BaseCollector):
    """爱范儿 - 聚焦创新及消费科技"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.category = config.get("category", "all")  # all, appso, coolbuy

    async def collect(self) -> CollectorResult:
        """采集爱范儿 RSS"""
        result = CollectorResult()

        try:
            # 爱范儿 RSS
            rss_urls = {
                "all": "https://www.ifanr.com/feed",
                "appso": "https://www.ifanr.com/app/feed",  # AppSo
            }

            feed_url = rss_urls.get(self.category, rss_urls["all"])

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
                        keywords=["科技", "数码", "生活方式"],
                        extra={"source": "ifanr", "category": self.category}
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


class DgtleCollector(BaseCollector):
    """数字尾巴 - 分享美好数字生活"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集数字尾巴 RSS"""
        result = CollectorResult()

        try:
            # 数字尾巴 RSS
            rss_url = "https://www.dgtle.com/rss/dgtle.xml"

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
                        keywords=["数码", "生活方式", "评测"],
                        extra={"source": "dgtle"}
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


class AppinnCollector(BaseCollector):
    """小众软件 - 分享免费、小巧、有趣、实用的软件"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集小众软件 RSS"""
        result = CollectorResult()

        try:
            # 小众软件 RSS
            rss_url = "https://www.appinn.com/feed/"

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
                        keywords=["软件", "工具", "效率", "免费"],
                        extra={"source": "appinn"}
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


class LiqiCollector(BaseCollector):
    """利器 - 采访优秀的创造者，邀请他们分享工作时所使用的工具"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集利器 RSS"""
        result = CollectorResult()

        try:
            # 利器 RSS
            rss_url = "https://liqi.io/feed/"

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
                        keywords=["工具", "效率", "创作者", "工作流"],
                        extra={"source": "liqi"}
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


class UisdcCollector(BaseCollector):
    """优设网 - 设计师交流平台"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.category = config.get("category", "article")  # article, inspiration

    async def collect(self) -> CollectorResult:
        """采集优设 RSS"""
        result = CollectorResult()

        try:
            # 优设 RSS
            rss_urls = {
                "article": "https://www.uisdc.com/feed",
                "inspiration": "https://www.uisdc.com/feed/inspiration",
            }

            feed_url = rss_urls.get(self.category, rss_urls["article"])

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
                        keywords=["设计", "UI", "UX", "创意"],
                        extra={"source": "uisdc", "category": self.category}
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


class ToodaylabCollector(BaseCollector):
    """理想生活实验室 - 关注创意设计和生活方式"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集理想生活实验室 RSS"""
        result = CollectorResult()

        try:
            # 理想生活实验室 RSS
            rss_url = "https://www.toodaylab.com/feed"

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
                        keywords=["设计", "生活方式", "创意", "文化"],
                        extra={"source": "toodaylab"}
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
