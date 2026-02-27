"""
命令行工具
"""
import asyncio
import os
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def cli():
    """Daily Agent CLI"""
    pass


@cli.command()
@click.option("--user", "-u", default="default", help="用户 ID")
@click.option("--date", "-d", help="日期 (YYYY-MM-DD)")
def generate(user: str, date: str = None):
    """生成日报"""
    async def _generate():
        from src.service import DailyAgentService
        
        service = DailyAgentService()
        await service.initialize()
        
        dt = datetime.strptime(date, "%Y-%m-%d") if date else None
        report = await service.generate_daily_report(user_id=user, date=dt)
        
        console.print(f"[green]日报生成成功:[/green] {report.id}")
        console.print(f"  总条目: {report.total_items}")
    
    asyncio.run(_generate())


@cli.command()
@click.argument("report_id")
@click.option("--channel", "-c", multiple=True, help="推送渠道")
def push(report_id: str, channel: tuple):
    """推送日报"""
    async def _push():
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.database import get_session, DailyReportRepository
        from src.models import DailyReport
        from src.service import DailyAgentService
        
        service = DailyAgentService()
        await service.initialize()
        
        async for session in get_session():
            repo = DailyReportRepository(session)
            db_report = await repo.get_by_id(report_id)
            
            if not db_report:
                console.print(f"[red]日报不存在: {report_id}[/red]")
                return
            
            report = DailyReport(
                id=db_report.id,
                date=db_report.date,
                user_id=db_report.user_id,
                title=db_report.title,
                total_items=db_report.total_items
            )
            
            channels = list(channel) if channel else None
            results = await service.push_report(report, channels)
            
            for ch, result in results.items():
                status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
                console.print(f"{status} {ch}: {result.message}")
            
            break
    
    asyncio.run(_push())


@cli.command()
def collect():
    """手动触发采集"""
    async def _collect():
        from src.service import DailyAgentService
        
        service = DailyAgentService()
        await service.initialize()
        
        results = await service.collect_all()
        
        table = Table(title="采集结果")
        table.add_column("来源", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("数量", justify="right")
        table.add_column("消息")
        
        for name, result in results.items():
            status = "✓" if result.success else "✗"
            table.add_row(
                name,
                status,
                str(len(result.items)),
                result.message[:50]
            )
        
        console.print(table)
    
    asyncio.run(_collect())


@cli.command()
def verify():
    """验证配置"""
    from src.config import get_settings, get_column_config
    
    settings = get_settings()
    col_config = get_column_config()
    
    console.print("[bold]配置验证[/bold]\n")
    
    # 检查 LLM
    llm_status = "✓" if settings.openai_api_key else "✗"
    console.print(f"{llm_status} LLM 配置: {'已配置' if settings.openai_api_key else '未配置'}")
    
    # 检查推送渠道
    channels = []
    if settings.telegram_bot_token:
        channels.append("Telegram")
    if settings.slack_bot_token:
        channels.append("Slack")
    if settings.discord_bot_token:
        channels.append("Discord")
    
    if channels:
        console.print(f"✓ 推送渠道: {', '.join(channels)}")
    else:
        console.print("✗ 推送渠道: 未配置")
    
    # 检查分栏配置
    try:
        columns = col_config.get_columns()
        console.print(f"✓ 分栏配置: {len(columns)} 个分栏")
        for col in columns:
            console.print(f"  • {col.get('name')} ({len(col.get('sources', []))} 个源)")
    except Exception as e:
        console.print(f"✗ 分栏配置错误: {e}")


@cli.command()
def init():
    """初始化数据库"""
    async def _init():
        from src.database import init_db
        await init_db()
        console.print("[green]数据库初始化完成[/green]")
    
    asyncio.run(_init())


if __name__ == "__main__":
    cli()
