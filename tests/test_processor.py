"""
处理器测试
"""
import pytest
from src.models import ContentItem
from src.processor.cleaner import ContentCleaner
from src.processor.extractor import KeywordExtractor, TopicClassifier


def test_content_cleaner():
    """测试内容清洗"""
    cleaner = ContentCleaner()
    
    html = "<html><body><p>Hello <b>World</b></p><script>alert(1)</script></body></html>"
    result = cleaner.clean(html)
    
    assert "Hello" in result
    assert "World" in result
    assert "<script>" not in result


def test_keyword_extractor():
    """测试关键词提取"""
    extractor = KeywordExtractor()
    
    item = ContentItem(
        title="Python and Machine Learning Tutorial",
        url="http://example.com",
        source="Test",
        source_type="rss",
        content="This is a tutorial about Python programming and machine learning.",
        keywords=[]
    )
    
    keywords = extractor.extract(item, top_k=5)
    
    assert len(keywords) > 0
    assert isinstance(keywords[0], str)


def test_topic_classifier():
    """测试主题分类"""
    classifier = TopicClassifier()
    
    item = ContentItem(
        title="OpenAI releases GPT-4",
        url="http://example.com",
        source="Test",
        source_type="rss",
        keywords=["AI", "OpenAI", "GPT"],
        topics=[]
    )
    
    topics = classifier.classify(item)
    
    assert len(topics) > 0
    assert "人工智能" in topics or "AI" in str(topics)
