"""
进度显示和错误处理增强模块
提供统一的进度条和错误处理
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.style import Style

console = Console()


class ProgressManager:
    """进度管理器"""

    def __init__(self, description: str = "处理中..."):
        self.description = description
        self.progress: Optional[Progress] = None
        self.task_id: Optional[int] = None

    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=True,
        )
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=100)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()

    def update(self, completed: int, total: int, description: str = None):
        """更新进度"""
        if self.progress and self.task_id is not None:
            self.progress.update(
                self.task_id,
                completed=completed,
                total=total,
                description=description or self.description,
            )

    def advance(self, amount: int = 1):
        """前进指定步数"""
        if self.progress and self.task_id is not None:
            self.progress.advance(self.task_id, amount)


@asynccontextmanager
async def async_progress(
    description: str,
    total: int = 100,
) -> AsyncGenerator[Progress, None]:
    """异步进度条上下文管理器"""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )

    progress.start()
    task_id = progress.add_task(description, total=total)

    try:
        yield progress
    finally:
        progress.stop()


class ErrorHandler:
    """统一错误处理器"""

    ERROR_TYPES = {
        "config": {
            "icon": "🔧",
            "title": "配置错误",
            "color": "yellow",
            "suggestions": [
                "运行: python daily.py --init 重新配置",
                "检查 .env 文件中的 API Key",
                "运行: python daily.py check 诊断问题",
            ],
        },
        "network": {
            "icon": "🌐",
            "title": "网络错误",
            "color": "yellow",
            "suggestions": [
                "检查网络连接",
                "检查代理设置",
                "稍后重试",
            ],
        },
        "llm": {
            "icon": "🤖",
            "title": "LLM 错误",
            "color": "yellow",
            "suggestions": [
                "检查 API Key 是否有效",
                "检查 API 余额",
                "尝试切换到其他模型",
                "系统会使用规则摘要作为降级方案",
            ],
        },
        "auth": {
            "icon": "🔐",
            "title": "认证错误",
            "color": "red",
            "suggestions": [
                "运行: python daily.py auth <source> 重新认证",
                "检查认证是否过期",
                "确认账号权限",
            ],
        },
        "database": {
            "icon": "🗄️",
            "title": "数据库错误",
            "color": "red",
            "suggestions": [
                "检查磁盘空间",
                "检查文件权限",
                "尝试删除 data/daily.db 重新初始化",
            ],
        },
        "unknown": {
            "icon": "❌",
            "title": "未知错误",
            "color": "red",
            "suggestions": [
                "运行: python daily.py check 诊断问题",
                "查看日志获取详细信息",
                "提交 issue 寻求帮助",
            ],
        },
    }

    @classmethod
    def classify_error(cls, error: Exception) -> str:
        """分类错误类型"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        if any(kw in error_str for kw in ["api key", "authentication", "unauthorized", "401"]):
            return "auth"
        elif any(kw in error_str for kw in ["config", "configuration", "setting"]):
            return "config"
        elif any(kw in error_str for kw in ["connection", "timeout", "network", "dns", "refused"]):
            return "network"
        elif any(kw in error_str for kw in ["llm", "openai", "gpt", "claude", "api error"]):
            return "llm"
        elif any(kw in error_str for kw in ["database", "sqlite", "disk", "permission denied"]):
            return "database"
        else:
            return "unknown"

    @classmethod
    def handle(cls, error: Exception, context: str = ""):
        """处理并显示错误"""
        error_type = cls.classify_error(error)
        error_info = cls.ERROR_TYPES[error_type]

        # 显示错误面板
        from rich.panel import Panel

        content = f"""
[bold {error_info['color']}]{error_info['icon']} {error_info['title']}[/{error_info['color']}]

{context}

错误详情: {error}

[bold]建议解决方案:[/bold]
"""
        for suggestion in error_info["suggestions"]:
            content += f"  • {suggestion}\n"

        console.print(Panel(content, border_style=error_info["color"]))

    @classmethod
    def success(cls, message: str):
        """显示成功信息"""
        console.print(f"[bold green]✓[/bold green] {message}")

    @classmethod
    def warning(cls, message: str):
        """显示警告信息"""
        console.print(f"[bold yellow]⚠[/bold yellow] {message}")

    @classmethod
    def info(cls, message: str):
        """显示信息"""
        console.print(f"[dim]ℹ {message}[/dim]")


# 装饰器：为异步函数添加进度显示
def with_progress(description: str, total: int = 100):
    """装饰器：为函数添加进度显示"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with ProgressManager(description) as pm:
                kwargs['_progress'] = pm
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# 装饰器：统一错误处理
def with_error_handler(context: str = ""):
    """装饰器：统一错误处理"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                ErrorHandler.handle(e, context)
                raise
        return wrapper
    return decorator
