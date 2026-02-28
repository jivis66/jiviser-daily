#!/usr/bin/env python3
"""调试脚本 - 检查数据类型问题"""
import asyncio
from datetime import datetime, timezone

from src.database import get_session, ContentRepository, DailyReportRepository
from src.service import DailyAgentService
from src.config import get_column_config


async def debug_data():
    """检查数据类型"""
    service = DailyAgentService()
    
    columns = get_column_config().get_columns()
    print(f"分栏: {[col.get('id') for col in columns]}")
    
    async with get_session() as session:
        content_repo = ContentRepository(session)
        report_repo = DailyReportRepository(session)
        
        # 获取今天的日报
        today = datetime.now(timezone.utc)
        db_report = await report_repo.get_by_date("default", today)
        
        if db_report:
            print(f"\n日报: {db_report.id}")
            print(f"日期: {db_report.date}")
        
        # 获取各分栏内容
        for col in columns:
            col_id = col.get("id")
            items = await content_repo.get_by_column(
                column_id=col_id,
                date=today
            )
            print(f"\n分栏 '{col_id}': {len(items)} 条")
            
            for i, db_item in enumerate(items[:2]):  # 只检查前2条
                print(f"\n  第 {i+1} 条:")
                print(f"    ID: {db_item.id}")
                print(f"    标题: {db_item.title[:50]}...")
                print(f"    key_points 类型: {type(db_item.key_points)}, 值: {db_item.key_points}")
                print(f"    topics 类型: {type(db_item.topics)}, 值: {db_item.topics}")
                print(f"    keywords 类型: {type(db_item.keywords)}, 值: {db_item.keywords}")
                
                # 转换为 ContentItem
                item = service._from_db_item(db_item)
                print(f"    转换后 key_points 类型: {type(item.key_points)}, 值: {item.key_points[:3] if item.key_points else []}")
                print(f"    转换后 topics 类型: {type(item.topics)}, 值: {item.topics}")


if __name__ == "__main__":
    asyncio.run(debug_data())
