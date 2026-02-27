"""
摘要生成模块
支持抽取式和生成式摘要
"""
import re
from abc import ABC, abstractmethod
from typing import List, Optional

import jieba

from src.config import get_settings
from src.models import ContentItem

settings = get_settings()


class Summarizer(ABC):
    """摘要器基类"""
    
    @abstractmethod
    async def summarize(
        self, 
        item: ContentItem, 
        style: str = "3_points",
        max_length: int = 500
    ) -> str:
        """
        生成摘要
        
        Args:
            item: 内容条目
            style: 摘要风格 (1_sentence/3_points/paragraph/detailed)
            max_length: 最大长度
            
        Returns:
            str: 摘要文本
        """
        pass
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        # 中文句号、英文句号、问号、感叹号
        sentences = re.split(r"(?<=[。．.!?！？])\s*", text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_importance(self, sentence: str, title: str, keywords: List[str]) -> float:
        """
        计算句子重要性
        
        基于：
        - 是否包含关键词
        - 与标题的相似度
        - 句子位置
        """
        score = 0.0
        sentence_lower = sentence.lower()
        
        # 关键词匹配
        for kw in keywords:
            if kw.lower() in sentence_lower:
                score += 1.0
        
        # 标题词匹配
        title_words = set(jieba.lcut(title.lower()))
        sentence_words = set(jieba.lcut(sentence_lower))
        common_words = title_words & sentence_words
        score += len(common_words) * 0.5
        
        return score


class ExtractiveSummarizer(Summarizer):
    """抽取式摘要器"""
    
    async def summarize(
        self, 
        item: ContentItem, 
        style: str = "3_points",
        max_length: int = 500
    ) -> str:
        """生成抽取式摘要"""
        content = item.content or item.title
        if not content or len(content) < 100:
            return content or item.title
        
        sentences = self._split_sentences(content)
        if len(sentences) <= 3:
            return content[:max_length]
        
        # 计算每句的重要性
        keywords = item.keywords
        scores = [
            (i, self._calculate_importance(s, item.title, keywords))
            for i, s in enumerate(sentences)
        ]
        
        if style == "1_sentence":
            # 选最重要的一句
            best_idx = max(scores, key=lambda x: x[1])[0]
            return sentences[best_idx][:200]
        
        elif style == "3_points":
            # 选最重要的 3 句
            top_indices = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
            top_indices.sort(key=lambda x: x[0])  # 按原文顺序
            points = [f"• {sentences[i]}" for i, _ in top_indices]
            return "\n".join(points)
        
        elif style == "paragraph":
            # 选前几句组成段落
            top_indices = sorted(scores, key=lambda x: x[1], reverse=True)[:5]
            top_indices.sort(key=lambda x: x[0])
            para = "".join(sentences[i] for i, _ in top_indices)
            return para[:max_length]
        
        else:  # detailed
            return content[:max_length]


class LLMSummarizer(Summarizer):
    """LLM 生成式摘要器"""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        try:
            from openai import AsyncOpenAI
            
            api_key = settings.openai_api_key
            if not api_key:
                return
            
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.openai_base_url or None
            )
            self.model = settings.openai_model
        except Exception as e:
            print(f"初始化 LLM 客户端失败: {e}")
            self.client = None
    
    async def summarize(
        self, 
        item: ContentItem, 
        style: str = "3_points",
        max_length: int = 500
    ) -> str:
        """使用 LLM 生成摘要"""
        if not self.client:
            # 降级到抽取式
            fallback = ExtractiveSummarizer()
            return await fallback.summarize(item, style, max_length)
        
        content = item.content or ""
        if len(content) > 8000:
            content = content[:8000] + "..."
        
        # 构建 Prompt
        prompt = self._build_prompt(item, style, max_length)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻摘要助手。请根据提供的内容生成简洁、准确的摘要。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"LLM 摘要生成失败: {e}")
            # 降级到抽取式
            fallback = ExtractiveSummarizer()
            return await fallback.summarize(item, style, max_length)
    
    def _build_prompt(self, item: ContentItem, style: str, max_length: int) -> str:
        """构建 Prompt"""
        
        style_instructions = {
            "1_sentence": "用一句话概括核心观点（50字以内）",
            "3_points": "提取3-5个关键要点，每个要点用一句话描述",
            "paragraph": "生成1-2段简短的总结（200字以内）",
            "detailed": "生成详细的摘要，保留关键细节（500字以内）"
        }
        
        instruction = style_instructions.get(style, style_instructions["3_points"])
        
        prompt = f"""标题：{item.title}
来源：{item.source}
关键词：{', '.join(item.keywords[:5])}

正文：
{item.content or '(无正文)'}

请根据以上内容生成摘要。要求：
{instruction}
- 保留关键事实和数据
- 语言简洁准确
- 直接输出摘要内容，不需要额外说明
"""
        return prompt
    
    async def batch_summarize(
        self, 
        items: List[ContentItem], 
        style: str = "3_points"
    ) -> List[str]:
        """
        批量生成摘要
        
        Args:
            items: 内容条目列表
            style: 摘要风格
            
        Returns:
            List[str]: 摘要列表
        """
        results = []
        for item in items:
            summary = await self.summarize(item, style)
            results.append(summary)
        return results


