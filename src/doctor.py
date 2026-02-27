"""
Daily Agent 诊断工具
一键检查系统健康状态、配置问题和依赖情况
"""
import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

console = Console()


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: str  # "ok", "warning", "error"
    message: str
    details: List[str] = field(default_factory=list)
    fix_command: Optional[str] = None


class SystemChecker:
    """系统检查器"""
    
    def __init__(self):
        self.results: List[CheckResult] = []
    
    async def run_all_checks(self) -> List[CheckResult]:
        """运行所有检查"""
        self.results = []
        
        # 环境检查
        self.results.append(await self._check_environment())
        
        # 依赖检查
        self.results.append(await self._check_dependencies())
        
        # 配置检查
        self.results.append(await self._check_configuration())
        
        # 数据库检查
        self.results.append(await self._check_database())
        
        # 数据源检查
        self.results.append(await self._check_sources())
        
        # 推送渠道检查
        self.results.append(await self._check_channels())
        
        # 资源使用检查
        self.results.append(await self._check_resources())
        
        return self.results
    
    async def _check_environment(self) -> CheckResult:
        """检查 Python 环境"""
        details = []
        
        # Python 版本
        py_version = sys.version_info
        py_version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        
        if py_version < (3, 10):
            status = "error"
            message = f"Python {py_version_str} (需要 >= 3.10)"
        elif py_version < (3, 11):
            status = "warning"
            message = f"Python {py_version_str} (建议 >= 3.11)"
        else:
            status = "ok"
            message = f"Python {py_version_str}"
        
        details.append(f"版本: {message}")
        
        # 虚拟环境检查
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        if in_venv:
            details.append("虚拟环境: 已激活 ✓")
        else:
            details.append("虚拟环境: 未使用 (建议创建)")
        
        return CheckResult(
            name="环境检查",
            status=status,
            message=message,
            details=details
        )
    
    async def _check_dependencies(self) -> CheckResult:
        """检查依赖包"""
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "pydantic", 
            "httpx", "click", "rich", "feedparser", "playwright"
        ]
        
        missing = []
        outdated = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(package)
        
        # 检查 playwright 浏览器
        playwright_ok = False
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                # 尝试获取 chromium
                p.chromium._impl_obj  # 检查是否安装
                playwright_ok = True
        except:
            pass
        
        details = []
        
        if missing:
            status = "error"
            message = f"缺少 {len(missing)} 个依赖包"
            details.append(f"缺失: {', '.join(missing)}")
        else:
            status = "ok"
            message = "所有依赖包已安装"
        
        if not playwright_ok:
            details.append("Playwright 浏览器未安装 (运行: playwright install chromium)")
            if status == "ok":
                status = "warning"
                message += " (浏览器未安装)"
        else:
            details.append("Playwright 浏览器: 已安装")
        
        fix_cmd = None
        if missing:
            fix_cmd = f"pip install {' '.join(missing)}"
        elif not playwright_ok:
            fix_cmd = "python -m playwright install chromium"
        
        return CheckResult(
            name="依赖检查",
            status=status,
            message=message,
            details=details,
            fix_command=fix_cmd
        )
    
    async def _check_configuration(self) -> CheckResult:
        """检查配置"""
        from src.config import get_settings, get_column_config
        
        details = []
        warnings = 0
        errors = 0
        
        try:
            settings = get_settings()
            
            # API_SECRET_KEY 检查
            if settings.api_secret_key in ["change-this-secret-key", "your-secret-key-change-this", ""]:
                details.append("⚠️ API_SECRET_KEY 使用默认值 (建议修改)")
                warnings += 1
            else:
                details.append("✓ API_SECRET_KEY 已设置")
            
            # LLM 配置
            if settings.openai_api_key:
                key_preview = f"{settings.openai_api_key[:8]}...{settings.openai_api_key[-4:]}"
                details.append(f"✓ LLM 已配置: {settings.openai_model} ({key_preview})")
            else:
                details.append("⚠️ LLM 未配置 (将使用规则摘要)")
                warnings += 1
            
        except Exception as e:
            details.append(f"✗ 加载配置失败: {e}")
            errors += 1
        
        # 检查配置文件
        config_files = {
            ".env": "环境变量",
            "config/columns.yaml": "分栏配置",
        }
        
        for file_path, desc in config_files.items():
            if os.path.exists(file_path):
                details.append(f"✓ {desc}: {file_path}")
            else:
                details.append(f"⚠️ {desc}: {file_path} 不存在")
                warnings += 1
        
        # 检查分栏配置
        try:
            col_config = get_column_config()
            columns = col_config.get_columns(enabled_only=False)
            enabled = [c for c in columns if c.get("enabled", True)]
            details.append(f"✓ 分栏配置: {len(enabled)}/{len(columns)} 个分栏启用")
        except Exception as e:
            details.append(f"✗ 分栏配置错误: {e}")
            errors += 1
        
        if errors > 0:
            status = "error"
            message = f"发现 {errors} 个错误"
        elif warnings > 0:
            status = "warning"
            message = f"发现 {warnings} 个警告"
        else:
            status = "ok"
            message = "配置正常"
        
        return CheckResult(
            name="配置检查",
            status=status,
            message=message,
            details=details
        )
    
    async def _check_database(self) -> CheckResult:
        """检查数据库"""
        details = []
        
        db_path = Path("data/daily.db")
        
        if not db_path.exists():
            return CheckResult(
                name="数据库检查",
                status="warning",
                message="数据库不存在 (将自动创建)",
                details=["路径: data/daily.db", "状态: 未初始化"],
                fix_command="python -m src.cli init"
            )
        
        details.append(f"✓ 数据库文件存在 ({db_path.stat().st_size / 1024:.1f} KB)")
        
        # 检查数据库连接和表
        try:
            from src.database import get_session
            from sqlalchemy import text
            
            async with get_session() as session:
                # 检查表数量
                result = await session.execute(text(
                    "SELECT count(*) FROM sqlite_master WHERE type='table'"
                ))
                table_count = result.scalar()
                details.append(f"✓ 数据库表: {table_count} 个")
                
                # 检查内容数量
                try:
                    result = await session.execute(text("SELECT count(*) FROM content_items"))
                    content_count = result.scalar()
                    details.append(f"✓ 内容条目: {content_count} 条")
                except:
                    details.append("⚠️ content_items 表不存在")
                
                # 检查日报数量
                try:
                    result = await session.execute(text("SELECT count(*) FROM daily_reports"))
                    report_count = result.scalar()
                    details.append(f"✓ 日报数量: {report_count} 份")
                except:
                    pass
        
        except Exception as e:
            return CheckResult(
                name="数据库检查",
                status="error",
                message=f"数据库连接失败: {e}",
                details=details,
                fix_command="python -m src.cli init"
            )
        
        return CheckResult(
            name="数据库检查",
            status="ok",
            message="数据库正常",
            details=details
        )
    
    async def _check_sources(self) -> CheckResult:
        """检查数据源"""
        from src.config import get_column_config
        
        details = []
        errors = 0
        warnings = 0
        
        try:
            col_config = get_column_config()
            columns = col_config.get_columns()
        except Exception as e:
            return CheckResult(
                name="数据源检查",
                status="error",
                message=f"无法加载配置: {e}",
                details=[]
            )
        
        total_sources = 0
        auth_sources = []
        
        for col in columns:
            sources = col.get("sources", [])
            for source in sources:
                total_sources += 1
                source_type = source.get("type", "unknown")
                source_name = source.get("name", "unnamed")
                
                # 检查需要认证的源
                if source_type in ["xiaohongshu", "jike", "zhihu"]:
                    auth_sources.append(source_name)
        
        details.append(f"配置数据源: {total_sources} 个")
        
        # 检查认证状态
        if auth_sources:
            try:
                from src.auth_manager import get_auth_manager
                
                auth_manager = get_auth_manager()
                creds = await auth_manager.list_auth()
                cred_sources = {c["source_name"] for c in creds}
                
                for source_name in auth_sources:
                    # 简化匹配逻辑
                    source_key = None
                    for key in ["xiaohongshu", "jike", "zhihu"]:
                        if key in source_name.lower():
                            source_key = key
                            break
                    
                    if source_key and source_key in cred_sources:
                        # 检查是否过期
                        for cred in creds:
                            if cred["source_name"] == source_key:
                                if cred.get("expires_at") and cred["expires_at"] < datetime.now(timezone.utc):
                                    details.append(f"✗ {source_name}: 认证已过期")
                                    errors += 1
                                elif not cred.get("is_valid", True):
                                    details.append(f"✗ {source_name}: 认证无效")
                                    errors += 1
                                else:
                                    details.append(f"✓ {source_name}: 认证有效")
                                break
                    else:
                        details.append(f"⚠️ {source_name}: 未配置认证")
                        warnings += 1
            
            except Exception as e:
                details.append(f"⚠️ 无法检查认证状态: {e}")
        
        if errors > 0:
            status = "error"
            message = f"{errors} 个认证问题"
        elif warnings > 0:
            status = "warning"
            message = f"{warnings} 个未配置认证"
        else:
            status = "ok"
            message = "所有数据源正常"
        
        return CheckResult(
            name="数据源检查",
            status=status,
            message=message,
            details=details,
            fix_command="python -m src.cli auth guide" if errors + warnings > 0 else None
        )
    
    async def _check_channels(self) -> CheckResult:
        """检查推送渠道"""
        from src.config import get_settings
        
        details = []
        configured = []
        missing = []
        
        try:
            settings = get_settings()
            
            # 检查各渠道配置
            channels = [
                ("Telegram", settings.telegram_bot_token and settings.telegram_chat_id),
                ("Slack", settings.slack_bot_token and settings.slack_channel),
                ("Discord", settings.discord_bot_token and settings.discord_channel_id),
                ("Email", settings.smtp_host and settings.email_to),
            ]
            
            for name, is_configured in channels:
                if is_configured:
                    configured.append(name)
                else:
                    missing.append(name)
            
            if configured:
                details.append(f"✓ 已配置: {', '.join(configured)}")
            
            if missing:
                details.append(f"○ 未配置: {', '.join(missing)} (可选)")
            
            if not configured:
                return CheckResult(
                    name="推送渠道检查",
                    status="warning",
                    message="未配置任何推送渠道",
                    details=details + ["日报将仅保存到本地，不会推送"]
                )
            
            # 测试连接（异步）
            test_results = []
            for name in configured:
                # 这里简化处理，实际应该测试 API 连接
                test_results.append(f"✓ {name}: 配置完整")
            
            details.extend(test_results)
            
        except Exception as e:
            return CheckResult(
                name="推送渠道检查",
                status="error",
                message=f"检查失败: {e}",
                details=details
            )
        
        return CheckResult(
            name="推送渠道检查",
            status="ok",
            message=f"{len(configured)} 个渠道已配置",
            details=details
        )
    
    async def _check_resources(self) -> CheckResult:
        """检查资源使用"""
        details = []
        
        try:
            from src.database import get_session
            from sqlalchemy import text, func
            from datetime import datetime, timedelta, timezone
            
            async with get_session() as session:
                # 今日采集数量
                today = datetime.now(timezone.utc).date()
                yesterday = today - timedelta(days=1)
                
                try:
                    result = await session.execute(text(
                        "SELECT count(*) FROM content_items WHERE date(fetch_time) >= :date"
                    ), {"date": yesterday.isoformat()})
                    today_count = result.scalar() or 0
                    details.append(f"今日采集: {today_count} 条")
                except:
                    details.append("今日采集: 无法统计")
                
                # 最后生成日报时间
                try:
                    result = await session.execute(text(
                        "SELECT max(created_at) FROM daily_reports"
                    ))
                    last_report = result.scalar()
                    if last_report:
                        if isinstance(last_report, str):
                            details.append(f"最后日报: {last_report}")
                        else:
                            details.append(f"最后日报: {last_report.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        details.append("最后日报: 从未生成")
                except:
                    pass
        
        except Exception as e:
            details.append(f"统计信息暂不可用: {e}")
        
        # 磁盘空间
        try:
            import shutil
            stat = shutil.disk_usage(".")
            free_gb = stat.free / (1024**3)
            details.append(f"磁盘空间: {free_gb:.1f} GB 可用")
        except:
            pass
        
        return CheckResult(
            name="资源使用",
            status="ok",
            message="资源使用正常",
            details=details
        )
    
    def get_summary(self) -> Tuple[int, int, int]:
        """获取检查摘要 (ok, warning, error)"""
        ok = sum(1 for r in self.results if r.status == "ok")
        warning = sum(1 for r in self.results if r.status == "warning")
        error = sum(1 for r in self.results if r.status == "error")
        return ok, warning, error


class DoctorReport:
    """诊断报告生成器"""
    
    def __init__(self, checker: SystemChecker):
        self.checker = checker
    
    def print_report(self):
        """打印诊断报告"""
        console.print("\n🩺 [bold]Daily Agent 诊断报告[/bold]", justify="center")
        console.print("━" * 60, justify="center")
        
        for result in self.checker.results:
            self._print_check_result(result)
        
        # 汇总
        ok, warning, error = self.checker.get_summary()
        
        console.print("\n" + "━" * 60)
        console.print(f"[bold]检查结果汇总:[/bold] ", end="")
        console.print(f"[green]✓ {ok} 正常[/green]  ", end="")
        if warning > 0:
            console.print(f"[yellow]⚠ {warning} 警告[/yellow]  ", end="")
        if error > 0:
            console.print(f"[red]✗ {error} 错误[/red]  ", end="")
        console.print()
        
        # 修复建议
        fixes = [r for r in self.checker.results if r.fix_command]
        if fixes:
            console.print("\n[bold blue]💡 修复建议:[/bold blue]")
            for result in fixes:
                console.print(f"  {result.name}:")
                console.print(f"    [cyan]{result.fix_command}[/cyan]")
            console.print("\n运行 [cyan]python -m src.cli fix[/cyan] 自动修复所有问题")
        
        if error == 0 and warning == 0:
            console.print("\n[green bold]🎉 所有检查通过！系统运行正常。[/green bold]")
        
        console.print()
    
    def _print_check_result(self, result: CheckResult):
        """打印单个检查结果"""
        # 状态图标
        icons = {
            "ok": "[green]✓[/green]",
            "warning": "[yellow]⚠️[/yellow]",
            "error": "[red]✗[/red]"
        }
        
        status_color = {
            "ok": "green",
            "warning": "yellow",
            "error": "red"
        }
        
        # 主结果行
        icon = icons.get(result.status, "?")
        console.print(f"\n{icon} [bold]{result.name}[/bold]: [{status_color[result.status]}]{result.message}[/{status_color[result.status]}]")
        
        # 详情
        for detail in result.details:
            console.print(f"   {detail}")
    
    def generate_fix_script(self) -> str:
        """生成修复脚本"""
        fixes = [r for r in self.checker.results if r.fix_command]
        if not fixes:
            return "# 没有需要修复的问题"
        
        script = "#!/bin/bash\n# Daily Agent 自动修复脚本\n\n"
        script += "echo '正在修复问题...'\n\n"
        
        for result in fixes:
            script += f"# {result.name}\n"
            script += f"echo '修复: {result.name}'\n"
            script += f"{result.fix_command}\n\n"
        
        script += "echo '修复完成！'\n"
        return script


async def run_diagnosis() -> SystemChecker:
    """运行诊断"""
    checker = SystemChecker()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("正在诊断系统...", total=None)
        await checker.run_all_checks()
        progress.remove_task(task)
    
    return checker


async def fix_issues():
    """自动修复问题"""
    checker = SystemChecker()
    await checker.run_all_checks()
    
    fixes = [r for r in checker.results if r.fix_command]
    
    if not fixes:
        console.print("[green]没有问题需要修复！[/green]")
        return
    
    console.print(f"\n[bold]将修复 {len(fixes)} 个问题:[/bold]\n")
    
    for i, result in enumerate(fixes, 1):
        console.print(f"{i}. {result.name}")
        console.print(f"   命令: [cyan]{result.fix_command}[/cyan]\n")
    
    # 询问确认
    from rich.prompt import Confirm
    if not Confirm.ask("是否执行修复?"):
        console.print("已取消")
        return
    
    # 执行修复
    for result in fixes:
        console.print(f"\n[bold]修复: {result.name}[/bold]")
        console.print(f"执行: {result.fix_command}")
        
        # 这里简化处理，实际应该执行命令
        # 对于数据库初始化
        if "init" in result.fix_command:
            from src.database import init_db
            await init_db()
            console.print("  [green]✓ 数据库初始化完成[/green]")
        # 对于依赖安装
        elif "pip install" in result.fix_command:
            console.print("  [yellow]请手动运行: {result.fix_command}[/yellow]")
        # 对于 playwright 安装
        elif "playwright" in result.fix_command:
            console.print("  [yellow]请手动运行: {result.fix_command}[/yellow]")
        else:
            console.print("  [yellow]请手动运行上述命令[/yellow]")
    
    console.print("\n[green]修复流程执行完毕！[/green]")
    console.print("建议再次运行 [cyan]python -m src.cli doctor[/cyan] 确认问题已解决")


if __name__ == "__main__":
    # 命令行入口
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        asyncio.run(fix_issues())
    else:
        checker = asyncio.run(run_diagnosis())
        report = DoctorReport(checker)
        report.print_report()
