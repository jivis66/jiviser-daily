"""
采集器测试
"""
import pytest
from src.collector.rss_collector import RSSCollector
from src.collector.api_collector import HackerNewsCollector


@pytest.mark.asyncio
async def test_rss_collector():
    """测试 RSS 采集器"""
    config = {
        "url": "https://news.ycombinator.com/rss",
        "weight": 1.0,
        "filter": {}
    }
    
    collector = RSSCollector("HNRSS", config)
    result = await collector.collect()
    
    assert result.success
    assert len(result.items) > 0
    
    await collector.close()


@pytest.mark.asyncio
async def test_hackernews_collector():
    """测试 Hacker News 采集器"""
    config = {
        "max_items": 10,
        "filter": {"min_score": 50}
    }
    
    collector = HackerNewsCollector("HN", config)
    result = await collector.collect()
    
    assert result.success
    
    await collector.close()


@pytest.mark.asyncio
async def test_collector_filter():
    """测试采集器过滤"""
    from src.models import ContentItem
    
    config = {
        "url": "https://example.com/feed",
        "weight": 1.0,
        "filter": {
            "keywords": ["AI", "人工智能"]
        }
    }
    
    collector = RSSCollector("Test", config)
    
    # 测试过滤
    item1 = ContentItem(
        title="AI breakthrough today",
        url="http://example.com/1",
        source="Test",
        source_type="rss",
        keywords=["AI"]
    )
    
    item2 = ContentItem(
        title="Sports news",
        url="http://example.com/2",
        source="Test",
        source_type="rss",
        keywords=["sports"]
    )
    
    assert collector.should_include(item1) == True
    assert collector.should_include(item2) == False
    
    await collector.close()
