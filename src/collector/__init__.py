"""
采集模块 - 负责从各种数据源收集信息
"""
from src.collector.base import BaseCollector, CollectorManager, CollectorResult
from src.collector.rss_collector import RSSCollector
from src.collector.api_collector import APICollector, HackerNewsCollector
from src.collector.bilibili_collector import BilibiliCollector, BilibiliHotCollector
from src.collector.xiaohongshu_collector import XiaohongshuCollector, XiaohongshuSearchCollector

__all__ = [
    "BaseCollector",
    "CollectorManager",
    "CollectorResult",
    "RSSCollector",
    "APICollector",
    "HackerNewsCollector",
    "BilibiliCollector",
    "BilibiliHotCollector",
    "XiaohongshuCollector",
    "XiaohongshuSearchCollector",
]
