"""
中国科技媒体采集器
支持稀土掘金、开源中国、InfoQ、CSDN等
"""
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class JuejinCollector(BaseCollector):
    """稀土掘金 - 技术社区"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.WEB, config)
        self.category = config.get("category", "all")  # all, frontend, backend, ai
        self.limit = config.get("limit", 10)

    async def collect(self) -> CollectorResult:
        """采集掘金热榜"""
        result = CollectorResult()

        try:
            # 掘金热榜 API
            url = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
            payload = {
                "client_type": 2608,
                "cursor": "0",
                "id_type": 2,
                "limit": self.limit,
                "sort_type": 200  # 热榜
            }

            response = await self.client.post(url, json=payload)
            data = response.json()

            if data.get("err_no") != 0:
                result.success = False
                result.message = f"API 错误: {data.get('err_msg')}"
                return result

            items = data.get("data", [])
            result.total_found = len(items)

            for item in items:
                try:
                    article = item.get("item_info", {}).get("article_info", {})
                    if not article:
                        continue

                    title = article.get("title", "")
                    url = f"https://juejin.cn/post/{article.get('article_id')}"
                    content = article.get("brief_content", "")

                    # 过滤非技术内容
                    if self.should_include_by_keywords(title, content):
                        content_item = self.create_content_item(
                            title=title,
                            url=url,
                            content=content,
                            author=article.get("author_name", ""),
                            popularity_score=float(article.get("view_count", 0)),
                            extra={
                                "category": self.category,
                                "tags": article.get("tags", []),
                                "read_count": article.get("view_count"),
                                "like_count": article.get("digg_count"),
                            }
                        )
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

    def should_include_by_keywords(self, title: str, content: str) -> bool:
        """根据关键词过滤"""
        text = (title + " " + content).lower()
        tech_keywords = [
            "ai", "人工智能", "大模型", "llm", "chatgpt", "claude",
            "前端", "后端", "python", "javascript", "typescript", "java",
            "go", "golang", "rust", "react", "vue", "angular",
            "docker", "kubernetes", "k8s", "云原生", "devops",
            "算法", "数据结构", "leetcode", "面试",
            "开源", "github", "开源项目",
            "架构", "微服务", "分布式",
        ]
        return any(kw in text for kw in tech_keywords)


class OschinaCollector(BaseCollector):
    """开源中国 - 开源资讯"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_type = config.get("feed_type", "news")  # news, blog, project

    async def collect(self) -> CollectorResult:
        """采集开源中国 RSS"""
        result = CollectorResult()

        # 开源中国 RSS 源
        rss_urls = {
            "news": "https://www.oschina.net/news/rss",
            "blog": "https://www.oschina.net/blog/rss",
        }

        feed_url = rss_urls.get(self.feed_type, rss_urls["news"])

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
                        keywords=[tag.get("term", "") for tag in entry.get("tags", [])],
                        extra={"source": "oschina", "type": self.feed_type}
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


class InfoqChinaCollector(BaseCollector):
    """InfoQ 中文站"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.WEB, config)
        self.category = config.get("category", "ai-ml")  # ai-ml, architecture, devops

    async def collect(self) -> CollectorResult:
        """采集 InfoQ 中文站"""
        result = CollectorResult()

        try:
            # InfoQ 列表页
            url = f"https://www.infoq.cn/{self.category}"
            headers = {
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = await self.client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            # 解析文章列表
            articles = soup.find_all("div", class_="card")
            result.total_found = len(articles)

            for article in articles:
                try:
                    title_elem = article.find("h3") or article.find("h2")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link_elem = article.find("a", href=True)
                    if not link_elem:
                        continue

                    url = link_elem["href"]
                    if url.startswith("/"):
                        url = f"https://www.infoq.cn{url}"

                    # 摘要
                    summary_elem = article.find("p", class_="summary") or article.find("p")
                    content = summary_elem.get_text(strip=True)[:300] if summary_elem else ""

                    content_item = self.create_content_item(
                        title=title,
                        url=url,
                        content=content,
                        extra={"category": self.category, "source": "infoq_cn"}
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


class SegmentFaultCollector(BaseCollector):
    """思否 SegmentFault"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.tag = config.get("tag", "python")
        self.limit = config.get("limit", 10)

    async def collect(self) -> CollectorResult:
        """采集思否 RSS"""
        result = CollectorResult()

        try:
            import feedparser
            import asyncio

            rss_url = f"https://segmentfault.com/feeds/tag/{self.tag}"
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_url)

            if not feed.entries:
                result.success = True
                result.message = "RSS返回空数据"
                return result

            entries = feed.entries[:self.limit]
            result.total_found = len(feed.entries)

            for entry in entries:
                try:
                    title = entry.get("title", "")
                    url = entry.get("link", "")
                    content = entry.get("summary", "")[:300]

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
                        extra={"tag": self.tag, "source": "segmentfault"}
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
