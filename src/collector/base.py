"""
采集器基类
"""
import asyncio
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings
from src.models import ContentItem, ContentStatus, SourceType

settings = get_settings()


@dataclass
class CollectorResult:
    """采集结果"""
    items: List[ContentItem] = field(default_factory=list)
    success: bool = True
    message: str = ""
    total_found: int = 0
    total_filtered: int = 0


class BaseCollector(ABC):
    """采集器基类"""
    
    def __init__(self, name: str, source_type: SourceType, config: Optional[Dict] = None):
        self.name = name
        self.source_type = source_type
        self.config = config or {}
        self.weight = self.config.get("weight", 1.0)
        self.filter_config = self.config.get("filter", {})
        
        # HTTP 客户端
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（延迟初始化）"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                }
            )
        return self._client
    
    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @abstractmethod
    async def collect(self) -> CollectorResult:
        """
        执行采集
        
        Returns:
            CollectorResult: 采集结果
        """
        pass
    
    def create_content_item(
        self,
        title: str,
        url: str,
        content: Optional[str] = None,
        **kwargs
    ) -> ContentItem:
        """
        创建内容条目
        
        Args:
            title: 标题
            url: URL
            content: 内容
            **kwargs: 其他字段
            
        Returns:
            ContentItem: 内容条目
        """
        # 生成稳定 ID
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        
        item = ContentItem(
            id=f"{self.source_type.value}_{url_hash}",
            title=title,
            url=url,
            source=self.name,
            source_type=self.source_type,
            content=content,
            **kwargs
        )
        return item
    
    def should_include(self, item: ContentItem) -> bool:
        """
        根据配置过滤内容
        
        Args:
            item: 内容条目
            
        Returns:
            bool: 是否包含
        """
        # 关键词过滤
        keywords = self.filter_config.get("keywords", [])
        if keywords:
            text = f"{item.title} {' '.join(item.keywords)}".lower()
            if not any(kw.lower() in text for kw in keywords):
                return False
        
        # 排除关键词
        exclude = self.filter_config.get("exclude", [])
        if exclude:
            text = f"{item.title} {item.content or ''}".lower()
            if any(ex.lower() in text for ex in exclude):
                return False
        
        # 最小点赞数（社交媒体）
        min_likes = self.filter_config.get("min_likes")
        if min_likes and item.extra.get("likes", 0) < min_likes:
            return False
        
        # 最小分数
        min_score = self.filter_config.get("min_score")
        if min_score and item.popularity_score < min_score:
            return False
        
        return True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def fetch_url(self, url: str, **kwargs) -> httpx.Response:
        """
        获取 URL 内容（带重试）
        
        Args:
            url: 目标 URL
            **kwargs: 额外请求参数
            
        Returns:
            httpx.Response: 响应对象
        """
        await asyncio.sleep(settings.request_delay)
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response
    
    def extract_domain(self, url: str) -> str:
        """提取域名"""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def normalize_url(self, url: str) -> str:
        """标准化 URL"""
        # 移除追踪参数
        tracking_params = ["utm_source", "utm_medium", "utm_campaign", "utm_content"]
        parsed = urlparse(url)
        
        # 重新构建 URL，移除追踪参数
        query = "&".join(
            f"{k}={v}" 
            for k, v in [p.split("=") for p in parsed.query.split("&") if "=" in p]
            if k not in tracking_params
        )
        
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query}" if query else f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


class CollectorManager:
    """采集器管理器"""
    
    def __init__(self):
        self.collectors: List[BaseCollector] = []
    
    def register(self, collector: BaseCollector):
        """注册采集器"""
        self.collectors.append(collector)
    
    async def collect_all(self, max_concurrent: int = None) -> Dict[str, CollectorResult]:
        """
        执行所有采集器
        
        Args:
            max_concurrent: 最大并发数
            
        Returns:
            Dict[str, CollectorResult]: 采集结果字典
        """
        max_concurrent = max_concurrent or settings.max_concurrent_collectors
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def collect_with_limit(collector: BaseCollector) -> tuple:
            async with semaphore:
                try:
                    result = await collector.collect()
                    return collector.name, result
                except Exception as e:
                    return collector.name, CollectorResult(
                        success=False,
                        message=str(e)
                    )
                finally:
                    await collector.close()
        
        tasks = [collect_with_limit(c) for c in self.collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {name: result for name, result in results if not isinstance(result, Exception)}
    
    def get_collector(self, name: str) -> Optional[BaseCollector]:
        """获取指定采集器"""
        for c in self.collectors:
            if c.name == name:
                return c
        return None
