#!/usr/bin/env python3
"""
性能诊断脚本
用于找出 LLM 处理中的阻塞点
"""
import asyncio
import time
import sys
from datetime import datetime, timezone

# 测试不同的处理环节


async def test_jieba_blocking():
    """测试 jieba 是否阻塞"""
    print("\n" + "="*60)
    print("测试 1: jieba 分词是否阻塞事件循环")
    print("="*60)
    
    import jieba
    
    text = "这是一个测试文本。" * 1000  # 长文本
    
    async def async_task(name, delay):
        """模拟异步任务"""
        await asyncio.sleep(delay)
        print(f"  [{name}] 完成 (预期在 {delay}s)")
    
    print("\n同步执行 jieba.cut（会阻塞）:")
    start = time.time()
    
    # 启动一个定时任务
    task = asyncio.create_task(async_task("后台任务", 0.1))
    
    # 同步执行 jieba
    result = list(jieba.cut(text))
    
    elapsed = time.time() - start
    print(f"jieba.cut 耗时: {elapsed:.3f}s, 分词数: {len(result)}")
    
    # 检查后台任务是否被延迟
    if not task.done():
        print("警告: 后台任务被阻塞！")
        await task
    else:
        print("后台任务正常执行")
    
    print("\n异步执行 jieba.cut（使用线程池）:")
    start = time.time()
    
    task = asyncio.create_task(async_task("后台任务", 0.1))
    
    # 在线程池中执行
    result = await asyncio.to_thread(lambda: list(jieba.cut(text)))
    
    elapsed = time.time() - start
    print(f"jieba.cut (线程池) 耗时: {elapsed:.3f}s, 分词数: {len(result)}")
    
    if not task.done():
        print("警告: 后台任务被阻塞！")
        await task
    else:
        print("后台任务正常执行")


async def test_extractor_performance():
    """测试提取器性能"""
    print("\n" + "="*60)
    print("测试 2: 关键词提取器性能")
    print("="*60)
    
    from src.models import ContentItem, SourceType
    from src.processor.extractor import KeywordExtractor
    
    extractor = KeywordExtractor()
    
    item = ContentItem(
        id="test_1",
        title="OpenAI 发布 GPT-5，性能提升 10 倍，支持多模态",
        url="https://example.com/1",
        source="TechNews",
        source_type=SourceType.ARTICLE,
        content="""OpenAI 今日正式发布 GPT-5，新一代大语言模型在多项基准测试中表现出色。
据官方介绍，GPT-5 参数量达到 10 万亿，相比 GPT-4 提升了 5 倍。
新模型不仅能更好地理解上下文，还具备了多模态能力。""" * 50,  # 长内容
        keywords=[]
    )
    
    print("异步提取关键词...")
    start = time.time()
    keywords = await extractor.extract(item, top_k=10)
    elapsed = time.time() - start
    print(f"提取完成: {elapsed:.3f}s, 关键词: {keywords}")


async def test_llm_api_latency():
    """测试 LLM API 延迟"""
    print("\n" + "="*60)
    print("测试 3: LLM API 延迟测试")
    print("="*60)
    
    from src.config import get_settings
    from src.processor.batch_llm import BatchLLMProcessor
    
    settings = get_settings()
    
    if not settings.llm_api_key and not settings.openai_api_key:
        print("跳过: 未配置 LLM API Key")
        return
    
    processor = BatchLLMProcessor()
    
    if not processor.client:
        print("错误: LLM 客户端初始化失败")
        return
    
    print(f"模型: {processor.model}")
    print("测试单条 API 调用延迟...")
    
    import openai
    
    start = time.time()
    try:
        response = await processor.client.chat.completions.create(
            model=processor.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, respond with 'OK' only."}
            ],
            max_tokens=10
        )
        elapsed = time.time() - start
        print(f"单条 API 调用耗时: {elapsed:.3f}s")
        print(f"响应: {response.choices[0].message.content}")
    except Exception as e:
        print(f"API 调用失败: {e}")


