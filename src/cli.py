"""
命令行工具
"""
import asyncio
import os
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
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


# ============ 认证管理命令 ============

@cli.group()
def auth():
    """认证管理 - 管理需要登录的信息渠道"""
    pass


@auth.command("list")
def auth_list():
    """列出所有已配置的认证"""
    async def _list():
        from src.auth_manager import get_auth_manager
        
        manager = get_auth_manager()
        credentials = await manager.list_auth()
        
        if not credentials:
            console.print("[yellow]暂无认证配置[/yellow]")
            console.print("\n使用 [cyan]python -m src.cli auth add <渠道名>[/cyan] 添加认证")
            console.print("\n支持的渠道:")
            for key, config in manager.get_supported_sources().items():
                console.print(f"  • [green]{key}[/green] - {config.display_name}")
            return
        
        table = Table(title="已配置的认证")
        table.add_column("渠道", style="cyan")
        table.add_column("认证方式", style="blue")
        table.add_column("用户信息", style="green")
        table.add_column("过期时间", style="yellow")
        table.add_column("状态", style="bold")
        
        for cred in credentials:
            expires = cred["expires_at"].strftime("%Y-%m-%d %H:%M") if cred["expires_at"] else "未知"
            
            # 计算状态
            if not cred["is_valid"]:
                status = "[red]✗ 失效[/red]"
            elif cred["expires_at"] and cred["expires_at"] < datetime.utcnow():
                status = "[red]✗ 已过期[/red]"
            elif cred["expires_at"] and (cred["expires_at"] - datetime.utcnow()).days <= 3:
                status = "[yellow]⚠ 即将过期[/yellow]"
            else:
                status = "[green]✓ 有效[/green]"
            
            user_info = cred["username"] or "-"
            
            table.add_row(
                f"{cred['display_name']}\n[cyan]({cred['source_name']})[/cyan]",
                cred["auth_type"],
                user_info,
                expires,
                status
            )
        
        console.print(table)
    
    asyncio.run(_list())


@auth.command("add")
@click.argument("source_name")
@click.option("--username", "-u", help="用户名（可选）")
def auth_add(source_name: str, username: str = None):
    """添加认证配置"""
    async def _add():
        from src.auth_manager import get_auth_manager, AUTH_CONFIGS
        
        manager = get_auth_manager()
        config = manager.get_config(source_name)
        
        if not config:
            console.print(f"[red]不支持的渠道: {source_name}[/red]")
            console.print("\n支持的渠道:")
            for key, cfg in AUTH_CONFIGS.items():
                console.print(f"  • [green]{key}[/green] - {cfg.display_name}")
            return
        
        # 显示帮助信息
        console.print(Panel(
            f"[bold blue]正在为 [{config.display_name}] 配置认证信息[/bold blue]\n\n"
            f"{config.help_text}\n\n"
            "[yellow]提示: 支持粘贴完整的 cURL 命令或仅 Cookie 字符串[/yellow]",
            title="认证配置向导",
            border_style="blue"
        ))
        
        # 获取输入
        console.print("\n[cyan]请粘贴 cURL 命令或 Cookie 字符串:[/cyan]")
        console.print("(输入完成后按 Enter，支持多行输入，按 Ctrl+D 或输入空行结束)\n")
        
        lines = []
        try:
            while True:
                line = input("> ")
                if not line.strip():
                    break
                lines.append(line)
        except EOFError:
            pass
        
        curl_command = "\n".join(lines).strip()
        
        if not curl_command:
            console.print("[red]输入为空，取消配置[/red]")
            return
        
        # 添加认证
        with console.status("[bold green]正在保存认证配置..."):
            success, message = await manager.add_auth(source_name, curl_command, username)
        
        if success:
            console.print(f"\n[green]{message}[/green]")
            
            # 自动测试
            console.print("\n[bold]正在测试认证...[/bold]")
            is_valid, test_msg, user_info = await manager.test_auth(source_name)
            
            if is_valid:
                console.print(f"[green]✓ 认证测试通过: {test_msg}[/green]")
                if user_info and user_info.get("username"):
                    console.print(f"  用户名: [cyan]{user_info['username']}[/cyan]")
            else:
                console.print(f"[yellow]⚠ 认证测试失败: {test_msg}[/yellow]")
                console.print("[yellow]配置已保存，但可能无法正常使用，请检查 Cookie 是否有效[/yellow]")
        else:
            console.print(f"\n[red]✗ {message}[/red]")
    
    asyncio.run(_add())


