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


@config.command("edit")
@click.option("--file", "-f", type=click.Choice(["columns", "env", "daily"]), default="columns", help="要编辑的配置文件")
def config_edit(file: str):
    """使用编辑器打开配置文件"""
    import os
    import subprocess
    
    # 确定文件路径
    if file == "columns":
        filepath = "config/columns.yaml"
    elif file == "env":
        filepath = ".env"
    elif file == "daily":
        filepath = "config/daily_report.yaml"
    else:
        console.print(f"[red]未知的配置文件: {file}[/red]")
        return
    
    # 检查文件是否存在
    if not os.path.exists(filepath):
        console.print(f"[yellow]配置文件不存在: {filepath}[/yellow]")
        if file == "daily":
            console.print("此文件将在首次运行设置向导后创建")
        return
    
    # 获取编辑器
    editor = os.environ.get("EDITOR", "vim")
    if sys.platform == "win32":
        editor = os.environ.get("EDITOR", "notepad")
    
    # 显示文件信息
    console.print(f"[bold]编辑配置文件:[/bold] {filepath}")
    console.print(f"使用编辑器: {editor}\n")
    
    # 打开编辑器
    try:
        subprocess.run([editor, filepath], check=True)
        console.print(f"\n[green]✅ 配置文件已保存[/green]")
        console.print(f"运行 [cyan]python -m src.cli config validate[/cyan] 验证配置")
        console.print(f"运行 [cyan]curl -X POST http://localhost:8080/api/v1/reload[/cyan] 热更新配置")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]编辑器退出异常: {e}[/red]")
    except FileNotFoundError:
        console.print(f"[red]找不到编辑器: {editor}[/red]")
        console.print("请设置 EDITOR 环境变量指向你的编辑器")


@config.command("sources")
def config_sources():
    """列出所有配置的数据源"""
    from src.config import get_column_config
    
    try:
        col_config = get_column_config()
        columns = col_config.get_columns(enabled_only=False)
        
        console.print("[bold]配置的数据源列表[/bold]\n")
        
        for col in columns:
            col_id = col.get("id")
            col_name = col.get("name")
            enabled = col.get("enabled", True)
            
            status = "[green]✓[/green]" if enabled else "[red]✗[/red]"
            console.print(f"{status} [bold]{col_name}[/bold] ([dim]{col_id}[/dim])")
            
            sources = col.get("sources", [])
            for source in sources:
                source_name = source.get("name", "unnamed")
                source_type = source.get("type", "unknown")
                console.print(f"    • {source_name} ([dim]{source_type}[/dim])")
            
            console.print()
        
        # 统计
        total_sources = sum(len(c.get("sources", [])) for c in columns)
        enabled_cols = sum(1 for c in columns if c.get("enabled", True))
        
        console.print(f"[dim]总计: {len(columns)} 个分栏 ({enabled_cols} 个启用), {total_sources} 个数据源[/dim]")
    
    except Exception as e:
        console.print(f"[red]加载配置失败: {e}[/red]")


# ============ 诊断工具命令 ============

@cli.command()
@click.option("--fix", "auto_fix", is_flag=True, help="自动修复发现的问题")
def doctor(auto_fix: bool):
    """运行系统诊断 - 检查环境、配置、依赖等"""
    async def _doctor():
        from src.doctor import run_diagnosis, fix_issues, DoctorReport
        
        if auto_fix:
            await fix_issues()
        else:
            checker = await run_diagnosis()
            report = DoctorReport(checker)
            report.print_report()
    
    asyncio.run(_doctor())


@cli.command()
def fix():
    """自动修复系统问题"""
    async def _fix():
        from src.doctor import fix_issues
        await fix_issues()
    
    asyncio.run(_fix())


# ============ 日报管理命令 ============

@cli.group()
def reports():
    """日报管理 - 查看、对比历史日报"""
    pass


