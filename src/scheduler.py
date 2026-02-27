"""
任务调度器
管理定时采集和推送任务
"""
import asyncio
from datetime import datetime
from typing import Callable, Dict, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import get_settings

settings = get_settings()


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, str] = {}  # job_name -> job_id
        self._running = False
    
    def start(self):
        """启动调度器"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            print(f"[Scheduler] 调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            print(f"[Scheduler] 调度器已关闭")
    
    def add_daily_job(
        self,
        func: Callable,
        hour: int = 9,
        minute: int = 0,
        job_id: str = "daily_job",
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None
    ) -> str:
        """
        添加每日定时任务
        
        Args:
            func: 执行函数
            hour: 小时 (0-23)
            minute: 分钟 (0-59)
            job_id: 任务标识
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            str: 任务 ID
        """
        trigger = CronTrigger(hour=hour, minute=minute)
        
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True
        )
        
        self.jobs[job_id] = job.id
        print(f"[Scheduler] 添加每日任务: {job_id} ({hour:02d}:{minute:02d})")
        
        return job.id
    
    def add_interval_job(
        self,
        func: Callable,
        minutes: int = 30,
        job_id: str = "interval_job",
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None
    ) -> str:
        """
        添加间隔任务
        
        Args:
            func: 执行函数
            minutes: 间隔分钟数
            job_id: 任务标识
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            str: 任务 ID
        """
        from apscheduler.triggers.interval import IntervalTrigger
        
        trigger = IntervalTrigger(minutes=minutes)
        
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True
        )
        
        self.jobs[job_id] = job.id
        print(f"[Scheduler] 添加间隔任务: {job_id} (每 {minutes} 分钟)")
        
        return job.id
    
    def add_cron_job(
        self,
        func: Callable,
        cron_expr: str,
        job_id: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None
    ) -> str:
        """
        添加 Cron 表达式任务
        
        Args:
            func: 执行函数
            cron_expr: Cron 表达式 (如 "0 9 * * *")
            job_id: 任务标识
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            str: 任务 ID
        """
        # 解析 Cron 表达式
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("Cron 表达式必须是 5 部分: 分 时 日 月 周")
        
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4]
        )
        
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True
        )
        
        self.jobs[job_id] = job.id
        print(f"[Scheduler] 添加 Cron 任务: {job_id} ({cron_expr})")
        
        return job.id
    
    def remove_job(self, job_id: str):
        """移除任务"""
        if job_id in self.jobs:
            self.scheduler.remove_job(self.jobs[job_id])
            del self.jobs[job_id]
            print(f"[Scheduler] 移除任务: {job_id}")
    
    def pause_job(self, job_id: str):
        """暂停任务"""
        if job_id in self.jobs:
            self.scheduler.pause_job(self.jobs[job_id])
            print(f"[Scheduler] 暂停任务: {job_id}")
    
    def resume_job(self, job_id: str):
        """恢复任务"""
        if job_id in self.jobs:
            self.scheduler.resume_job(self.jobs[job_id])
            print(f"[Scheduler] 恢复任务: {job_id}")
    
    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()
    
    def add_listener(self, callback, event=None):
        """添加事件监听器"""
        self.scheduler.add_listener(callback, event)


class DailyTaskManager:
    """日报任务管理器"""
    
    def __init__(self, scheduler: Optional[TaskScheduler] = None):
        self.scheduler = scheduler or TaskScheduler()
        self._generate_func: Optional[Callable] = None
        self._push_func: Optional[Callable] = None
    
    def setup(
        self,
        generate_func: Callable,
        push_func: Optional[Callable] = None,
        push_time: str = "09:00"
    ):
        """
        设置日报任务
        
        Args:
            generate_func: 生成日报的函数
            push_func: 推送日报的函数（可选）
            push_time: 推送时间 (HH:MM)
        """
        self._generate_func = generate_func
        self._push_func = push_func
        
        # 解析时间
        hour, minute = map(int, push_time.split(":"))
        
        # 添加生成任务
        self.scheduler.add_daily_job(
            func=self._on_generate,
            hour=hour,
            minute=minute,
            job_id="daily_generate"
        )
        
        # 添加清理任务（每天凌晨 3 点）
        self.scheduler.add_daily_job(
            func=self._on_cleanup,
            hour=3,
            minute=0,
            job_id="daily_cleanup"
        )
    
    async def _on_generate(self):
        """生成日报回调"""
        print(f"[DailyTask] 开始生成日报: {datetime.now()}")
        
        try:
            if self._generate_func:
                report = await self._generate_func()
                print(f"[DailyTask] 日报生成完成: {report.id if report else 'None'}")
                
                # 如果配置了推送，自动推送
                if self._push_func and report:
                    await self._push_func(report)
                    
        except Exception as e:
            print(f"[DailyTask] 日报生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _on_cleanup(self):
        """清理任务回调"""
        print(f"[DailyTask] 开始清理旧数据: {datetime.now()}")
        
        try:
            # 清理旧内容的逻辑可以在这里实现
            # 或者通过回调传递给外部
            pass
        except Exception as e:
            print(f"[DailyTask] 清理失败: {e}")
    
    def start(self):
        """启动"""
        self.scheduler.start()
    
    def shutdown(self):
        """关闭"""
        self.scheduler.shutdown()


# 全局调度器实例
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
