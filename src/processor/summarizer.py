"""
摘要生成模块
支持抽取式和生成式摘要
优化版本：支持批量处理和并发控制，避免阻塞操作
"""
import asyncio
import re
from abc import ABC, abstractmethod
from typing import List, Optional, ClassVar, Any

import httpx
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
        pass
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        sentences = re.split(r"(?<=[。．.!?！？])\s*", text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _calculate_importance_async(self, sentence: str, title: str, keywords: List[str]) -> float:
        """异步计算句子重要性（避免 jieba 阻塞）"""
        score = 0.0
        sentence_lower = sentence.lower()
        
        # 关键词匹配
        for kw in keywords:
            if kw.lower() in sentence_lower:
                score += 1.0
        
        # 标题词匹配（在线程池中执行 jieba）
        def _calc_title_match():
            title_words = set(jieba.lcut(title.lower()))
            sentence_words = set(jieba.lcut(sentence_lower))
            common_words = title_words & sentence_words
            return len(common_words) * 0.5
        
        # 只在需要时调用 jieba
        if title and sentence:
            score += await asyncio.to_thread(_calc_title_match)
        
        return score


class ExtractiveSummarizer(Summarizer):
    """抽取式摘要器（本地处理，无需 LLM）"""
    
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
        
        # 异步计算每句的重要性
        keywords = item.keywords or []
        scores = []
        for i, s in enumerate(sentences):
            score = await self._calculate_importance_async(s, item.title, keywords)
            scores.append((i, score))
        
        if style == "1_sentence":
            best_idx = max(scores, key=lambda x: x[1])[0]
            return sentences[best_idx][:200]
        
        elif style == "3_points":
            top_indices = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
            top_indices.sort(key=lambda x: x[0])
            points = [f"• {sentences[i]}" for i, _ in top_indices]
            return "\n".join(points)
        
        elif style == "paragraph":
            top_indices = sorted(scores, key=lambda x: x[1], reverse=True)[:5]
            top_indices.sort(key=lambda x: x[0])
            para = "".join(sentences[i] for i, _ in top_indices)
            return para[:max_length]
        
        else:
            return content[:max_length]


class LLMSummarizer(Summarizer):
    """
    LLM 生成式摘要器（优化版）
    优化特性：
    - 类级别客户端缓存
    - 连接池复用 HTTP 连接
    - 支持并发批量处理
    - 智能降级机制
    """
    
    _client_cache: ClassVar[Optional[Any]] = None
    _model_cache: ClassVar[Optional[str]] = None
    _init_error: ClassVar[Optional[str]] = None
    
    DEFAULT_CONCURRENCY = 5
    TIMEOUT = 30.0
    
    def __init__(self, max_concurrency: int = None):
        self.semaphore = asyncio.Semaphore(max_concurrency or self.DEFAULT_CONCURRENCY)
        self.max_concurrency = max_concurrency or self.DEFAULT_CONCURRENCY
    
    @classmethod
    def _get_cached_client(cls):
        """获取缓存的客户端（类级别单例）"""
        if cls._client_cache is not None:
            return cls._client_cache, cls._model_cache
        
        if cls._init_error is not None:
            return None, None
        
        try:
            from openai import AsyncOpenAI
            
            api_key = settings.llm_api_key or settings.openai_api_key
            base_url = settings.llm_base_url or settings.openai_base_url
            model = settings.llm_model or settings.openai_model
            
            if not api_key:
                cls._init_error = "未配置 API Key"
                return None, None
            
            http_client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=50
                ),
                timeout=httpx.Timeout(cls.TIMEOUT, connect=10.0)
            )
            
            cls._client_cache = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url or None,
                http_client=http_client
            )
            cls._model_cache = model
            
            print(f"[LLMSummarizer] 客户端初始化成功，模型: {model}")
            
        except Exception as e:
            cls._init_error = str(e)
            print(f"[LLMSummarizer] 初始化失败: {e}")
            return None, None
        
        return cls._client_cache, cls._model_cache
    
    @property
    def client(self):
        client, _ = self._get_cached_client()
        return client
    
    @property
    def model(self):
        _, model = self._get_cached_client()
        return model
    
    async def summarize(
        self, 
        item: ContentItem, 
        style: str = "3_points",
        max_length: int = 500
    ) -> str:
        """使用 LLM 生成摘要（带并发控制）"""
        if not self.client:
            fallback = ExtractiveSummarizer()
            return await fallback.summarize(item, style, max_length)
        
        async with self.semaphore:
            return await self._summarize_single(item, style, max_length)
    
    async def _summarize_single(
        self, 
        item: ContentItem, 
        style: str = "3_points",
        max_length: int = 500
    ) -> str:
        """单个摘要生成"""
        import time
        start = time.time()
        
        content = item.content or ""
        if len(content) > 8000:
            content = content[:8000] + "..."
        
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
            
            elapsed = time.time() - start
            if elapsed > 5:
                print(f"[LLMSummarizer] 单条处理耗时: {elapsed:.1f}s - {item.title[:50]}...")
            
            return summary
            
        except asyncio.TimeoutError:
            print(f"[LLMSummarizer] 超时: {item.title[:50]}...")
            fallback = ExtractiveSummarizer()
            return await fallback.summarize(item, style, max_length)
            
        except Exception as e:
            print(f"[LLMSummarizer] 失败: {e}")
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
关键词：{', '.join(item.keywords[:5] if item.keywords else [])}

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
        style: str = "3_points",
        max_concurrency: int = None,
        use_batch_api: bool = True
    ) -> List[str]:
        """批量生成摘要"""
        if not items:
            return []
        
        if not self.client:
            fallback = ExtractiveSummarizer()
            results = []
            for item in items:
                summary = await fallback.summarize(item, style)
                results.append(summary)
            return results
        
        # 尝试使用批量处理器
        if use_batch_api and len(items) > 1:
            try:
                from src.processor.batch_llm import BatchLLMProcessor
                
                batch_processor = BatchLLMProcessor()
                if batch_processor.client:
                    print(f"[LLMSummarizer] 使用批量处理模式，共 {len(items)} 条内容")
                    results = await batch_processor.smart_batch_process(items, style)
                    
                    if results and len(results) == len(items):
                        for item, (summary, key_points) in zip(items, results):
                            item.summary = summary
                            item.key_points = key_points
                        
                        return [r[0] for r in results]
                    
                    print(f"[LLMSummarizer] 批量处理未返回完整结果，降级到并发模式")
            except Exception as e:
                print(f"[LLMSummarizer] 批量处理失败: {e}，降级到并发模式")
        
        # 并发模式
        print(f"[LLMSummarizer] 使用并发处理模式，共 {len(items)} 条内容")
        
        semaphore = asyncio.Semaphore(max_concurrency or self.DEFAULT_CONCURRENCY)
        
        async def _summarize_with_semaphore(item):
            async with semaphore:
                return await self._summarize_single(item, style)
        
        tasks = [_summarize_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        summaries = []
        fallback = ExtractiveSummarizer()
        
        for item, result in zip(items, results):
            if isinstance(result, Exception):
                print(f"摘要生成失败，使用抽取式降级: {item.title[:50]}... ({result})")
                summary = await fallback.summarize(item, style)
                summaries.append(summary)
            else:
                summaries.append(result)
        
        return summaries


class SummarizerFactory:
    """摘要器工厂"""
    
    @staticmethod
    def create(use_llm: bool = True, max_concurrency: int = None) -> Summarizer:
        has_api_key = settings.llm_api_key or settings.openai_api_key
        if use_llm and has_api_key:
            return LLMSummarizer(max_concurrency=max_concurrency)
        return ExtractiveSummarizer()


class ContentProcessor:
    """
    内容处理器 - 整合清洗、提取、摘要
    优化版本：支持批量并行处理 + 缓存，避免阻塞操作
    
    使用快速模式跳过非必要的处理步骤：
    - 不提取实体
    - 不分类主题
    - 简化关键词提取
    """
    
    DEFAULT_CONCURRENCY = 5
    
    def __init__(self, use_llm: bool = True, max_concurrency: int = None, enable_cache: bool = True, fast_mode: bool = True):
        from src.processor.cleaner import ContentCleaner
        from src.processor.extractor import KeywordExtractor, EntityExtractor, TopicClassifier
        from src.processor.cache import get_processing_cache
        
        self.cleaner = ContentCleaner()
        self.keyword_extractor = KeywordExtractor()
        self.entity_extractor = EntityExtractor()
        self.topic_classifier = TopicClassifier()
        
        concurrency = max_concurrency or self.DEFAULT_CONCURRENCY
        self.summarizer = SummarizerFactory.create(use_llm, max_concurrency=concurrency)
        self.max_concurrency = concurrency
        
        self.cache = get_processing_cache() if enable_cache else None
        self.enable_cache = enable_cache
        self.fast_mode = fast_mode
    
    async def process(self, item: ContentItem) -> ContentItem:
        """处理内容条目"""
        # 清洗内容
        if item.content:
            if "<" in item.content and ">" in item.content:
                item.content = self.cleaner.clean(item.content)
            else:
                item.content = self.cleaner.clean_markdown(item.content)
        
        # 提取关键词（异步）
        if not item.keywords:
            item.keywords = await self.keyword_extractor.extract(item)
        
        # 提取实体（同步，很快）
        if not item.entities:
            item.entities = self.entity_extractor.extract(item)
        
        # 主题分类（同步，很快）
        if not item.topics:
            item.topics = self.topic_classifier.classify(item)
        
        # 生成摘要（异步）
        if not item.summary:
            style = "3_points"
            item.summary = await self.summarizer.summarize(item, style=style)
        
        # 提取关键要点
        if not item.key_points:
            item.key_points = await self._extract_key_points(item)
        
        # 预估阅读时间
        if item.content and not item.read_time:
            word_count = len(item.content)
            item.read_time = max(1, word_count // 400)
        
        return item
    
    async def _extract_key_points(self, item: ContentItem) -> List[str]:
        """提取关键要点"""
        summary = await self.summarizer.summarize(item, style="3_points")
        points = [p.strip().lstrip("•-・").strip() for p in summary.split("\n")]
        return [p for p in points if p and len(p) > 10]
    
    async def process_batch(
        self, 
        items: List[ContentItem],
        progress_callback: callable = None
    ) -> List[ContentItem]:
        """批量处理（优化版 - 并行处理）"""
        if not items:
            return []
        
        import time
        total_start = time.time()
        
        # 第一步：并行预处理
        pre_start = time.time()
        preprocessed_items = await self._preprocess_batch(items, progress_callback)
        pre_time = time.time() - pre_start
        
        # 第二步：批量生成摘要
        llm_start = time.time()
        if isinstance(self.summarizer, LLMSummarizer):
            await self._batch_summarize_items(preprocessed_items, progress_callback)
        llm_time = time.time() - llm_start
        
        total_time = time.time() - total_start
        print(f"[ContentProcessor] 批量处理完成: {len(items)} 条, "
              f"总耗时: {total_time:.1f}s (预处理: {pre_time:.1f}s, LLM: {llm_time:.1f}s)")
        
        return preprocessed_items
    
    async def _preprocess_batch(
        self, 
        items: List[ContentItem],
        progress_callback: callable = None
    ) -> List[ContentItem]:
        """批量预处理（异步化，支持快速模式）"""
        processed = []
        total = len(items)
        
        for i, item in enumerate(items):
            try:
                # 清洗内容（必要）
                if item.content:
                    if "<" in item.content and ">" in item.content:
                        item.content = self.cleaner.clean(item.content)
                    else:
                        item.content = self.cleaner.clean_markdown(item.content)
                
                # 快速模式：跳过实体提取和主题分类，简化关键词提取
                if self.fast_mode:
                    # 只提取简单的关键词（从标题中）
                    if not item.keywords and item.title:
                        # 简单的关键词提取：从标题中提取名词
                        import re
                        words = re.findall(r'[A-Za-z]+|[\u4e00-\u9fff]{2,}', item.title)
                        item.keywords = [w for w in words if len(w) > 1][:5]
                    
                    # 跳过实体和主题
                    item.entities = item.entities or []
                    item.topics = item.topics or []
                else:
                    # 完整模式：异步提取关键词
                    if not item.keywords:
                        item.keywords = await self.keyword_extractor.extract(item)
                    
                    # 提取实体
                    if not item.entities:
                        item.entities = self.entity_extractor.extract(item)
                    
                    # 主题分类
                    if not item.topics:
                        item.topics = self.topic_classifier.classify(item)
                
                # 预估阅读时间
                if item.content and not item.read_time:
                    word_count = len(item.content)
                    item.read_time = max(1, word_count // 400)
                
                processed.append(item)
                
                if progress_callback and (i + 1) % 10 == 0:
                    progress_callback(i + 1, total, f"预处理 {i + 1}/{total}")
                    
            except Exception as e:
                print(f"预处理失败 {item.url}: {e}")
                processed.append(item)
        
        return processed
    
    async def _batch_summarize_items(
        self, 
        items: List[ContentItem],
        progress_callback: callable = None
    ):
        """批量生成摘要（带缓存和批量 LLM 模式）"""
        items_needing_summary = []
        cached_count = 0
        
        for item in items:
            if self.enable_cache and self.cache:
                cache_entry = self.cache.get(item)
                if cache_entry:
                    self.cache.apply_to_item(item, cache_entry)
                    cached_count += 1
                    continue
            
            if not item.summary or not item.key_points:
                items_needing_summary.append(item)
        
        if cached_count > 0:
            print(f"[ContentProcessor] 缓存命中: {cached_count} 条")
        
        if not items_needing_summary:
            return
        
        total = len(items_needing_summary)
        print(f"[ContentProcessor] 批量生成摘要: {total} 条内容")
        
        from src.config import get_settings
        settings = get_settings()
        use_batch_mode = settings.llm_batch_mode
        
        if use_batch_mode and isinstance(self.summarizer, LLMSummarizer):
            summaries = await self.summarizer.batch_summarize(
                items_needing_summary, 
                style="3_points",
                max_concurrency=self.max_concurrency,
                use_batch_api=True
            )
        else:
            summaries = await self.summarizer.batch_summarize(
                items_needing_summary, 
                style="3_points",
                max_concurrency=self.max_concurrency,
                use_batch_api=False
            )
        
        for item, summary in zip(items_needing_summary, summaries):
            if not item.summary:
                item.summary = summary
            if not item.key_points:
                points = [p.strip().lstrip("•-・").strip() for p in summary.split("\n")]
                item.key_points = [p for p in points if p and len(p) > 10]
            
            if self.enable_cache and self.cache:
                self.cache.set(
                    item,
                    summary=item.summary,
                    key_points=item.key_points,
                    keywords=item.keywords,
                    entities=item.entities,
                    topics=item.topics
                )
            
            if progress_callback:
                idx = items_needing_summary.index(item) + 1
                progress_callback(idx, total, f"生成摘要 {idx}/{total}")
        
        if self.enable_cache and self.cache:
            stats = self.cache.get_stats()
            print(f"[ContentProcessor] 缓存统计: 命中率 {stats['hit_rate']}, 大小 {stats['size']}")
