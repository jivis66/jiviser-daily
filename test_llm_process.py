#!/usr/bin/env python3
"""
测试日报生成流程，验证 LLM 是否被正确调用
"""
import asyncio
import sys
sys.path.insert(0, '/Users/jivis/Project/jiviser-daily')

from src.service import DailyAgentService
from src.database import get_session, ContentRepository, ContentItemDB
from src.models import ContentItem, ContentStatus
from datetime import datetime, timezone


async def test_generate():
    """测试日报生成流程"""
    service = DailyAgentService()
    await service.initialize()
    
    print("\n" + "="*50)
    print("第一步：采集内容")
    print("="*50)
    
    # 只采集一次
    results = await service.collect_all()
    
    # 统计采集结果
    total_items = sum(len(r.items) for r in results.values() if r.success)
    print(f"\n采集完成，共 {total_items} 条内容")
    
    # 检查数据库中的内容
    async with get_session() as session:
        repo = ContentRepository(session)
        pending = await repo.get_by_status(ContentStatus.PENDING.value, limit=100)
        print(f"数据库中 pending 状态内容: {len(pending)} 条")
        
        if len(pending) == 0:
            print("⚠️ 没有待处理的内容，无法测试 LLM 处理")
            return
        
        # 显示前几条内容
        print("\n待处理内容列表:")
        for i, item in enumerate(pending[:5], 1):
            print(f"  {i}. [{item.source}] {item.title[:50]}...")
    
    print("\n" + "="*50)
    print("第二步：生成日报（包含 LLM 处理）")
    print("="*50)
    
    # 生成日报
    report = await service.generate_daily_report(user_id='default')
    
    print(f"\n✅ 日报生成完成!")
    print(f"   ID: {report.id}")
    print(f"   标题: {report.title}")
    print(f"   总条目: {report.total_items}")
    
    if report.total_items == 0:
        print("\n⚠️ 警告: 日报条目为 0，可能内容筛选有问题")
    else:
        print(f"\n📊 数据来源: {report.sources_count} 个")
        print(f"📊 主题数: {report.topics_count} 个")
    
    # 检查处理后的内容摘要
    print("\n" + "="*50)
    print("第三步：检查 LLM 处理结果")
    print("="*50)
    
    async with get_session() as session:
        repo = ContentRepository(session)
        selected = await repo.get_by_status(ContentStatus.SELECTED.value, limit=10)
        
        print(f"\n已选中内容: {len(selected)} 条")
        
        for i, item in enumerate(selected[:3], 1):
            print(f"\n  {i}. [{item.source}] {item.title[:50]}...")
            if item.summary:
                print(f"     摘要: {item.summary[:100]}...")
            else:
                print(f"     摘要: (无)")
            
            if item.keywords:
                print(f"     关键词: {item.keywords}")


if __name__ == "__main__":
    asyncio.run(test_generate())
