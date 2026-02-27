"""
采集模块 - 负责从各种数据源收集信息
"""
from src.collector.base import BaseCollector, CollectorResult
from src.collector.rss_collector import RSSCollector
from src.collector.api_collector import APICollector, HackerNewsCollector

__all__ = [
    "BaseCollector",
    "CollectorResult", 
    "RSSCollector",
    "APICollector",
    "HackerNewsCollector",
]
