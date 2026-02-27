"""
进度追踪器模块
提供采集、处理、生成等操作的实时进度显示
"""
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, 
    TaskProgressColumn, TimeRemainingColumn
)
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass
class TaskInfo:
    """任务信息"""
    name: str
    total: int = 100
    completed: int = 0
    status: str = "pending"  # pending, running, done, error
    message: str = ""
    details: Dict = field(default_factory=dict)


class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self, title: str = "任务进度"):
        self.title = title
        self.tasks: Dict[str, TaskInfo] = {}
        self.progress: Optional[Progress] = None
        self._task_ids: Dict[str, any] = {}
        self._callbacks: List[Callable] = []
    
    def add_task(self, task_id: str, name: str, total: int = 100) -> TaskInfo:
        """添加任务"""
        task = TaskInfo(name=name, total=total)
        self.tasks[task_id] = task
        
        if self.progress:
            self._task_ids[task_id] = self.progress.add_task(
                f"[cyan]{name}[/cyan]",
                total=total
            )
        
        return task
    
    def update_task(self, task_id: str, completed: Optional[int] = None, 
                    advance: Optional[int] = None, message: str = "",
                    status: Optional[str] = None):
        """更新任务进度"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        if completed is not None:
            task.completed = completed
        elif advance is not None:
            task.completed += advance
        
        if message:
            task.message = message
        
        if status:
            task.status = status
        
        # 更新 Rich Progress
        if self.progress and task_id in self._task_ids:
            update_args = {"completed": task.completed}
            if message:
                update_args["description"] = f"[cyan]{task.name}[/cyan] {message}"
            self.progress.update(self._task_ids[task_id], **update_args)
        
        # 触发回调
        for callback in self._callbacks:
            callback(task_id, task)
    
    def complete_task(self, task_id: str, message: str = ""):
        """完成任务"""
        if task_id in self.tasks:
            self.update_task(
                task_id, 
                completed=self.tasks[task_id].total,
                status="done",
                message=message or "✓"
            )
    
    def fail_task(self, task_id: str, message: str):
        """标记任务失败"""
        if task_id in self.tasks:
            self.update_task(
                task_id,
                status="error",
                message=f"✗ {message}"
            )
    
    def __enter__(self):
        """上下文管理器入口"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeRemainingColumn(elapsed_when_finished=True),
            console=console,
            transient=False
        )
        self.progress.start()
        
        # 为已添加的任务创建进度条
        for task_id, task in self.tasks.items():
            self._task_ids[task_id] = self.progress.add_task(
                f"[cyan]{task.name}[/cyan]",
                total=task.total
            )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.progress:
            self.progress.stop()
        return False


class CollectionProgressTracker(ProgressTracker):
    """采集进度追踪器"""
    
    def __init__(self, collectors: List[str]):
        super().__init__(title="内容采集")
        self.collectors = collectors
        
        # 预创建任务
        for name in collectors:
            self.add_task(f"collect_{name}", name, total=100)
    
    def update_collector(self, name: str, progress: float, message: str = ""):
        """更新采集器进度"""
        self.update_task(f"collect_{name}", completed=int(progress), message=message)
    
    def complete_collector(self, name: str, item_count: int):
        """完成采集"""
        self.complete_task(f"collect_{name}", f"({item_count} 条)")
    
    def print_summary(self):
        """打印采集摘要"""
        table = Table(title="采集结果摘要")
        table.add_column("来源", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("数量", justify="right")
        
        for task_id, task in self.tasks.items():
            if task_id.startswith("collect_"):
                name = task.name
                if task.status == "done":
                    status = "[green]✓[/green]"
                elif task.status == "error":
                    status = "[red]✗[/red]"
                else:
                    status = "[yellow]○[/yellow]"
                
                # 从消息中提取数量
                count = task.message.strip("()") if "(" in task.message else "-"
                table.add_row(name, status, count)
        
        console.print(table)


class ReportGenerationTracker(ProgressTracker):
    """日报生成进度追踪器"""
    
    def __init__(self):
        super().__init__(title="日报生成")
        
        # 定义阶段
        self.phases = [
            ("collect", "📡 内容采集", 30),
            ("process", "🧹 内容处理", 30),
            ("select", "🎯 内容筛选", 20),
            ("format", "📝 格式生成", 20),
        ]
        
        for task_id, name, total in self.phases:
            self.add_task(task_id, name, total)
    
    def enter_phase(self, phase_id: str):
        """进入阶段"""
        for task_id, task in self.tasks.items():
            if task_id == phase_id:
                self.update_task(task_id, status="running")
            elif task.status == "pending":
                pass  # 未开始
            elif task.status == "running":
                self.complete_task(task_id)  # 完成之前的阶段
    
    def update_phase(self, phase_id: str, progress: float, message: str = ""):
        """更新阶段进度"""
        phase_progress = int(progress)
        self.update_task(phase_id, completed=phase_progress, message=message)


def format_time_remaining(seconds: float) -> str:
    """格式化剩余时间"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        return f"{int(seconds/60)}分钟"
    else:
        return f"{seconds/3600:.1f}小时"


class ProgressManager:
    """进度管理器 - 全局进度管理"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_tracker = None
        return cls._instance
    
    def start_collection(self, collectors: List[str]) -> CollectionProgressTracker:
        """开始采集追踪"""
        self.current_tracker = CollectionProgressTracker(collectors)
        return self.current_tracker
    
    def start_generation(self) -> ReportGenerationTracker:
        """开始生成追踪"""
        self.current_tracker = ReportGenerationTracker()
        return self.current_tracker
    
    def get_tracker(self) -> Optional[ProgressTracker]:
        """获取当前追踪器"""
        return self.current_tracker


# 全局进度管理器
progress_manager = ProgressManager()