class SummarizerFactory:
    """摘要器工厂"""
    
    @staticmethod
    def create(use_llm: bool = True) -> Summarizer:
        """
        创建摘要器
        
        Args:
            use_llm: 是否使用 LLM
            
        Returns:
            Summarizer: 摘要器实例
        """
        if use_llm and settings.openai_api_key:
            return LLMSummarizer()
        return ExtractiveSummarizer()


class ContentProcessor:
    """内容处理器 - 整合清洗、提取、摘要"""
    
    def __init__(self, use_llm: bool = True):
        from src.processor.cleaner import ContentCleaner
        from src.processor.extractor import KeywordExtractor, EntityExtractor, TopicClassifier
        
        self.cleaner = ContentCleaner()
        self.keyword_extractor = KeywordExtractor()
        self.entity_extractor = EntityExtractor()
        self.topic_classifier = TopicClassifier()
        self.summarizer = SummarizerFactory.create(use_llm)
    
    async def process(self, item: ContentItem) -> ContentItem:
        """
        处理内容条目
        
        Args:
            item: 原始内容条目
            
        Returns:
            ContentItem: 处理后的内容条目
        """
        # 清洗内容
        if item.content:
            # 检测是否是 HTML
            if "<" in item.content and ">" in item.content:
                item.content = self.cleaner.clean(item.content)
            else:
                item.content = self.cleaner.clean_markdown(item.content)
        
        # 提取关键词
        if not item.keywords:
            item.keywords = self.keyword_extractor.extract(item)
        
        # 提取实体
        if not item.entities:
            item.entities = self.entity_extractor.extract(item)
        
        # 主题分类
        if not item.topics:
            item.topics = self.topic_classifier.classify(item)
        
        # 生成摘要
        if not item.summary:
            style = "3_points"
            item.summary = await self.summarizer.summarize(item, style=style)
        
        # 提取关键要点
        if not item.key_points:
            item.key_points = await self._extract_key_points(item)
        
        # 预估阅读时间
        if item.content and not item.read_time:
            word_count = len(item.content)
            item.read_time = max(1, word_count // 400)  # 假设 400 字/分钟
        
        return item
    
    async def _extract_key_points(self, item: ContentItem) -> List[str]:
        """提取关键要点"""
        summary = await self.summarizer.summarize(item, style="3_points")
        # 解析要点
        points = [p.strip().lstrip("•-・").strip() for p in summary.split("\n")]
        return [p for p in points if p and len(p) > 10]
    
    async def process_batch(self, items: List[ContentItem]) -> List[ContentItem]:
        """批量处理"""
        results = []
        for item in items:
            try:
                processed = await self.process(item)
                results.append(processed)
            except Exception as e:
                print(f"处理内容失败 {item.url}: {e}")
                results.append(item)
        return results
