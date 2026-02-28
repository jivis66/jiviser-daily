#!/usr/bin/env python3
"""
测试中国信息源采集器
"""
import asyncio
from rich.console import Console
from rich.table import Table

console = Console()


async def test_collector(collector_class, name, config):
    """测试单个采集器"""
    try:
        collector = collector_class(name, config)
        result = await collector.collect()
        await collector.close()
        return result
    except Exception as e:
        from src.collector import CollectorResult
        result = CollectorResult()
        result.success = False
        result.message = f"异常: {e}"
        return result


async def main():
    """测试所有中国信息源"""
    console.print("[bold blue]测试中国信息源采集器[/bold blue]\n")

    from src.collector import (
        # 科技媒体
        JuejinCollector, OschinaCollector, InfoqChinaCollector,
        SegmentFaultCollector, CSDNCollector,
        # 商业媒体
        HuxiuCollector, LeiphoneCollector, PingWestCollector,
        GeekParkCollector, SinaTechCollector, NetEaseTechCollector,
        # 社区
        V2EXCollector, XueqiuCollector, WallstreetCnCollector,
        RuanYifengBlogCollector, ITPubCollector, ChinaUnixCollector,
    )

    # 测试配置
    tests = [
        # 科技媒体
        (JuejinCollector, "稀土掘金", {"category": "all", "limit": 5}),
        (OschinaCollector, "开源中国", {"feed_type": "news"}),
        (InfoqChinaCollector, "InfoQ中文", {"category": "ai-ml"}),
        (SegmentFaultCollector, "思否", {"tag": "python", "limit": 5}),
        (CSDNCollector, "CSDN", {"category": "hot"}),

        # 商业媒体
        (HuxiuCollector, "虎嗅", {"feed_type": "all"}),
        (LeiphoneCollector, "雷锋网", {"category": "ai"}),
        (PingWestCollector, "品玩", {}),
        (GeekParkCollector, "极客公园", {}),
        (SinaTechCollector, "新浪科技", {}),
        (NetEaseTechCollector, "网易科技", {}),

        # 社区
        (V2EXCollector, "V2EX", {"node": "python", "limit": 5}),
        (XueqiuCollector, "雪球", {"category": "hot", "limit": 5}),
        (WallstreetCnCollector, "华尔街见闻", {"category": "hot"}),
        (RuanYifengBlogCollector, "阮一峰", {}),
        (ITPubCollector, "ITPUB", {"category": "hot"}),
        (ChinaUnixCollector, "ChinaUnix", {}),
    ]

    # 执行测试
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("信息源", style="cyan", width=20)
    table.add_column("状态", width=8)
    table.add_column("数量", justify="right", width=6)
    table.add_column("消息", style="dim")

    for collector_class, name, config in tests:
        result = await test_collector(collector_class, name, config)

        status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
        count = str(len(result.items)) if result.success else "0"
        message = result.message[:50] + "..." if len(result.message) > 50 else result.message

        table.add_row(name, status, count, message)

    console.print(table)

    # 统计
    total_count = len(tests)

    console.print(f"\n[bold]总计: {total_count} 个采集器已测试[/bold]")
    console.print("[dim]注: 部分RSS源可能需要特殊的用户代理或已失效[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