@auth.command("update")
@click.argument("source_name")
@click.option("--username", "-u", help="用户名（可选）")
def auth_update(source_name: str, username: str = None):
    """更新认证配置"""
    # 复用 add 逻辑
    async def _update():
        from src.auth_manager import get_auth_manager
        
        manager = get_auth_manager()
        config = manager.get_config(source_name)
        
        if not config:
            console.print(f"[red]不支持的渠道: {source_name}[/red]")
            return
        
        # 检查现有配置
        from src.database import get_session, AuthCredentialRepository
        async with get_session() as session:
            repo = AuthCredentialRepository(session)
            existing = await repo.get_by_source(source_name)
        
        if existing:
            console.print(f"[blue]当前配置将于 {existing.expires_at.strftime('%Y-%m-%d %H:%M')} 过期[/blue]\n")
        
        # 调用 add 逻辑
        await auth_add.callback(source_name, username)
    
    asyncio.run(_update())


@auth.command("remove")
@click.argument("source_name")
@click.confirmation_option(prompt="确定要删除此认证配置吗?")
def auth_remove(source_name: str):
    """删除认证配置"""
    async def _remove():
        from src.auth_manager import get_auth_manager
        
        manager = get_auth_manager()
        success, message = await manager.remove_auth(source_name)
        
        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[red]{message}[/red]")
    
    asyncio.run(_remove())


@auth.command("test")
@click.argument("source_name")
def auth_test(source_name: str):
    """测试认证是否有效"""
    async def _test():
        from src.auth_manager import get_auth_manager
        
        manager = get_auth_manager()
        config = manager.get_config(source_name)
        
        if not config:
            console.print(f"[red]不支持的渠道: {source_name}[/red]")
            return
        
        console.print(f"[bold]测试 [{config.display_name}] 认证状态...[/bold]\n")
        
        with console.status("[bold green]正在测试认证..."):
            is_valid, message, user_info = await manager.test_auth(source_name)
        
        if is_valid:
            console.print(f"[green]✓ 认证有效[/green]")
            if user_info:
                if user_info.get("username"):
                    console.print(f"  用户名: [cyan]{user_info['username']}[/cyan]")
                if user_info.get("user_id"):
                    console.print(f"  用户ID: [dim]{user_info['user_id']}[/dim]")
        else:
            console.print(f"[red]✗ {message}[/red]")
    
    asyncio.run(_test())


@auth.command("guide")
def auth_guide():
    """显示认证配置指南"""
    from src.auth_manager import AUTH_CONFIGS
    
    console.print("[bold blue]认证配置指南[/bold blue]\n")
    console.print("以下渠道需要登录认证才能采集个性化内容:\n")
    
    for key, config in AUTH_CONFIGS.items():
        console.print(Panel(
            f"[bold]{config.display_name}[/bold] ([cyan]{key}[/cyan])\n"
            f"[dim]认证方式:[/dim] {config.auth_type}\n"
            f"[dim]默认有效期:[/dim] {config.expires_days} 天\n\n"
            f"{config.help_text}",
            border_style="green"
        ))
    
    console.print("\n[bold]常用命令:[/bold]")
    console.print("  [cyan]python -m src.cli auth list[/cyan]     - 查看已配置的认证")
    console.print("  [cyan]python -m src.cli auth add jike[/cyan]  - 添加即刻认证")
    console.print("  [cyan]python -m src.cli auth test jike[/cyan] - 测试即刻认证")


# ============ 启动设置向导命令 ============

@cli.group()
def setup():
    """启动设置向导 - 配置用户画像、兴趣和日报"""
    pass


@setup.command("wizard")
@click.option("--user", "-u", default="default", help="用户 ID")
def setup_wizard(user: str):
    """运行完整设置向导"""
    async def _wizard():
        from src.setup_wizard import SetupWizard
        
        wizard = SetupWizard(user_id=user)
        await wizard.run_full_setup()
    
    asyncio.run(_wizard())