@reports.command("list")
@click.option("--user", "-u", default="default", help="用户 ID")
@click.option("--limit", "-l", default=10, help="显示数量")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="输出格式")
def reports_list(user: str, limit: int, format: str):
    """列出历史日报"""
    async def _list():
        from src.database import get_session, DailyReportRepository
        
        async with get_session() as session:
            repo = DailyReportRepository(session)
            
            # 获取日报列表
            from sqlalchemy import select
            from src.database import DailyReportDB
            
            result = await session.execute(
                select(DailyReportDB)
                .where(DailyReportDB.user_id == user)
                .order_by(DailyReportDB.date.desc())
                .limit(limit)
            )
            reports = result.scalars().all()
            
            if not reports:
                console.print("[yellow]暂无日报记录[/yellow]")
                return
            
            if format == "json":
                import json
                data = [
                    {
                        "id": r.id,
                        "date": r.date.isoformat() if r.date else None,
                        "title": r.title,
                        "total_items": r.total_items,
                        "is_sent": r.is_sent,
                        "sent_at": r.sent_at.isoformat() if r.sent_at else None
                    }
                    for r in reports
                ]
                console.print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                table = Table(title=f"📰 {user} 的日报列表")
                table.add_column("日期", style="cyan")
                table.add_column("标题", style="green")
                table.add_column("内容数", justify="right")
                table.add_column("状态", style="yellow")
                table.add_column("操作")
                
                for r in reports:
                    date_str = r.date.strftime("%Y-%m-%d") if r.date else "-"
                    status = "[green]已推送[/green]" if r.is_sent else "[dim]未推送[/dim]"
                    actions = f"[cyan]view[/cyan] | [cyan]export[/cyan]"
                    
                    table.add_row(
                        date_str,
                        r.title[:30] + "..." if len(r.title) > 30 else r.title,
                        str(r.total_items),
                        status,
                        actions
                    )
                
                console.print(table)
                console.print(f"\n[dim]使用 `python -m src.cli reports view <report_id>` 查看详情[/dim]")
    
    asyncio.run(_list())


@reports.command("view")
@click.argument("report_id")
@click.option("--format", "-f", type=click.Choice(["markdown", "json", "html"]), default="markdown", help="输出格式")
def reports_view(report_id: str, format: str):
    """查看日报详情"""
    async def _view():
        from src.database import get_session, DailyReportRepository, ContentRepository
        from src.output.formatter import MarkdownFormatter
        
        async with get_session() as session:
            repo = DailyReportRepository(session)
            content_repo = ContentRepository(session)
            
            # 获取日报
            report = await repo.get_by_id(report_id)
            if not report:
                console.print(f"[red]日报不存在: {report_id}[/red]")
                return
            
            # 获取日报内容
            items = await content_repo.get_by_column(
                column_id=None,
                date=report.date
            )
            
            if format == "json":
                import json
                data = {
                    "id": report.id,
                    "title": report.title,
                    "date": report.date.isoformat() if report.date else None,
                    "total_items": report.total_items,
                    "is_sent": report.is_sent,
                    "items": [
                        {
                            "title": item.title,
                            "url": item.url,
                            "source": item.source,
                            "summary": item.summary
                        }
                        for item in items
                    ]
                }
                console.print(json.dumps(data, indent=2, ensure_ascii=False))
            
            elif format == "html":
                from src.output.formatter import HTMLFormatter
                formatter = HTMLFormatter()
                # 简化输出
                console.print(f"[yellow]HTML 格式暂不支持直接显示，请导出查看[/yellow]")
            
            else:  # markdown
                console.print(f"\n[bold]{report.title}[/bold]\n")
                console.print(f"日期: {report.date.strftime('%Y-%m-%d') if report.date else '-'}")
                console.print(f"内容数: {report.total_items}")
                console.print(f"推送状态: {'已推送' if report.is_sent else '未推送'}")
                console.print("\n" + "━" * 50 + "\n")
                
                for i, item in enumerate(items[:20], 1):  # 最多显示20条
                    console.print(f"{i}. [bold]{item.title}[/bold]")
                    console.print(f"   [dim]{item.url}[/dim]")
                    if item.summary:
                        console.print(f"   {item.summary[:100]}...")
                    console.print()
    
    asyncio.run(_view())


