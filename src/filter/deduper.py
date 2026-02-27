"""
内容去重模块
支持精确去重和语义去重
"""
import hashlib
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models import ContentItem


@dataclass
class DedupResult:
    """去重结果"""
    items: List[ContentItem]  # 去重后的内容
    duplicates: List[Tuple[ContentItem, ContentItem]]  # (重复项, 保留项) 列表
    stats: Dict[str, int]  # 统计信息


class ContentDeduper:
    """内容去重器"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()
    
    def dedup(
        self, 
        items: List[ContentItem], 
        strategy: str = "semantic"
    ) -> DedupResult:
        """
        执行去重
        
        Args:
            items: 内容列表
            strategy: 去重策略 (exact/semantic/none)
            
        Returns:
            DedupResult: 去重结果
        """
        if strategy == "none":
            return DedupResult(items=items, duplicates=[], stats={"kept": len(items), "removed": 0})
        
        if strategy == "exact":
            return self._exact_dedup(items)
        
        return self._semantic_dedup(items)
    
    def _exact_dedup(self, items: List[ContentItem]) -> DedupResult:
        """精确去重 - 基于 URL 和标题哈希"""
        seen_urls: Set[str] = set()
        seen_titles: Dict[str, ContentItem] = {}
        kept: List[ContentItem] = []
        duplicates: List[Tuple[ContentItem, ContentItem]] = []
        
        for item in items:
            # URL 去重
            url_normalized = self._normalize_url(item.url)
            if url_normalized in seen_urls:
                # 找到重复项
                for kept_item in kept:
                    if self._normalize_url(kept_item.url) == url_normalized:
                        duplicates.append((item, kept_item))
                        break
                continue
            
            # 标题去重（归一化后比较）
            title_normalized = self._normalize_text(item.title)
            if title_normalized in seen_titles:
                duplicates.append((item, seen_titles[title_normalized]))
                continue
            
            seen_urls.add(url_normalized)
            seen_titles[title_normalized] = item
            kept.append(item)
        
        stats = {"kept": len(kept), "removed": len(items) - len(kept)}
        return DedupResult(items=kept, duplicates=duplicates, stats=stats)
    
    def _semantic_dedup(self, items: List[ContentItem]) -> DedupResult:
        """语义去重 - 基于内容相似度"""
        # 先进行精确去重
        exact_result = self._exact_dedup(items)
        items = exact_result.items
        duplicates = list(exact_result.duplicates)
        
        if len(items) <= 1:
            return DedupResult(
                items=items, 
                duplicates=duplicates,
                stats={"kept": len(items), "removed": len(items) - len(items)}
            )
        
        # 计算 TF-IDF 相似度
        texts = [self._get_dedup_text(item) for item in items]
        
        try:
            vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words="english"
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # 计算相似度矩阵
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 聚类去重
            kept_indices = []
            removed_indices = set()
            
            for i in range(len(items)):
                if i in removed_indices:
                    continue
                
                kept_indices.append(i)
                
                # 找到相似的项
                for j in range(i + 1, len(items)):
                    if j in removed_indices:
                        continue
                    
                    sim = similarity_matrix[i][j]
                    if sim >= self.similarity_threshold:
                        removed_indices.add(j)
                        duplicates.append((items[j], items[i]))
            
            kept = [items[i] for i in kept_indices]
            
        except Exception as e:
            # 如果失败，返回精确去重结果
            kept = items
        
        stats = {
            "kept": len(kept),
            "removed": len(items) - len(kept),
            "exact_dups": len(exact_result.duplicates)
        }
        
        return DedupResult(items=kept, duplicates=duplicates, stats=stats)
    
    def _normalize_url(self, url: str) -> str:
        """标准化 URL 用于比较"""
        # 移除协议、www、尾部斜杠
        url = url.lower().strip()
        url = re.sub(r"^https?://", "", url)
        url = re.sub(r"^www\.", "", url)
        url = url.rstrip("/")
        # 移除常见的追踪参数
        url = re.sub(r"\?(utm_.*|ref|source)=[^&]*", "", url)
        return url
    
    def _normalize_text(self, text: str) -> str:
        """标准化文本用于比较"""
        text = text.lower().strip()
        # 移除标点
        text = re.sub(r"[^\w\s]", "", text)
        # 移除多余空格
        text = re.sub(r"\s+", " ", text)
        # 移除常见词
        stop_words = ["the", "a", "an", "is", "are", "was", "were", "的", "了", "在"]
        for word in stop_words:
            text = text.replace(f" {word} ", " ")
        return text.strip()
    
    def _get_dedup_text(self, item: ContentItem) -> str:
        """获取用于去重的文本"""
        parts = [item.title]
        if item.content:
            # 取内容前 500 字符
            parts.append(item.content[:500])
        if item.keywords:
            parts.extend(item.keywords[:5])
        return " ".join(parts)
    
    def cluster_by_event(self, items: List[ContentItem]) -> List[List[ContentItem]]:
        """
        按事件聚类
        
        将相似的内容聚类到同一事件
        
        Args:
            items: 内容列表
            
        Returns:
            List[List[ContentItem]]: 事件簇列表
        """
        if len(items) <= 1:
            return [[item] for item in items]
        
        texts = [self._get_dedup_text(item) for item in items]
        
        try:
            vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 简单的贪心聚类
            clusters = []
            used = set()
            
            for i in range(len(items)):
                if i in used:
                    continue
                
                cluster = [items[i]]
                used.add(i)
                
                for j in range(i + 1, len(items)):
                    if j in used:
                        continue
                    if similarity_matrix[i][j] >= self.similarity_threshold:
                        cluster.append(items[j])
                        used.add(j)
                
                clusters.append(cluster)
            
            return clusters
            
        except Exception:
            return [[item] for item in items]


class SimHashDeduper:
    """基于 SimHash 的去重器（适合大规模数据）"""
    
    def __init__(self, hash_size: int = 64, distance_threshold: int = 3):
        self.hash_size = hash_size
        self.distance_threshold = distance_threshold
        self.hashes: Dict[str, int] = {}
    
    def _compute_hash(self, text: str) -> int:
        """计算 SimHash"""
        import hashlib
        
        # 简单实现：使用 MD5 的前 64 位
        # 实际生产环境应使用真正的 SimHash 算法
        md5_hash = hashlib.md5(text.encode()).hexdigest()
        return int(md5_hash[:16], 16)
    
    def _hamming_distance(self, h1: int, h2: int) -> int:
        """计算汉明距离"""
        x = h1 ^ h2
        distance = 0
        while x:
            distance += 1
            x &= x - 1
        return distance
    
    def is_duplicate(self, text: str) -> Optional[str]:
        """检查是否重复"""
        h = self._compute_hash(text)
        
        for item_id, existing_hash in self.hashes.items():
            if self._hamming_distance(h, existing_hash) <= self.distance_threshold:
                return item_id
        
        return None
    
    def add(self, item_id: str, text: str):
        """添加哈希"""
        self.hashes[item_id] = self._compute_hash(text)
