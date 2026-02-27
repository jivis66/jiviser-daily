"""
RSS 采集器
支持标准 RSS/Atom 订阅源
"""
from datetime import datetime
from typing import Dict, Optional
from xml.etree import ElementTree as ET

import feedparser
from bs4 import BeautifulSoup

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class RSSCollector(BaseCollector):
    """RSS 采集器"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_url = config.get("url")
        if not self.feed_url:
            raise ValueError(f"RSS采集器 {name} 必须配置 url")
    
    async def collect(self) -> CollectorResult:
        """采集 RSS 订阅源"""
        result = CollectorResult()
        
        try:
            # 使用同步的 feedparser
            feed = await self._parse_feed()
            
            if feed.bozo:
                result.message = f"警告: 解析可能存在问题 - {feed.get('bozo_exception', 'Unknown')}"
            
            result.total_found = len(feed.entries)
            
            for entry in feed.entries:
                try:
                    item = self._parse_entry(entry)
                    if self.should_include(item):
                        result.items.append(item)
                    else:
                        result.total_filtered += 1
                except Exception as e:
                    result.message += f"\n解析条目失败: {str(e)}"
                    continue
            
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"
            
        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"
        
        return result
    
    async def _parse_feed(self):
        """解析 RSS Feed"""
        # feedparser 是同步的，但解析速度通常很快
        # 如果需要可以移到线程池执行
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, feedparser.parse, self.feed_url)
    
    def _parse_entry(self, entry: Dict) -> ContentItem:
        """解析 RSS 条目"""
        # 标题
        title = entry.get("title", "无标题")
        
        # 链接
        url = entry.get("link", "")
        if not url:
            # 有些 feed 链接在 guid 中
            url = entry.get("guid", "")
        
        # 清理 URL
        url = self.normalize_url(url)
        
        # 内容
        content = self._extract_content(entry)
        
        # 发布时间
        publish_time = None
        if "published_parsed" in entry:
            try:
                parsed = entry["published_parsed"]
                publish_time = datetime(*parsed[:6])
            except (TypeError, ValueError):
                pass
        
        if not publish_time and "updated_parsed" in entry:
            try:
                parsed = entry["updated_parsed"]
                publish_time = datetime(*parsed[:6])
            except (TypeError, ValueError):
                pass
        
        # 作者
        author = entry.get("author", "")
        if not author:
            # 尝试从 dc:creator 获取
            author = entry.get("dc:creator", "")
        
        # 标签/分类
        tags = []
        if "tags" in entry:
            tags = [tag.get("term", "") for tag in entry["tags"] if tag.get("term")]
        
        # 媒体内容
        image_url = None
        if "media_content" in entry and entry["media_content"]:
            image_url = entry["media_content"][0].get("url")
        elif "media_thumbnail" in entry and entry["media_thumbnail"]:
            image_url = entry["media_thumbnail"][0].get("url")
        elif "enclosures" in entry and entry["enclosures"]:
            for enc in entry["enclosures"]:
                if enc.get("type", "").startswith("image/"):
                    image_url = enc.get("href")
                    break
        
        # 从内容中提取图片
        if not image_url and content:
            image_url = self._extract_image(content)
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content,
            author=author,
            publish_time=publish_time,
            keywords=tags,
            image_url=image_url,
            raw_data=entry
        )
    
    def _extract_content(self, entry: Dict) -> str:
        """提取内容"""
        # 优先使用 content
        if "content" in entry and entry["content"]:
            return entry["content"][0].get("value", "")
        
        # 其次使用 description/summary
        if "description" in entry:
            return entry["description"]
        
        if "summary" in entry:
            return entry["summary"]
        
        return ""
    
    def _extract_image(self, html: str) -> Optional[str]:
        """从 HTML 中提取第一张图片"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                return img["src"]
        except Exception:
            pass
        return None


class AtomCollector(RSSCollector):
    """Atom 格式采集器（与 RSS 兼容）"""
    pass
