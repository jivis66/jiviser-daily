"""
命令行工具
"""
import asyncio
import os
from datetime import datetime, timezone

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
        
        async with get_session() as session:
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
@click.option("--mode", "-m", type=click.Choice(["fast", "configure"]), help="启动模式")
@click.option("--template", "-t", help="使用预设模板")
def start(mode: str, template: str):
    """启动 Daily Agent 服务"""
    async def _init_and_setup():
        """初始化数据库和配置（异步部分）"""
        from src.database import init_db
        
        # 检查是否首次启动
        is_first_run = not os.path.exists("data/daily.db")
        
        if is_first_run and not mode:
            # 首次启动，交互式选择模式
            console.print("""
🚀 Daily Agent 首次启动
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

欢迎使用 Daily Agent 个性化日报系统！

请选择启动模式：

  [1] ⚡ Fast 模式 - 开箱即用（推荐首次体验）
      • 30 秒完成启动
      • 使用默认配置，无需设置
      • 基础功能立即可用
      • ⚠️ 智能摘要、个性化推荐等功能不可用
  
  [2] 🔧 Configure 模式 - 全面配置（推荐日常使用）
      • 3-5 分钟完成配置
      • 个性化用户画像
      • LLM 智能摘要
      • 推送渠道设置
      • 完整能力体验

请选择 [1-2]: """)
            choice = input().strip()
            return "fast" if choice == "1" else "configure"
        return mode
    
    async def _run_setup(selected_mode: str):
        """运行设置（异步部分）"""
        from src.database import init_db
        
        if selected_mode == "fast" or (not selected_mode and template):
            # Fast 模式启动
            console.print("""
🚀 Daily Agent - Fast 模式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ 正在初始化...
            """)
            
            await init_db()
            
            # 如果有模板，应用模板
            if template:
                from src.setup_wizard import SetupWizard
                wizard = SetupWizard()
                await wizard.apply_template(template)
                console.print(f"  ✓ 应用模板: {template}")
            
            console.print("""
  ✓ 数据库初始化完成
  ✓ 默认配置加载完成
  ✓ 通用模板应用完成

✅ Fast 模式启动成功！

📖 可用命令：
  生成日报:    python -m src.cli generate
  查看配置:    python -m src.cli verify
  切换模式:    python -m src.cli setup wizard

⚠️  提示：当前使用默认配置，部分高级功能未启用。
    如需完整功能体验，请运行：python -m src.cli setup wizard

🌐 Web 界面: http://localhost:8080
📚 API 文档: http://localhost:8080/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """)
        
        elif selected_mode == "configure":
            # Configure 模式 - 运行完整向导
            from src.setup_wizard import SetupWizard
            wizard = SetupWizard()
            await wizard.run_full_setup()
    
    # 第一步：交互式选择模式（如果需要）
    selected_mode = asyncio.run(_init_and_setup())
    
    # 第二步：运行设置
    if selected_mode:
        asyncio.run(_run_setup(selected_mode))
    
    # 第三步：启动服务（同步方式，避免 asyncio.run 嵌套）
    import uvicorn
    from src.config import get_settings
    settings = get_settings()
    
    console.print(f"\n[green]正在启动服务...[/green]\n")
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