@reports.command("diff")
@click.argument("report_id1")
@click.argument("report_id2")
def reports_diff(report_id1: str, report_id2: str):
    """对比两份日报"""
    async def _diff():
        from src.database import get_session, DailyReportRepository, ContentRepository
        
        async with get_session() as session:
            repo = DailyReportRepository(session)
            content_repo = ContentRepository(session)
            
            # 获取两份日报
            report1 = await repo.get_by_id(report_id1)
            report2 = await repo.get_by_id(report_id2)
            
            if not report1 or not report2:
                console.print("[red]日报不存在[/red]")
                return
            
            # 获取内容
            items1 = await content_repo.get_by_column(date=report1.date)
            items2 = await content_repo.get_by_column(date=report2.date)
            
            urls1 = {item.url for item in items1}
            urls2 = {item.url for item in items2}
            
            # 对比
            only_in_1 = urls1 - urls2
            only_in_2 = urls2 - urls1
            in_both = urls1 & urls2
            
            console.print(f"\n[bold]📊 日报对比[/bold]\n")
            console.print(f"日报 1: {report1.title} ({report1.date.strftime('%Y-%m-%d') if report1.date else '-'})")
            console.print(f"日报 2: {report2.title} ({report2.date.strftime('%Y-%m-%d') if report2.date else '-'})")
            console.print()
            
            console.print(f"[green]共同内容: {len(in_both)} 条[/green]")
            console.print(f"[blue]仅在日报 1: {len(only_in_1)} 条[/blue]")
            console.print(f"[yellow]仅在日报 2: {len(only_in_2)} 条[/yellow]")
            console.print()
            
            if only_in_1:
                console.print("[bold blue]仅在日报 1 中的内容:[/bold blue]")
                for url in list(only_in_1)[:5]:
                    item = next((i for i in items1 if i.url == url), None)
                    if item:
                        console.print(f"  • {item.title}")
                if len(only_in_1) > 5:
                    console.print(f"  ... 还有 {len(only_in_1) - 5} 条")
                console.print()
            
            if only_in_2:
                console.print("[bold yellow]仅在日报 2 中的内容:[/bold yellow]")
                for url in list(only_in_2)[:5]:
                    item = next((i for i in items2 if i.url == url), None)
                    if item:
                        console.print(f"  • {item.title}")
                if len(only_in_2) > 5:
                    console.print(f"  ... 还有 {len(only_in_2) - 5} 条")
    
    asyncio.run(_diff())


@reports.command("stats")
def reports_stats():
    """查看性能统计"""
    async def _stats():
        from src.metrics import print_performance_report
        await print_performance_report()
    
    asyncio.run(_stats())


