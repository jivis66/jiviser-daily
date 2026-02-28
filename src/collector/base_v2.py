"""
采集器基类 v2 - 改进版
减少重复代码，统一错误处理
"""
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, Generic, List, Optional, TypeVar

import httpx
from rich.console import Console

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem

T = TypeVar('T')
console = Console()


@dataclass
class CollectContext:
    """采集上下文"""
    source_name: str
    progress_callback: Optional[Callable[[str, int, int], None]] = None
    errors: List[str] = field(default_factory=list)

    def report_progress(self, message: str, current: int, total: int):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, current, total)

    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)


class BaseCollectorV2(BaseCollector, ABC):
    """
    改进版采集器基类

    特点：
    - 统一的错误处理和日志
    - 自动进度报告
    - 简化的结果构建
    - 批量处理支持
    """

    async def collect(self) -> CollectorResult:
        """
        采集入口 - 提供统一的错误处理和进度报告
        子类应该实现 _do_collect 方法
        """
        result = CollectorResult()
        context = CollectContext(source_name=self.name)

        try:
            console.print(f"[dim]开始采集: {self.name}...[/dim]")

            items = await self._do_collect(context)

            # 应用过滤
            filtered_items = []
            for item in items:
                if self.should_include(item):
                    filtered_items.append(item)
                else:
                    result.total_filtered += 1

            result.items = filtered_items
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(filtered_items)} 条内容"

            if result.total_filtered > 0:
                result.message += f" (过滤 {result.total_filtered} 条)"

            if context.errors:
                result.message += f"\n警告: {len(context.errors)} 个条目解析失败"

        except httpx.HTTPError as e:
            result.success = False
            result.message = f"网络错误: {e}"
        except Exception as e:
            result.success = False
            result.message = f"采集失败: {e}"

        status_icon = "[green]✓[/green]" if result.success else "[red]✗[/red]"
        console.print(f"{status_icon} {self.name}: {result.message}")

        return result

    @abstractmethod
    async def _do_collect(self, context: CollectContext) -> List[ContentItem]:
        """
        实际采集逻辑 - 子类实现

        Args:
            context: 采集上下文，用于报告进度和错误

        Returns:
            采集到的内容列表
        """
        pass

    def safe_create_item(self, **kwargs) -> Optional[ContentItem]:
        """
        安全地创建内容条目，捕获异常
        """
        try:
            return self.create_content_item(**kwargs)
        except Exception as e:
            console.print(f"[yellow]警告: 创建内容条目失败: {e}[/yellow]")
            return None


class BatchCollector(BaseCollectorV2, Generic[T]):
    """
    批量采集器基类

    适用于需要批量获取详情的 API（如 Hacker News）
    """

    async def _do_collect(self, context: CollectContext) -> List[ContentItem]:
        """批量采集流程"""
        # 1. 获取 ID 列表
        ids = await self._fetch_ids(context)
        if not ids:
            return []

        # 2. 批量获取详情
        items = []
        for i, id in enumerate(ids):
            context.report_progress(f"获取详情 {i+1}/{len(ids)}", i + 1, len(ids))

            try:
                data = await self._fetch_detail(id)
                if data:
                    item = self._parse_item(data)
                    if item:
                        items.append(item)
            except Exception as e:
                context.add_error(f"获取 {id} 失败: {e}")
                continue

        return items

    @abstractmethod
    async def _fetch_ids(self, context: CollectContext) -> List[T]:
        """获取条目 ID 列表"""
        pass

    @abstractmethod
    async def _fetch_detail(self, id: T) -> Optional[Dict]:
        """获取单个条目详情"""
        pass

    @abstractmethod
    def _parse_item(self, data: Dict) -> Optional[ContentItem]:
        """解析条目数据"""
        pass


class SimpleRSSCollector(BaseCollectorV2):
    """
    简化版 RSS 采集器
    使用 v2 基类，代码更简洁
    """

    def __init__(self, name: str, config: Dict):
        from src.models import SourceType
        super().__init__(name, SourceType.RSS, config)
        self.feed_url = config.get("url")
        if not self.feed_url:
            raise ValueError(f"RSS采集器 {name} 必须配置 url")

    async def _do_collect(self, context: CollectContext) -> List[ContentItem]:
        import feedparser

        # 解析 Feed
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, self.feed_url)

        if feed.bozo:
            console.print(f"[yellow]警告: RSS 解析可能有问题: {feed.get('bozo_exception')}[/yellow]")

        items = []
        for entry in feed.entries:
            try:
                item = self._parse_entry(entry)
                if item:
                    items.append(item)
            except Exception as e:
                context.add_error(f"解析条目失败: {e}")
                continue

        return items

    def _parse_entry(self, entry) -> Optional[ContentItem]:
        """解析 RSS 条目"""
        from datetime import datetime

        title = entry.get("title", "无标题")
        url = entry.get("link", entry.get("guid", ""))

        if not url:
            return None

        # 内容
        content = ""
        if "content" in entry:
            content = entry["content"][0].get("value", "")
        elif "description" in entry:
            content = entry["description"]
        elif "summary" in entry:
            content = entry["summary"]

        # 发布时间
        publish_time = None
        for key in ["published_parsed", "updated_parsed"]:
            if key in entry:
                try:
                    parsed = entry[key]
                    publish_time = datetime(*parsed[:6])
                    break
                except:
                    pass

        # 作者
        author = entry.get("author", entry.get("dc:creator", ""))

        # 标签
        tags = []
        if "tags" in entry:
            tags = [tag.get("term", "") for tag in entry["tags"] if tag.get("term")]

        return self.create_content_item(
            title=title,
            url=url,
            content=content,
            author=author,
            publish_time=publish_time,
            keywords=tags,
            raw_data=dict(entry)
        )


class HackerNewsCollectorV2(BatchCollector[int]):
    """
    Hacker News 采集器 v2 - 使用批量采集基类
    """

    API_BASE = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, name: str, config: Dict):
        from src.models import SourceType
        # 不调用父类 __init__，直接设置属性
        self.name = name
        self.source_type = SourceType.API
        self.config = config or {}
        self.weight = self.config.get("weight", 1.0)
        self.filter_config = self.config.get("filter", {})
        self._client = None

        self.min_score = config.get("filter", {}).get("min_score", 100)
        self.max_items = config.get("max_items", 30)

    async def _fetch_ids(self, context: CollectContext) -> List[int]:
        """获取热门故事 ID"""
        response = await self.fetch_url(f"{self.API_BASE}/topstories.json")
        return response.json()[:self.max_items]

    async def _fetch_detail(self, story_id: int) -> Optional[Dict]:
        """获取故事详情"""
        response = await self.fetch_url(f"{self.API_BASE}/item/{story_id}.json")
        data = response.json()

        # 过滤低分
        if data.get("score", 0) < self.min_score:
            return None

        return data

    def _parse_item(self, story: Dict) -> Optional[ContentItem]:
        """解析故事"""
        from datetime import datetime

        title = story.get("title", "无标题")
        url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}")
        content = story.get("text", "")
        score = story.get("score", 0)
        author = story.get("by", "")

        time_unix = story.get("time", 0)
        publish_time = datetime.utcfromtimestamp(time_unix) if time_unix else None

        return self.create_content_item(
            title=title,
            url=url,
            content=content,
            author=author,
            publish_time=publish_time,
            popularity_score=float(score),
            extra={
                "score": score,
                "comments": story.get("descendants", 0),
                "hn_id": story.get("id")
            }
        )