async def test_full_pipeline():
    """测试完整处理流程，找出瓶颈"""
    print("\n" + "="*60)
    print("测试 4: 完整处理流程分析")
    print("="*60)
    
    from src.models import ContentItem, SourceType
    from src.processor.summarizer import ContentProcessor
    
    # 创建测试数据
    items = []
    for i in range(5):
        item = ContentItem(
            id=f"test_{i}",
            title=f"测试文章 {i}: AI 技术新突破",
            url=f"https://example.com/{i}",
            source="TechNews",
            source_type=SourceType.ARTICLE,
            content="人工智能技术在近年来取得了突破性进展。" * 100,
            keywords=[],
            entities=[],
            topics=[]
        )
        items.append(item)
    
    processor = ContentProcessor(use_llm=True, max_concurrency=5, enable_cache=False)
    
    print(f"\n处理 {len(items)} 条内容...")
    
    # 记录每个阶段的时间
    stage_times = {}
    
    # 阶段 1: 清洗
    start = time.time()
    for item in items:
        if item.content:
            if "<" in item.content and ">" in item.content:
                item.content = processor.cleaner.clean(item.content)
            else:
                item.content = processor.cleaner.clean_markdown(item.content)
    stage_times['clean'] = time.time() - start
    
    # 阶段 2: 关键词提取（异步）
    start = time.time()
    for item in items:
        item.keywords = await processor.keyword_extractor.extract(item)
    stage_times['keywords'] = time.time() - start
    
    # 阶段 3: 实体提取
    start = time.time()
    for item in items:
        item.entities = processor.entity_extractor.extract(item)
    stage_times['entities'] = time.time() - start
    
    # 阶段 4: 主题分类
    start = time.time()
    for item in items:
        item.topics = processor.topic_classifier.classify(item)
    stage_times['topics'] = time.time() - start
    
    # 阶段 5: LLM 摘要
    start = time.time()
    for item in items:
        item.summary = await processor.summarizer.summarize(item)
    stage_times['llm_summary'] = time.time() - start
    
    # 打印结果
    print("\n各阶段耗时:")
    for stage, t in stage_times.items():
        print(f"  {stage}: {t:.3f}s ({t/len(items):.3f}s/条)")
    
    total = sum(stage_times.values())
    print(f"\n总计: {total:.3f}s, 平均: {total/len(items):.3f}s/条")
    
    # 找出最慢的阶段
    slowest = max(stage_times.items(), key=lambda x: x[1])
    print(f"\n最慢的阶段: {slowest[0]} ({slowest[1]:.3f}s)")


async def test_concurrency():
    """测试并发处理"""
    print("\n" + "="*60)
    print("测试 5: 并发处理测试")
    print("="*60)
    
    from src.models import ContentItem, SourceType
    from src.processor.summarizer import LLMSummarizer
    
    items = []
    for i in range(10):
        item = ContentItem(
            id=f"test_{i}",
            title=f"测试文章 {i}",
            url=f"https://example.com/{i}",
            source="TechNews",
            source_type=SourceType.ARTICLE,
            content="简短内容",
            keywords=[]
        )
        items.append(item)
    
    # 测试不同并发数
    for concurrency in [1, 3, 5]:
        print(f"\n并发数: {concurrency}")
        summarizer = LLMSummarizer(max_concurrency=concurrency)
        
        if not summarizer.client:
            print("跳过: LLM 未配置")
            continue
        
        start = time.time()
        results = await summarizer.batch_summarize(items[:5], use_batch_api=False)
        elapsed = time.time() - start
        
        print(f"  处理 5 条耗时: {elapsed:.3f}s, 平均: {elapsed/5:.3f}s/条")


async def main():
    """主函数"""
    print("性能诊断工具")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 版本: {sys.version}")
    
    try:
        await test_jieba_blocking()
        await test_extractor_performance()
        await test_llm_api_latency()
        await test_full_pipeline()
        await test_concurrency()
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)
    print("\n优化建议:")
    print("1. 如果 jieba 阻塞严重，考虑使用更轻量的分词方案")
    print("2. 如果 LLM API 延迟高，考虑更换模型或服务商")
    print("3. 如果某个阶段特别慢，考虑跳过或简化")


if __name__ == "__main__":
    asyncio.run(main())