@reports.command("export")
@click.argument("report_id")
@click.option("--output", "-o", help="输出文件路径")
@click.option("--format", "-f", type=click.Choice(["markdown", "html", "json"]), default="markdown", help="导出格式")
def reports_export(report_id: str, output: str, format: str):
    """导出日报"""
    async def _export():
        from src.database import get_session, DailyReportRepository, ContentRepository
        
        async with get_session() as session:
            repo = DailyReportRepository(session)
            content_repo = ContentRepository(session)
            
            report = await repo.get_by_id(report_id)
            if not report:
                console.print(f"[red]日报不存在: {report_id}[/red]")
                return
            
            items = await content_repo.get_by_column(date=report.date)
            
            # 确定输出文件
            if not output:
                output = f"report_{report_id}_{format}"
                if format == "markdown":
                    output += ".md"
                elif format == "html":
                    output += ".html"
                else:
                    output += ".json"
            
            # 生成内容
            if format == "markdown":
                from src.output.formatter import MarkdownFormatter
                formatter = MarkdownFormatter()
                # 简化：直接生成
                content = f"# {report.title}\n\n"
                content += f"日期: {report.date.strftime('%Y-%m-%d') if report.date else '-'}\n\n"
                for item in items:
                    content += f"## {item.title}\n"
                    content += f"来源: {item.source}\n"
                    content += f"链接: {item.url}\n"
                    if item.summary:
                        content += f"\n{item.summary}\n"
                    content += "\n---\n\n"
            
            elif format == "html":
                content = f"<h1>{report.title}</h1>"
                content += f"<p>日期: {report.date.strftime('%Y-%m-%d') if report.date else '-'}</p>"
                for item in items:
                    content += f"<h2>{item.title}</h2>"
                    content += f"<p>来源: {item.source}</p>"
                    content += f"<p><a href='{item.url}'>阅读原文</a></p>"
                    if item.summary:
                        content += f"<p>{item.summary}</p>"
                    content += "<hr>"
            
            else:  # json
                import json
                data = {
                    "report": {
                        "id": report.id,
                        "title": report.title,
                        "date": report.date.isoformat() if report.date else None,
                        "total_items": report.total_items
                    },
                    "items": [
                        {
                            "title": item.title,
                            "url": item.url,
                            "source": item.source,
                            "summary": item.summary
                        }
                        for item in items
                    ]
                }
                content = json.dumps(data, indent=2, ensure_ascii=False)
            
            # 写入文件
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            
            console.print(f"[green]✅ 日报已导出到: {output}[/green]")
    
    asyncio.run(_export())


# ============ 测试命令 ============

@cli.group()
def test():
    """测试工具 - 测试采集器、推送渠道等"""
    pass


@test.command("source")
@click.argument("source_name")
def test_source(source_name: str):
    """测试单个数据源"""
    async def _test():
        from src.config import get_column_config
        from src.collector import CollectorManager, RSSCollector, HackerNewsCollector, BilibiliCollector, XiaohongshuCollector
        
        console.print(f"[bold]测试数据源: {source_name}[/bold]\n")
        
        # 查找数据源配置
        col_config = get_column_config()
        columns = col_config.get_columns(enabled_only=False)
        
        source_config = None
        source_type = None
        
        for col in columns:
            for source in col.get("sources", []):
                if source.get("name") == source_name:
                    source_config = source
                    source_type = source.get("type")
                    break
            if source_config:
                break
        
        if not source_config:
            console.print(f"[red]✗ 未找到数据源: {source_name}[/red]")
            console.print("\n可用数据源:")
            for col in columns:
                for source in col.get("sources", []):
                    console.print(f"  • {source.get('name')} ({source.get('type')})")
            return
        
        # 创建对应采集器
        try:
            if source_type == "rss":
                collector = RSSCollector(source_name, source_config)
            elif source_type == "api":
                provider = source_config.get("provider")
                if provider == "hackernews":
                    collector = HackerNewsCollector(source_name, source_config)
                else:
                    console.print(f"[red]✗ 不支持的 API 提供商: {provider}[/red]")
                    return
            elif source_type == "bilibili":
                collector = BilibiliCollector(source_name, source_config)
            elif source_type == "xiaohongshu":
                collector = XiaohongshuCollector(source_name, source_config)
            else:
                console.print(f"[red]✗ 不支持的采集器类型: {source_type}[/red]")
                return
            
            # 执行采集
            with console.status(f"[bold green]正在采集 {source_name}..."):
                result = await collector.collect()
            
            # 显示结果
            if result.success:
                console.print(f"[green]✓ 采集成功[/green]")
                console.print(f"  采集数量: {len(result.items)} 条")
                console.print(f"  消息: {result.message}")
                
                if result.items:
                    console.print("\n[bold]最新内容:[/bold]")
                    for i, item in enumerate(result.items[:3], 1):
                        console.print(f"  {i}. {item.title[:50]}...")
                        console.print(f"     [dim]{item.url[:60]}...[/dim]")
            else:
                console.print(f"[red]✗ 采集失败: {result.message}[/red]")
        
        except Exception as e:
            console.print(f"[red]✗ 测试出错: {e}[/red]")
        
        finally:
            if 'collector' in locals():
                await collector.close()
    
    asyncio.run(_test())


