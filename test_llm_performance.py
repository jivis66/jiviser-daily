#!/usr/bin/env python3
"""
测试 LLM 处理性能
"""
import asyncio
import time
from datetime import datetime, timezone

from src.models import ContentItem, SourceType
from src.processor.summarizer import ContentProcessor, LLMSummarizer, BatchLLMProcessor


# 创建测试数据
def create_test_items(count: int = 10) -> list:
    """创建测试内容"""
    items = []
    for i in range(count):
        item = ContentItem(
            id=f"test_{i}",
            title=f"测试文章 {i}: OpenAI 发布 GPT-5，性能提升 10 倍",
            url=f"https://example.com/article/{i}",
            source="TechNews",
            source_type=SourceType.ARTICLE,
            content="""OpenAI 今日正式发布 GPT-5，新一代大语言模型在多项基准测试中表现出色。

据官方介绍，GPT-5 参数量达到 10 万亿，相比 GPT-4 提升了 5 倍。在 MMLU 基准测试中，
GPT-5 达到了 95% 的准确率，超越了人类专家水平。

"GPT-5 不仅能更好地理解上下文，还具备了多模态能力，可以同时处理文本、图像和音频。"
OpenAI CEO Sam Altman 在发布会上表示。

新模型的主要特点包括：
1. 推理能力显著提升，可以解决更复杂的数学问题
2. 代码生成准确率提高，支持更多编程语言
3. 上下文长度扩展到 100 万 token
4. 响应速度比 GPT-4 快 2 倍

目前 GPT-5 已向 ChatGPT Plus 用户开放，API 价格与 GPT-4 持平。
开发者可以通过 OpenAI API 接入新模型。

业内专家认为，GPT-5 的发布将进一步推动 AI 应用的普及，
特别是在教育、医疗、金融等领域的应用将迎来新的突破。

不过也有研究人员提醒，随着模型能力增强，AI 安全问题也变得更加重要。
OpenAI 表示已经加强了安全评估，确保模型不会被滥用。

接下来，OpenAI 计划推出 GPT-5 的企业版，提供更多定制化功能。
同时，他们也在研发 GPT-6，预计将在 2025 年发布。
""",
            author=f"作者 {i}",
            publish_time=datetime.now(timezone.utc),
            keywords=["OpenAI", "GPT-5", "AI", "大模型"]
        )
        items.append(item)
    return items


async def test_single_processing():
    """测试单条处理速度"""
    print("\n" + "="*60)
    print("测试 1: 单条处理模式（逐条调用 LLM）")
    print("="*60)
    
    items = create_test_items(5)
    processor = ContentProcessor(use_llm=True, max_concurrency=1, enable_cache=False)
    
    start = time.time()
    
    for i, item in enumerate(items):
        item_start = time.time()
        await processor.summarizer.summarize(item)
        item_time = time.time() - item_start
        print(f"  第 {i+1} 条: {item_time:.2f}s")
    
    total_time = time.time() - start
    print(f"\n总计: {len(items)} 条, 耗时: {total_time:.2f}s, 平均: {total_time/len(items):.2f}s/条")


async def test_concurrent_processing():
    """测试并发处理速度"""
    print("\n" + "="*60)
    print("测试 2: 并发处理模式（5 并发）")
    print("="*60)
    
    items = create_test_items(10)
    summarizer = LLMSummarizer(max_concurrency=5)
    
    start = time.time()
    results = await summarizer.batch_summarize(items, use_batch_api=False)
    total_time = time.time() - start
    
    print(f"总计: {len(items)} 条, 耗时: {total_time:.2f}s, 平均: {total_time/len(items):.2f}s/条")


async def test_batch_processing():
    """测试批量处理速度（单次调用）"""
    print("\n" + "="*60)
    print("测试 3: 批量处理模式（单次 LLM 调用）")
    print("="*60)
    
    items = create_test_items(10)
    processor = BatchLLMProcessor()
    
    if not processor.client:
        print("LLM 未配置，跳过测试")
        return
    
    start = time.time()
    results = await processor.batch_process(items)
    total_time = time.time() - start
    
    print(f"总计: {len(items)} 条, 耗时: {total_time:.2f}s, 平均: {total_time/len(items):.2f}s/条")
    
    # 测试更大批量
    print("\n测试 3b: 批量处理 30 条")
    items_30 = create_test_items(30)
    start = time.time()
    results = await processor.batch_process(items_30)
    total_time = time.time() - start
    print(f"总计: {len(items_30)} 条, 耗时: {total_time:.2f}s, 平均: {total_time/len(items_30):.2f}s/条")


async def test_full_pipeline():
    """测试完整处理流程"""
    print("\n" + "="*60)
    print("测试 4: 完整处理流程（预处理 + LLM 摘要）")
    print("="*60)
    
    items = create_test_items(20)
    processor = ContentProcessor(use_llm=True, max_concurrency=5, enable_cache=False)
    
    print(f"开始处理 {len(items)} 条内容...")
    start = time.time()
    
    def progress_callback(processed, total, message):
        print(f"  进度: {processed}/{total} - {message}")
    
    results = await processor.process_batch(items, progress_callback=progress_callback)
    
    total_time = time.time() - start
    print(f"\n总计: {len(items)} 条, 耗时: {total_time:.2f}s, 平均: {total_time/len(items):.2f}s/条")


async def test_client_reuse():
    """测试客户端复用"""
    print("\n" + "="*60)
    print("测试 5: 客户端复用测试（创建多个实例）")
    print("="*60)
    
    start = time.time()
    
    # 创建多个 BatchLLMProcessor 实例
    processors = []
    for i in range(5):
        p = BatchLLMProcessor()
        processors.append(p)
    
    create_time = time.time() - start
    print(f"创建 5 个实例耗时: {create_time:.3f}s")
    
    # 检查是否是同一个客户端
    clients = [p.client for p in processors]
    same_client = all(c is clients[0] for c in clients)
    print(f"客户端是否复用: {same_client}")
    
    # 测试处理速度
    items = create_test_items(5)
    start = time.time()
    
    # 使用第一个处理器
    results = await processors[0].batch_process(items)
    
    process_time = time.time() - start
    print(f"处理 5 条耗时: {process_time:.2f}s")


async def main():
    """主函数"""
    print("LLM 性能测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查配置
    from src.config import get_settings
    settings = get_settings()
    
    if not settings.llm_api_key and not settings.openai_api_key:
        print("\n警告: 未配置 LLM API Key，请先配置环境变量")
        print("设置 LLM_API_KEY 或 OPENAI_API_KEY")
        return
    
    print(f"\n配置信息:")
    print(f"  模型: {settings.llm_model or settings.openai_model}")
    print(f"  API Base: {settings.llm_base_url or settings.openai_base_url or 'default'}")
    
    try:
        # 运行测试
        await test_client_reuse()
        await test_single_processing()
        await test_concurrent_processing()
        await test_batch_processing()
        await test_full_pipeline()
        
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
