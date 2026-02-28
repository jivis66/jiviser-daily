"""
处理缓存模块
用于缓存 LLM 处理结果，避免重复处理相同内容
"""
import hashlib
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from src.models import ContentItem


@dataclass
class CacheEntry:
    """缓存条目"""
    content_hash: str
    summary: str
    key_points: List[str]
    keywords: List[str]
    entities: List[str]
    topics: List[str]
    timestamp: float
    ttl: int = 3600  # 默认缓存 1 小时


class ProcessingCache:
    """
    处理结果缓存
    
    基于内容哈希缓存处理结果，避免重复调用 LLM
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def _generate_hash(self, item: ContentItem) -> str:
        """生成内容哈希"""
        # 使用标题和内容前 500 字作为哈希基础
        content = f"{item.title}:{item.content[:500] if item.content else ''}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, item: ContentItem) -> Optional[CacheEntry]:
        """
        获取缓存
        
        Args:
            item: 内容条目
            
        Returns:
            CacheEntry: 缓存的条目，如果不存在或已过期则返回 None
        """
        content_hash = self._generate_hash(item)
        entry = self._cache.get(content_hash)
        
        if entry is None:
            self._misses += 1
            return None
        
        # 检查是否过期
        if time.time() - entry.timestamp > entry.ttl:
            del self._cache[content_hash]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry
    
    def set(
        self, 
        item: ContentItem, 
        summary: str = None,
        key_points: List[str] = None,
        keywords: List[str] = None,
        entities: List[str] = None,
        topics: List[str] = None,
        ttl: int = None
    ):
        """
        设置缓存
        
        Args:
            item: 内容条目
            summary: 摘要
            key_points: 关键要点
            keywords: 关键词
            entities: 实体
            topics: 主题
            ttl: 过期时间（秒）
        """
        # 检查缓存大小，如果超过限制则清理最旧的条目
        if len(self._cache) >= self._max_size:
            self._cleanup_old_entries()
        
        content_hash = self._generate_hash(item)
        
        self._cache[content_hash] = CacheEntry(
            content_hash=content_hash,
            summary=summary or "",
            key_points=key_points or [],
            keywords=keywords or [],
            entities=entities or [],
            topics=topics or [],
            timestamp=time.time(),
            ttl=ttl or self._default_ttl
        )
    
    def _cleanup_old_entries(self, ratio: float = 0.3):
        """
        清理旧的缓存条目
        
        Args:
            ratio: 清理比例
        """
        # 按时间排序，删除最旧的
        sorted_items = sorted(
            self._cache.items(), 
            key=lambda x: x[1].timestamp
        )
        
        to_remove = int(len(sorted_items) * ratio)
        for key, _ in sorted_items[:to_remove]:
            del self._cache[key]
    
    def apply_to_item(self, item: ContentItem, entry: CacheEntry) -> ContentItem:
        """
        将缓存应用到内容条目
        
        Args:
            item: 内容条目
            entry: 缓存条目
            
        Returns:
            ContentItem: 更新后的内容条目
        """
        if entry.summary:
            item.summary = entry.summary
        if entry.key_points:
            item.key_points = entry.key_points
        if entry.keywords:
            item.keywords = entry.keywords
        if entry.entities:
            item.entities = entry.entities
        if entry.topics:
            item.topics = entry.topics
        
        return item
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1%}",
            "hit_rate_value": hit_rate
        }
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def cleanup_expired(self):
        """清理过期条目"""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now - entry.timestamp > entry.ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)


# 全局缓存实例
_processing_cache: Optional[ProcessingCache] = None


def get_processing_cache() -> ProcessingCache:
    """获取全局处理缓存"""
    global _processing_cache
    if _processing_cache is None:
        _processing_cache = ProcessingCache()
    return _processing_cache