@test.command("channel")
@click.argument("channel_name")
def test_channel(channel_name: str):
    """测试推送渠道"""
    async def _test():
        from src.config import get_settings
        from src.output.publisher import Publisher
        from src.models import DailyReport, ChannelType
        
        settings = get_settings()
        console.print(f"[bold]测试推送渠道: {channel_name}[/bold]\n")
        
        # 检查配置
        channel_configs = {
            "telegram": (settings.telegram_bot_token, settings.telegram_chat_id),
            "slack": (settings.slack_bot_token, settings.slack_channel),
            "discord": (settings.discord_bot_token, settings.discord_channel_id),
            "email": (settings.smtp_host, settings.email_to),
        }
        
        if channel_name.lower() not in channel_configs:
            console.print(f"[red]✗ 不支持的渠道: {channel_name}[/red]")
            console.print(f"\n支持的渠道: {', '.join(channel_configs.keys())}")
            return
        
        config = channel_configs[channel_name.lower()]
        if not all(config):
            console.print(f"[red]✗ {channel_name} 配置不完整[/red]")
            console.print("\n请检查环境变量配置:")
            env_vars = {
                "telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
                "slack": ["SLACK_BOT_TOKEN", "SLACK_CHANNEL"],
                "discord": ["DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID"],
                "email": ["SMTP_HOST", "EMAIL_TO"],
            }
            for var in env_vars.get(channel_name.lower(), []):
                console.print(f"  - {var}")
            return
        
        # 创建测试日报
        from datetime import datetime, timezone
        test_report = DailyReport(
            id="test_report",
            date=datetime.now(timezone.utc),
            user_id="test",
            title="测试日报 - Daily Agent 连接测试",
            total_items=0
        )
        
        # 尝试推送
        try:
            publisher = Publisher()
            
            channel_type = ChannelType(channel_name.lower())
            
            with console.status(f"[bold green]正在测试 {channel_name} 连接..."):
                results = await publisher.publish(
                    report=test_report,
                    columns_config=[],
                    items_by_column={},
                    channels=[channel_type]
                )
            
            result = results.get(channel_type)
            if result and result.success:
                console.print(f"[green]✓ 连接测试成功！[/green]")
                console.print(f"  消息: {result.message}")
            else:
                console.print(f"[red]✗ 连接测试失败[/red]")
                if result:
                    console.print(f"  错误: {result.message}")
        
        except Exception as e:
            console.print(f"[red]✗ 测试出错: {e}[/red]")
    
    asyncio.run(_test())


@test.command("llm")
def test_llm():
    """测试 LLM 连接"""
    async def _test():
        from src.llm_config import get_llm_manager
        
        console.print("[bold]测试 LLM 连接[/bold]\n")
        
        manager = get_llm_manager()
        config = manager.get_current_config()
        
        if not config.is_configured():
            console.print("[red]✗ LLM 未配置[/red]")
            console.print("\n请运行: [cyan]python -m src.cli llm setup[/cyan]")
            return
        
        console.print(f"提供商: {config.provider}")
        console.print(f"模型: {config.model}")
        console.print("")
        
        with console.status("[bold green]正在测试 API 连接..."):
            success, message = await manager.test_connection()
        
        if success:
            console.print(f"[green]✓ 连接成功[/green]")
            console.print(f"  {message}")
        else:
            console.print(f"[red]✗ 连接失败[/red]")
            console.print(f"  {message}")
    
    asyncio.run(_test())


@test.command("rules")
@click.option("--column", "-c", help="测试分栏规则")
@click.option("--source", "-s", help="测试数据源规则")
def test_rules(column: str, source: str):
    """测试过滤规则效果"""
    from src.rule_tester import cli_test_rules
    cli_test_rules(column_id=column, source_name=source)


# ============ 快捷操作命令 ============