@setup.command("export")
@click.option("--user", "-u", default="default", help="用户 ID")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="导出格式")
@click.option("--output", "-o", help="输出文件路径")
def setup_export(user: str, format: str, output: str):
    """导出用户配置"""
    async def _export():
        from src.setup_wizard import export_config
        
        try:
            filepath = await export_config(user_id=user, format=format, output=output)
            console.print(f"[green]✅ 配置已导出到: {filepath}[/green]")
        except ValueError as e:
            console.print(f"[red]✗ {e}[/red]")
    
    asyncio.run(_export())


@setup.command("import")
@click.argument("filepath")
@click.option("--user", "-u", default="default", help="用户 ID")
@click.option("--force", "-f", is_flag=True, help="强制覆盖现有配置")
def setup_import(filepath: str, user: str, force: bool):
    """导入用户配置"""
    async def _import():
        from src.setup_wizard import import_config
        
        try:
            success = await import_config(filepath, user_id=user, overwrite=force)
            if success:
                console.print(f"[green]✅ 配置导入成功[/green]")
            else:
                console.print(f"[yellow]⚠️ 用户已有配置，使用 --force 覆盖[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ 导入失败: {e}[/red]")
    
    asyncio.run(_import())


@setup.command("templates")
def setup_templates():
    """查看可用配置模板"""
    from src.setup_wizard import PROFILE_TEMPLATES
    
    console.print("[bold blue]可用配置模板[/bold blue]\n")
    
    table = Table()
    table.add_column("模板ID", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("描述")
    table.add_column("阅读时间")
    
    for key, template in PROFILE_TEMPLATES.items():
        table.add_row(
            key,
            template.name,
            template.description,
            f"{template.daily_time_minutes} 分钟"
        )
    
    console.print(table)
    
    console.print("\n[bold]使用模板快速设置：[/bold]")
    console.print("  [cyan]python -m src.cli setup wizard[/cyan]  - 启动向导并选择模板")


# ============ LLM 配置命令 ============

@cli.group()
def llm():
    """LLM 配置管理 - 配置大语言模型"""
    pass


@llm.command("setup")
def llm_setup():
    """启动 LLM 配置向导"""
    async def _setup():
        from src.llm_config import LLMSetupWizard
        
        wizard = LLMSetupWizard()
        await wizard.run_setup()
    
    asyncio.run(_setup())


@llm.command("status")
def llm_status():
    """查看 LLM 配置状态"""
    from src.llm_config import LLMSetupWizard
    
    wizard = LLMSetupWizard()
    wizard.print_status()


@llm.command("test")
def llm_test():
    """测试 LLM 连接"""
    async def _test():
        from src.llm_config import get_llm_manager
        
        manager = get_llm_manager()
        config = manager.get_current_config()
        
        if not config.is_configured():
            console.print("[yellow]⚠️ 尚未配置 LLM，请先运行: python -m src.cli llm setup[/yellow]")
            return
        
        console.print("[bold]🧪 正在测试 LLM 连接...[/bold]\n")
        
        with console.status("[bold green]测试中..."):
            success, message = await manager.test_connection()
        
        if success:
            console.print(f"[green]✅ {message}[/green]")
        else:
            console.print(f"[red]✗ {message}[/red]")
    
    asyncio.run(_test())


@llm.command("switch")
def llm_switch():
    """切换 LLM 模型"""
    async def _switch():
        from src.llm_config import LLMSetupWizard
        
        wizard = LLMSetupWizard()
        await wizard.switch_model()
    
    asyncio.run(_switch())


@llm.command("models")
def llm_models():
    """查看支持的模型列表"""
    from src.llm_config import LLMSetupWizard
    
    wizard = LLMSetupWizard()
    wizard.print_models()


# 简化命令别名
@cli.command()
@click.option("--user", "-u", default="default", help="用户 ID")
def quickstart(user: str):
    """快速开始 - 运行完整设置向导"""
    async def _quickstart():
        from src.setup_wizard import SetupWizard
        
        wizard = SetupWizard(user_id=user)
        await wizard.run_full_setup()
    
    asyncio.run(_quickstart())


if __name__ == "__main__":
    cli()
