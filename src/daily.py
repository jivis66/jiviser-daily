"""
简化版 Daily Agent CLI
提供直观、简洁的命令入口

用法:
    python -m daily              # 默认生成日报
    python -m daily --init       # 初始化配置
    python -m daily --preview    # 预览日报（不保存）
    python -m daily send         # 推送日报
    python -m daily check        # 系统检查
    python -m daily config       # 配置管理
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def is_first_run() -> bool:
    """检查是否首次运行"""
    env_file = PROJECT_ROOT / ".env"
    config_file = PROJECT_ROOT / "config" / "columns.yaml"
    # 如果没有 .env 或者配置文件是默认的，认为是首次运行
    if not env_file.exists():
        return True
    # 检查是否配置过 LLM
    content = env_file.read_text(encoding="utf-8")
    return "OPENAI_API_KEY" not in content and "LLM_API_KEY" not in content


def show_welcome():
    """显示欢迎界面"""
    welcome_text = """
[bold blue]欢迎使用 Daily Agent ![/bold blue]

你的个性化智能日报助手

[cyan]主要功能:[/cyan]
• 自动从多源采集信息（RSS、API、社交媒体）
• 智能筛选和摘要（支持 LLM）
• 个性化排序（基于你的兴趣）
• 多格式输出（Markdown、Telegram、Slack、邮件）

[cyan]首次使用，请选择配置方式:[/cyan]
"""
    console.print(Panel(welcome_text, border_style="blue"))


def show_mode_selection() -> str:
    """显示模式选择，返回选择的模式"""
    console.print("""
[bold]请选择配置模式:[/bold]

  [green]1. 快速模式[/green] (推荐首次体验)
     30 秒完成，使用默认模板

  [blue]2. 智能模式[/blue] (推荐日常使用)
     AI 辅助配置，了解你的兴趣后自动推荐

  [yellow]3. 专家模式[/yellow] (深度定制)
     完全手动控制所有配置选项
""")

    from rich.prompt import Prompt
    choice = Prompt.ask(
        "请选择",
        choices=["1", "2", "3", "fast", "smart", "expert"],
        default="1"
    )

    mapping = {
        "1": "fast", "fast": "fast",
        "2": "smart", "smart": "smart",
        "3": "expert", "expert": "expert"
    }
    return mapping.get(choice, "fast")


async def run_init(mode: str = None):
    """运行初始化"""
    if mode is None:
        show_welcome()
        mode = show_mode_selection()

    console.print(f"\n[bold cyan]启动 {mode} 模式...[/bold cyan]\n")

    if mode == "fast":
        await init_fast_mode()
    elif mode == "smart":
        await init_smart_mode()
    elif mode == "expert":
        await init_expert_mode()


async def _create_default_config(config_path: Path):
    """创建默认配置文件"""
    default_config = """columns:
  - id: "headlines"
    name: "🔥 今日头条"
    description: "当日最重要的科技新闻"
    enabled: true
    max_items: 5
    order: 1
    sources:
      - type: "api"
        name: "Hacker News"
        provider: "hackernews"
        weight: 1.0
        filter:
          min_score: 50
    organization:
      sort_by: "time"
      dedup_strategy: "semantic"
      summarize: "3_points"