@cli.group()
def disable():
    """禁用数据源或分栏"""
    pass


@disable.command("source")
@click.argument("source_name")
def disable_source(source_name: str):
    """临时禁用某个数据源"""
    async def _disable():
        console.print(f"[yellow]禁用数据源: {source_name}[/yellow]")
        console.print("\n[dim]提示: 此功能需要修改 config/columns.yaml[/dim]")
        console.print("请手动编辑配置文件，将对应源的 enabled 设为 false")
    
    asyncio.run(_disable())


@disable.command("column")
@click.argument("column_id")
def disable_column(column_id: str):
    """临时禁用某个分栏"""
    async def _disable():
        console.print(f"[yellow]禁用分栏: {column_id}[/yellow]")
        console.print("\n[dim]提示: 此功能需要修改 config/columns.yaml[/dim]")
        console.print("请手动编辑配置文件，将对应分栏的 enabled 设为 false")
    
    asyncio.run(_disable())


@cli.group()
def enable():
    """启用数据源或分栏"""
    pass


@enable.command("source")
@click.argument("source_name")
def enable_source(source_name: str):
    """启用某个数据源"""
    console.print(f"[green]启用数据源: {source_name}[/green]")
    console.print("\n[dim]提示: 此功能需要修改 config/columns.yaml[/dim]")


@enable.command("column")
@click.argument("column_id")
def enable_column(column_id: str):
    """启用某个分栏"""
    console.print(f"[green]启用分栏: {column_id}[/green]")
    console.print("\n[dim]提示: 此功能需要修改 config/columns.yaml[/dim]")


# ============ 插件管理命令 ============

@cli.group()
def plugin():
    """插件管理 - 管理自定义采集器、处理器、推送渠道"""
    pass


@plugin.command("list")
def plugin_list():
    """列出所有可用插件"""
    from src.plugin_system import cli_list_plugins
    cli_list_plugins()


@plugin.command("create")
@click.argument("name")
@click.option("--type", "plugin_type", type=click.Choice(["collector", "processor", "publisher"]), 
              default="collector", help="插件类型")
def plugin_create(name: str, plugin_type: str):
    """创建插件模板"""
    from src.plugin_system import cli_create_plugin
    cli_create_plugin(name, plugin_type)


@plugin.command("load")
@click.argument("name")
def plugin_load(name: str):
    """加载插件"""
    async def _load():
        from src.plugin_system import get_plugin_manager
        
        manager = get_plugin_manager()
        plugin = manager.load_plugin(name)
        
        if plugin:
            success = await manager.initialize_plugin(name)
            if success:
                console.print(f"[green]✓ 插件 {name} 加载成功[/green]")
            else:
                console.print(f"[red]✗ 插件 {name} 初始化失败[/red]")
        else:
            console.print(f"[red]✗ 插件 {name} 加载失败[/red]")
    
    asyncio.run(_load())


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


@cli.command()
def preview():
    """预览今日日报（不保存）"""
    async def _preview():
        from src.service import DailyAgentService
        from src.output.formatter import MarkdownFormatter
        
        console.print("[bold]生成日报预览...[/bold]\n")
        
        service = DailyAgentService()
        await service.initialize()
        
        # 采集
        with console.status("[bold green]正在采集内容..."):
            results = await service.collect_all()
        
        total = sum(len(r.items) for r in results.values() if r.success)
        console.print(f"✓ 采集完成: {total} 条内容\n")
        
        # 显示采集结果
        table = Table(title="采集结果")
        table.add_column("来源", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("数量", justify="right")
        
        for name, result in results.items():
            status = "✓" if result.success else "✗"
            table.add_row(name, status, str(len(result.items)))
        
        console.print(table)
        console.print("\n[yellow]注意: 这只是预览，未生成正式日报[/yellow]")
        console.print("运行 [cyan]python -m src.cli generate[/cyan] 生成正式日报")
    
    asyncio.run(_preview())


if __name__ == "__main__":
    cli()