@cli.command()
def status():
    """查看系统状态"""
    async def _status():
        from src.config import get_settings, get_column_config
        from src.database import get_session, DailyReportRepository, ContentRepository
        from datetime import datetime, timedelta
        
        settings = get_settings()
        
        console.print("""
🤖 Daily Agent 状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
        # 服务状态
        console.print("[bold]服务状态:[/bold]")
        console.print(f"  应用名称: {settings.app_name}")
        console.print(f"  调试模式: {'开启' if settings.debug else '关闭'}")
        console.print(f"  监听地址: {settings.host}:{settings.port}")
        
        # 配置状态
        console.print("\n[bold]配置状态:[/bold]")
        
        # LLM
        llm_status = "✅ 已配置" if settings.openai_api_key else "⚪ 未配置"
        console.print(f"  LLM: {llm_status}")
        
        # 推送渠道
        channels = []
        if settings.telegram_bot_token:
            channels.append("Telegram")
        if settings.slack_bot_token:
            channels.append("Slack")
        if settings.discord_bot_token:
            channels.append("Discord")
        if settings.smtp_host:
            channels.append("Email")
        
        channel_status = ", ".join(channels) if channels else "⚪ 未配置"
        console.print(f"  推送渠道: {channel_status}")
        
        # 分栏配置
        try:
            col_config = get_column_config()
            columns = col_config.get_columns()
            console.print(f"  日报分栏: {len(columns)} 个")
        except:
            console.print("  日报分栏: ⚪ 未配置")
        
        # 今日统计
        console.print("\n[bold]今日统计:[/bold]")
        try:
            async with get_session() as session:
                content_repo = ContentRepository(session)
                report_repo = DailyReportRepository(session)
                
                today = datetime.now(timezone.utc).date()
                yesterday = today - timedelta(days=1)
                
                # 获取今日采集数量
                daily_items = await content_repo.get_by_date(yesterday, today)
                console.print(f"  采集内容: {len(daily_items)} 条")
                
                # 获取今日日报
                today_report = await report_repo.get_by_date("default", datetime.now(timezone.utc))
                if today_report:
                    console.print(f"  生成日报: 1 份 ({today_report.total_items} 条内容)")
                    console.print(f"  推送状态: {'已推送' if today_report.is_sent else '未推送'}")
                else:
                    console.print("  生成日报: 0 份")
        except Exception as e:
            console.print(f"  统计信息: 暂不可用 ({e})")
        
        console.print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    asyncio.run(_status())


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
            elif cred["expires_at"] and cred["expires_at"] < datetime.now(timezone.utc):
                status = "[red]✗ 已过期[/red]"
            elif cred["expires_at"] and (cred["expires_at"] - datetime.now(timezone.utc)).days <= 3:
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
@click.option("--browser", "-b", is_flag=True, help="使用浏览器自动获取（推荐）")
@click.option("--manual", "-m", is_flag=True, help="手动粘贴 cURL")
def auth_add(source_name: str, username: str = None, browser: bool = False, manual: bool = False):
    """添加认证配置"""
    from src.auth_manager import get_auth_manager, AUTH_CONFIGS
    
    manager = get_auth_manager()
    config = manager.get_config(source_name)
    
    if not config:
        click.echo(f"不支持的渠道: {source_name}")
        click.echo("\n支持的渠道:")
        for key, cfg in AUTH_CONFIGS.items():
            click.echo(f"  • {key} - {cfg.display_name}")
        return
    
    # 选择方式
    if not browser and not manual:
        click.echo(f"\n{'='*60}")
        click.echo(f"正在为 [{config.display_name}] 配置认证信息")
        click.echo(f"{'='*60}\n")
        click.echo("请选择获取方式:")
        click.echo("  [1] 🌐 浏览器自动获取（推荐）- 自动登录并提取 Cookie")
        click.echo("  [2] 📋 手动粘贴 cURL - 从浏览器开发者工具复制")
        choice = click.prompt("请选择", type=str, default="1")
        browser = choice == "1"
        manual = choice == "2"
    
    if browser:
        # 浏览器自动获取
        _auth_add_browser(source_name, username)
    else:
        # 手动粘贴
        _auth_add_manual(source_name, username)


def _auth_add_browser(source_name: str, username: str = None):
    """使用浏览器自动获取 Cookie"""
    async def _run():
        from src.browser_auth import interactive_auth
        success, message = await interactive_auth(source_name, username)
        if success:
            click.echo(f"\n✓ {message}")
        else:
            click.echo(f"\n✗ {message}")
    
    asyncio.run(_run())


def _auth_add_manual(source_name: str, username: str = None):
    """手动粘贴 cURL"""
    from src.auth_manager import get_auth_manager
    
    manager = get_auth_manager()
    config = manager.get_config(source_name)
    
    click.echo("\n" + "-"*40)
    click.echo(config.help_text)
    click.echo("-"*40)
    click.echo("\n请粘贴 cURL 命令或 Cookie 字符串:")
    
    try:
        curl_command = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        click.echo("\n已取消")
        return
    
    curl_command = curl_command.replace("\\", "")
    
    if not curl_command:
        click.echo("输入为空，取消配置")
        return
    
    async def _save_and_test():
        click.echo("正在保存...")
        success, message = await manager.add_auth(source_name, curl_command, username)
        
        if success:
            click.echo(f"✓ {message}")
            
            # 对严格反爬平台，跳过 HTTP 测试（避免 406）
            if source_name in ['xiaohongshu', 'douyin']:
                click.echo("✓ Cookie 已保存（适合配合浏览器采集器使用）")
            else:
                click.echo("正在测试...")
                is_valid, test_msg, _ = await manager.test_auth(source_name)
                if is_valid:
                    click.echo(f"✓ 测试通过")
                else:
                    click.echo(f"⚠ 测试未通过: {test_msg}")
        else:
            click.echo(f"✗ {message}")
    
    asyncio.run(_save_and_test())


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
        # 小红书显示特殊提示
        special_note = ""
        if key == "xiaohongshu":
            special_note = "\n[green]✨ 支持浏览器自动登录，无需手动复制 Cookie[/green]"
        
        console.print(Panel(
            f"[bold]{config.display_name}[/bold] ([cyan]{key}[/cyan])\n"
            f"[dim]认证方式:[/dim] {config.auth_type}\n"
            f"[dim]默认有效期:[/dim] {config.expires_days} 天"
            f"{special_note}\n\n"
            f"{config.help_text}",
            border_style="green"
        ))
    
    console.print("\n[bold]常用命令:[/bold]")
    console.print("  [cyan]python -m src.cli auth list[/cyan]              - 查看已配置的认证")
    console.print("  [cyan]python -m src.cli auth add jike[/cyan]           - 添加即刻认证")
    console.print("  [cyan]python -m src.cli auth add xiaohongshu -b[/cyan] - 小红书浏览器自动登录")
    console.print("  [cyan]python -m src.cli auth test jike[/cyan]          - 测试即刻认证")


# ============ 启动设置向导命令 ============

@cli.group(invoke_without_command=True)
@click.option("--all", "all_modules", is_flag=True, help="完整重新配置所有模块")
@click.option("--module", "module_name", type=click.Choice(["profile", "interests", "daily", "llm", "channels"]), help="仅配置特定模块")
@click.option("--mode", type=click.Choice(["fast", "configure"]), help="启动模式")
@click.option("--template", help="使用预设模板")
@click.pass_context
def setup(ctx, all_modules: bool, module_name: str, mode: str, template: str):
    """启动设置向导 - 配置用户画像、兴趣和日报"""
    if ctx.invoked_subcommand is not None:
        return
    
    async def _setup():
        # 如果指定了模式，执行对应的启动流程
        if mode == "fast":
            console.print("⚡ Fast 模式启动...")
            if template:
                from src.setup_wizard import apply_template
                await apply_template(template)
                console.print(f"✓ 应用模板: {template}")
            console.print("✅ Fast 模式配置完成！")
            return
        
        elif mode == "configure" or all_modules or module_name:
            wizard = SetupWizard()
            
            if all_modules:
                await wizard.run_full_setup()
            elif module_name:
                # 仅配置特定模块
                if module_name == "profile":
                    wizard.profile_config = await wizard._setup_profile()
                    await wizard._save_config()
                elif module_name == "interests":
                    wizard.interest_config = await wizard._setup_interests()
                    await wizard._save_config()
                elif module_name == "daily":
                    wizard.daily_config = await wizard._setup_daily_report()
                    await wizard._save_daily_config()
                elif module_name == "llm":
                    await wizard._setup_llm()
                console.print(f"✅ {module_name} 模块配置完成！")
            else:
                await wizard.run_full_setup()
            return
        
        # 默认运行完整向导
        wizard = SetupWizard()
        await wizard.run_full_setup()
    
    asyncio.run(_setup())


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


# ============ 配置管理命令 ============

@cli.group()
def config():
    """配置管理 - 查看、导出、导入配置"""
    pass


@config.command("show")
@click.option("--user", "-u", default="default", help="用户 ID")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
def config_show(user: str, format: str):
    """查看当前配置"""
    async def _show():
        from src.setup_wizard import get_user_config
        
        try:
            user_config = await get_user_config(user)
            
            if format == "yaml":
                import yaml
                output = yaml.dump(user_config, allow_unicode=True, sort_keys=False)
            else:
                import json
                output = json.dumps(user_config, indent=2, ensure_ascii=False)
            
            console.print(Panel(output, title=f"用户配置: {user}", border_style="blue"))
        except Exception as e:
            console.print(f"[yellow]⚠️ 尚未配置，请运行: python -m src.cli setup wizard[/yellow]")
    
    asyncio.run(_show())


@config.command("export")
@click.option("--user", "-u", default="default", help="用户 ID")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="导出格式")
@click.option("--output", "-o", help="输出文件路径")
def config_export(user: str, format: str, output: str):
    """导出用户配置"""
    async def _export():
        from src.setup_wizard import export_config
        
        try:
            filepath = await export_config(user_id=user, format=format, output=output)
            console.print(f"[green]✅ 配置已导出到: {filepath}[/green]")
        except ValueError as e:
            console.print(f"[red]✗ {e}[/red]")
    
    asyncio.run(_export())


@config.command("import")
@click.argument("filepath")
@click.option("--user", "-u", default="default", help="用户 ID")
@click.option("--force", "-f", is_flag=True, help="强制覆盖现有配置")
def config_import(filepath: str, user: str, force: bool):
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


@config.command("validate")
@click.option("--config-file", "-c", help="配置文件路径（验证外部配置）")
def config_validate(config_file: str):
    """验证配置有效性"""
    console.print("[bold]配置验证[/bold]\n")
    
    if config_file:
        # 验证外部配置文件
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            console.print(f"[green]✅ 配置文件格式正确[/green]")
            console.print(f"  包含键: {', '.join(config.keys())}")
        except Exception as e:
            console.print(f"[red]✗ 配置文件错误: {e}[/red]")
    else:
        # 验证当前配置
        from src.config import get_settings, get_column_config
        
        settings = get_settings()
        col_config = get_column_config()
        
        errors = []
        warnings = []
        
        # 检查必要配置
        if not settings.api_secret_key or settings.api_secret_key == "your-secret-key-change-this":
            warnings.append("API_SECRET_KEY 使用默认值，建议修改")
        
        # 检查分栏配置
        try:
            columns = col_config.get_columns()
            if not columns:
                errors.append("分栏配置为空")
            else:
                for col in columns:
                    if not col.get('sources'):
                        warnings.append(f"分栏 '{col.get('name')}' 没有配置数据源")
        except Exception as e:
            errors.append(f"分栏配置错误: {e}")
        
        # 输出结果
        if errors:
            console.print("[red]错误:[/red]")
            for e in errors:
                console.print(f"  ✗ {e}")
        
        if warnings:
            console.print("[yellow]警告:[/yellow]")
            for w in warnings:
                console.print(f"  ⚠ {w}")
        
        if not errors and not warnings:
            console.print("[green]✅ 配置验证通过[/green]")


@config.command("reset")
@click.option("--user", "-u", default="default", help="用户 ID")
@click.confirmation_option(prompt="确定要重置配置吗？这将删除所有用户设置")
def config_reset(user: str):
    """重置用户配置"""
    async def _reset():
        from src.database import get_session
        from sqlalchemy import text
        
        async with get_session() as session:
            # 删除用户相关数据
            await session.execute(text("DELETE FROM user_profiles WHERE user_id = :user_id"), {"user_id": user})
            await session.execute(text("DELETE FROM user_feedbacks WHERE user_id = :user_id"), {"user_id": user})
            await session.commit()
            console.print(f"[green]✅ 用户 {user} 的配置已重置[/green]")
    
    asyncio.run(_reset())


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
