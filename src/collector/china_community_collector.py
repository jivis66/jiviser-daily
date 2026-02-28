"""
中国社区类信息源采集器
支持V2EX、雪球、雪球组合、一亩三分地等
"""
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class V2EXCollector(BaseCollector):
    """V2EX 技术社区"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.WEB, config)
        self.node = config.get("node", "python")  # python, go, java, ai
        self.limit = config.get("limit", 10)

    async def collect(self) -> CollectorResult:
        """采集V2EX热门主题"""
        result = CollectorResult()

        try:
            # V2EX API
            url = f"https://www.v2ex.com/api/topics/hot.json"
            if self.node:
                url = f"https://www.v2ex.com/api/nodes/{self.node}/topics.json"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }

            response = await self.client.get(url, headers=headers, follow_redirects=True)

            # 检查响应状态
            if response.status_code != 200:
                result.success = False
                result.message = f"HTTP {response.status_code}"
                return result

            try:
                items = response.json()
            except Exception as e:
                result.success = False
                result.message = f"JSON解析失败: {str(e)[:50]}"
                return result

            if not isinstance(items, list):
                result.success = False
                result.message = "API返回格式错误"
                return result

            result.total_found = len(items)

            for item in items[:self.limit]:
                try:
                    title = item.get("title", "")
                    url = item.get("url", "")
                    content = item.get("content", "")[:500]

                    # V2EX使用Unix时间戳
                    created = item.get("created", 0)
                    publish_time = datetime.fromtimestamp(created) if created else None

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=item.get("member", {}).get("username", ""),
                        publish_time=publish_time,
                        popularity_score=float(item.get("replies", 0)),
                        extra={
                            "node": self.node,
                            "replies": item.get("replies"),
                            "views": item.get("views"),
                        }
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


class XueqiuCollector(BaseCollector):
    """雪球 - 投资者社区"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.WEB, config)
        self.category = config.get("category", "hot")  # hot, new
        self.limit = config.get("limit", 10)

    async def collect(self) -> CollectorResult:
        """采集雪球热门文章"""
        result = CollectorResult()

        try:
            # 雪球文章列表
            url = "https://xueqiu.com/statuses/original.json"
            params = {
                "page": 1,
                "count": self.limit,
                "sort": "time" if self.category == "new" else "hot"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://xueqiu.com/"
            }

            response = await self.client.get(url, params=params, headers=headers)
            data = response.json()

            items = data.get("list", [])
            result.total_found = len(items)

            for item in items:
                try:
                    article = item.get("article", {})
                    title = article.get("title", "")
                    if not title:
                        # 有些文章只有描述
                        title = article.get("description", "")[:50] + "..."

                    url = f"https://xueqiu.com{item.get('target', '')}"
                    content = article.get("description", "")[:500]

                    # 时间戳转换
                    created_at = item.get("created_at", 0)
                    publish_time = datetime.fromtimestamp(created_at / 1000) if created_at else None

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        author=item.get("user", {}).get("screen_name", ""),
                        publish_time=publish_time,
                        popularity_score=float(item.get("view_count", 0)),
                        extra={
                            "category": self.category,
                            "view_count": item.get("view_count"),
                            "like_count": item.get("like_count"),
                        }
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


class WallstreetCnCollector(BaseCollector):
    """华尔街见闻 - 财经"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.category = config.get("category", "hot")

    async def collect(self) -> CollectorResult:
        """采集华尔街见闻"""
        result = CollectorResult()

        try:
            # 华尔街见闻 RSS
            rss_urls = {
                "hot": "https://rsshub.app/wallstreetcn/hot",
                "news": "https://rsshub.app/wallstreetcn/news",
                "global": "https://rsshub.app/wallstreetcn/global",
            }

            feed_url = rss_urls.get(self.category, rss_urls["hot"])

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
                        extra={"source": "wallstreetcn", "category": self.category}
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


class ITPubCollector(BaseCollector):
    """ITPUB - IT社区"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.category = config.get("category", "hot")

    async def collect(self) -> CollectorResult:
        """采集ITPUB热门文章"""
        result = CollectorResult()

        try:
            # ITPUB RSS
            rss_urls = {
                "hot": "https://www.itpub.net/rss/hot",
                "db": "https://www.itpub.net/rss/database",
                "ai": "https://www.itpub.net/rss/ai",
            }

            feed_url = rss_urls.get(self.category, rss_urls["hot"])

            import feedparser
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, feed_url)

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
                        author=entry.get("author", ""),
                        publish_time=publish_time,
                        extra={"source": "itpub", "category": self.category}
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


class ChinaUnixCollector(BaseCollector):
    """ChinaUnix - Linux/开源社区"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        """采集ChinaUnix热门文章"""
        result = CollectorResult()

        try:
            rss_url = "https://www.chinaunix.net/rss.php"

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
                        author=entry.get("author", ""),
                        publish_time=publish_time,
                        keywords=["Linux", "开源", "运维"],
                        extra={"source": "chinaunix"}
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