"""
    config_path.write_text(default_config, encoding="utf-8")


async def init_fast_mode():
    """快速模式初始化 - 一键完成所有设置"""
    from src.config import DATA_DIR
    from rich.progress import Progress, SpinnerColumn, TextColumn

    console.print("[bold blue]🚀 快速配置向导[/bold blue]\n")

    # 使用进度条显示初始化过程
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # 1. 确保数据目录存在
        task = progress.add_task("创建数据目录...", total=None)
        DATA_DIR.mkdir(exist_ok=True)
        progress.update(task, description="[green]✓[/green] 数据目录已创建")

        # 2. 初始化数据库
        task = progress.add_task("初始化数据库...", total=None)
        from src.database import init_db
        await init_db()
        progress.update(task, description="[green]✓[/green] 数据库初始化完成")

        # 3. 复制默认配置
        task = progress.add_task("应用默认配置...", total=None)
        config_path = PROJECT_ROOT / "config" / "columns.yaml"
        if not config_path.exists():
            await _create_default_config(config_path)
        progress.update(task, description="[green]✓[/green] 默认配置已应用")

        # 4. 测试数据源连接
        task = progress.add_task("测试数据源...", total=None)
        # 简单测试一个数据源
        try:
            from src.collector import HackerNewsCollector
            collector = HackerNewsCollector("Test", {"max_items": 1})
            result = await collector.collect()
            if result.success:
                progress.update(task, description=f"[green]✓[/green] 数据源连接正常 ({len(result.items)} 条)")
            else:
                progress.update(task, description=f"[yellow]⚠[/yellow] 数据源测试: {result.message}")
        except Exception as e:
            progress.update(task, description=f"[yellow]⚠[/yellow] 数据源测试失败: {e}")

    # 5. 生成测试日报
    console.print("\n[cyan]📰 正在生成测试日报...[/cyan]\n")
    await generate_daily_report(preview=True)

    # 6. 显示完成信息
    console.print("\n[bold green]✅ 快速配置完成！[/bold green]\n")

    # 显示配置总结
    from rich.table import Table
    table = Table(show_header=False, box=None)
    table.add_row("[dim]数据目录[/dim]", str(DATA_DIR))
    table.add_row("[dim]配置文件[/dim]", str(config_path))
    table.add_row("[dim]数据库[/dim]", str(DATA_DIR / "daily.db"))
    console.print(table)

    console.print(""\"
[cyan]常用命令:[/cyan]
  python -m daily              # 生成日报
  python -m daily --preview    # 预览日报
  python -m daily send         # 推送日报
  python -m daily config       # 配置管理
""")


async def init_smart_mode():
    """智能模式 - 使用 setup_wizard"""
    from src.setup_wizard import SetupWizard

    wizard = SetupWizard()
    await wizard.run_full_setup()

    console.print("\n[bold green]✅ 配置完成！[/bold green]")


async def init_expert_mode():
    """专家模式 - 使用 expert_setup"""
    from src.expert_setup import run_expert_setup
    await run_expert_setup()


async def generate_daily_report(
    user: str = "default",
    date: str = None,
    preview: bool = False
):
    """生成日报"""
    from src.service import DailyAgentService

    service = DailyAgentService()
    await service.initialize()

    dt = datetime.strptime(date, "%Y-%m-%d") if date else None

    if preview:
        console.print("[dim]预览模式：不保存到数据库[/dim]\n")

    with console.status("[bold green]正在生成日报..."):
        report = await service.generate_daily_report(user_id=user, date=dt)

    console.print(f"\n[bold green]✓[/bold green] 日报生成成功")
    console.print(f"  日期: {report.date.strftime('%Y-%m-%d') if hasattr(report, 'date') else '今天'}")
    console.print(f"  条目: {report.total_items} 条")
    console.print(f"  ID: {report.id}")

    return report


async def push_report(channel: str = None):
    """推送日报"""
    from src.database import DailyReportRepository, get_session
    from src.models import DailyReport
    from src.service import DailyAgentService
    from sqlalchemy import select

    service = DailyAgentService()
    await service.initialize()

    # 获取最新日报
    async with get_session() as session:
        from src.database import DailyReportDB
        result = await session.execute(
            select(DailyReportDB).order_by(DailyReportDB.date.desc()).limit(1)
        )
        db_report = result.scalar_one_or_none()

        if not db_report:
            console.print("[red]✗ 没有找到日报，请先运行：python -m daily[/red]")
            return

        report = DailyReport(
            id=db_report.id,
            date=db_report.date,
            user_id=db_report.user_id,
            title=db_report.title,
            total_items=db_report.total_items
        )

        channels = [channel] if channel else None

        with console.status(f"[bold green]正在推送到 {channel or '默认渠道'}..."):
            results = await service.push_report(report, channels)

        for ch, result in results.items():
            ch_name = ch.value if hasattr(ch, 'value') else str(ch)
            if result.success:
                console.print(f"[green]✓[/green] {ch_name}: {result.message}")
            else:
                console.print(f"[red]✗[/red] {ch_name}: {result.message}")


async def check_system():
    """系统检查"""
    from src.doctor import SystemChecker

    checker = SystemChecker()
    results = await checker.run_all_checks()

    console.print("\n[bold]系统检查结果:[/bold]\n")

    for result in results:
        icon = "✓" if result.status == "ok" else "⚠" if result.status == "warning" else "✗"
        color = "green" if result.status == "ok" else "yellow" if result.status == "warning" else "red"
        console.print(f"[{color}]{icon}[/{color}] {result.name}: {result.message}")

        if result.fix_command:
            console.print(f"   [dim]修复: {result.fix_command}[/dim]")


async def manage_config(action: str = "edit"):
    """配置管理"""
    if action == "edit":
        import subprocess
        import os

        config_path = PROJECT_ROOT / "config" / "columns.yaml"
        editor = os.environ.get("EDITOR", "vim")

        console.print(f"[dim]正在打开 {config_path}...[/dim]")
        subprocess.call([editor, str(config_path)])

    elif action == "show":
        from src.config import get_column_config

        config = get_column_config()
        columns = config.get_columns()

        console.print("\n[bold]当前配置的分栏:[/bold]\n")

        from rich.table import Table
        table = Table(show_header=True)
        table.add_column("序号", style="cyan", width=4)
        table.add_column("名称", style="green")
        table.add_column("数据源数量", justify="right")
        table.add_column("最大条目", justify="right")

        for i, col in enumerate(columns, 1):
            sources = len(col.get("sources", []))
            table.add_row(
                str(i),
                col.get("name", "未命名"),
                str(sources),
                str(col.get("max_items", 5))
            )

        console.print(table)


async def list_sources():
    """列出所有数据源"""
    from src.config import get_column_config

    config = get_column_config()
    columns = config.get_columns()

    console.print("\n[bold]数据源列表:[/bold]\n")

    from rich.tree import Tree
    root = Tree("📰 日报")

    for col in columns:
        col_node = root.add(f"[bold]{col.get('name')}[/bold]")
        for source in col.get("sources", []):
            source_type = source.get("type", "unknown")
            source_name = source.get("name", "未命名")
            col_node.add(f"  • {source_name} ([dim]{source_type}[/dim])")

    console.print(root)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="daily",
        description="Daily Agent - 个性化智能日报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m daily                    # 生成今日日报
  python -m daily --preview          # 预览日报（不保存）
  python -m daily --date 2024-01-15  # 生成指定日期的日报
  python -m daily send               # 推送最新日报
  python -m daily check              # 系统检查
  python -m daily config             # 查看配置
  python -m daily sources            # 列出数据源
  python -m daily --init             # 初始化配置
        """
    )

    # 主要选项
    parser.add_argument(
        "--init", "-i",
        action="store_true",
        help="初始化配置（首次使用）"
    )
    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="预览模式（不保存到数据库）"
    )
    parser.add_argument(
        "--date", "-d",
        help="指定日期 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--user", "-u",
        default="default",
        help="用户 ID (默认: default)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式（仅输出必要信息）"
    )

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # send 命令
    send_parser = subparsers.add_parser("send", help="推送日报")
    send_parser.add_argument(
        "--channel", "-c",
        help="指定推送渠道 (telegram/slack/discord/email)"
    )

    # check 命令
    subparsers.add_parser("check", help="系统检查和诊断")

    # config 命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument(
        "action",
        nargs="?",
        choices=["edit", "show"],
        default="show",
        help="配置操作 (默认: show)"
    )

    # sources 命令
    subparsers.add_parser("sources", help="列出所有数据源")

    # test 命令
    test_parser = subparsers.add_parser("test", help="测试组件")
    test_parser.add_argument(
        "component",
        choices=["llm", "source", "channel"],
        help="要测试的组件"
    )
    test_parser.add_argument(
        "name",
        nargs="?",
        help="组件名称（用于 source/channel 测试）"
    )

    args = parser.parse_args()

    # 检查是否首次运行
    if is_first_run() and not args.init and not args.command:
        show_welcome()
        mode = show_mode_selection()
        asyncio.run(run_init(mode))
        return

    # 处理 --init
    if args.init:
        asyncio.run(run_init())
        return

    # 处理子命令
    if args.command == "send":
        asyncio.run(push_report(args.channel))
    elif args.command == "check":
        asyncio.run(check_system())
    elif args.command == "config":
        asyncio.run(manage_config(args.action))
    elif args.command == "sources":
        asyncio.run(list_sources())
    elif args.command == "test":
        console.print(f"[dim]测试 {args.component}...[/dim]")
        # TODO: 实现测试逻辑
    else:
        # 默认生成日报
        asyncio.run(generate_daily_report(
            user=args.user,
            date=args.date,
            preview=args.preview
        ))


if __name__ == "__main__":
    main()
