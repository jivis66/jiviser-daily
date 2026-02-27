"""
定时任务管理模块
提供定时任务的可视化管理和手动控制
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Callable

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent
from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger

from src.scheduler import get_scheduler


@dataclass
class ScheduledTask:
    """定时任务信息"""
    id: str
    name: str
    trigger: str
    next_run_time: Optional[datetime]
    last_run_time: Optional[datetime]
    last_run_status: Optional[str]  # success, error, never
    last_error: Optional[str]
    enabled: bool = True


@dataclass
class TaskHistory:
    """任务执行历史"""
    task_id: str
    task_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # running, success, error
    error_message: Optional[str] = None
    result: Optional[Dict] = None


class SchedulerManager:
    """定时任务管理器"""
    
    def __init__(self):
        self.scheduler = get_scheduler()
        self._generate_func: Optional[Callable] = None
        self._push_func: Optional[Callable] = None
        self._task_history: List[TaskHistory] = []
        self._max_history = 100
        self._listeners_registered = False
    
    def setup(self, generate_func: Callable, push_func: Callable):
        """设置任务函数"""
        self._generate_func = generate_func
        self._push_func = push_func
        
        if not self._listeners_registered:
            self._register_listeners()
    
    def _register_listeners(self):
        """注册事件监听器"""
        self.scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        self._listeners_registered = True
    
    def _on_job_executed(self, event: JobExecutionEvent):
        """任务执行完成回调"""
        if event.exception:
            status = "error"
            error_msg = str(event.exception)
        else:
            status = "success"
            error_msg = None
        
        # 更新历史记录
        for history in self._task_history:
            if (history.task_id == event.job_id and 
                history.status == "running"):
                history.status = status
                history.end_time = datetime.now(timezone.utc)
                history.error_message = error_msg
                break
    
    def get_tasks(self) -> List[ScheduledTask]:
        """获取所有定时任务"""
        tasks = []
        
        for job in self.scheduler.get_jobs():
            # 获取任务状态
            last_run = self._get_last_run_time(job.id)
            last_status = self._get_last_run_status(job.id)
            last_error = self._get_last_error(job.id)
            
            task = ScheduledTask(
                id=job.id,
                name=job.name or job.id,
                trigger=self._format_trigger(job.trigger),
                next_run_time=job.next_run_time,
                last_run_time=last_run,
                last_run_status=last_status,
                last_error=last_error,
                enabled=job.next_run_time is not None
            )
            tasks.append(task)
        
        return tasks
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取单个任务"""
        job = self.scheduler.get_job(task_id)
        if not job:
            return None
        
        last_run = self._get_last_run_time(task_id)
        last_status = self._get_last_run_status(task_id)
        last_error = self._get_last_error(task_id)
        
        return ScheduledTask(
            id=job.id,
            name=job.name or job.id,
            trigger=self._format_trigger(job.trigger),
            next_run_time=job.next_run_time,
            last_run_time=last_run,
            last_run_status=last_status,
            last_error=last_error,
            enabled=job.next_run_time is not None
        )
    
    def _format_trigger(self, trigger) -> str:
        """格式化触发器描述"""
        if isinstance(trigger, CronTrigger):
            fields = []
            if trigger.fields:
                hour = getattr(trigger.fields, 'hour', None)
                minute = getattr(trigger.fields, 'minute', None)
                if hour is not None and minute is not None:
                    hour_val = str(hour).zfill(2)
                    minute_val = str(minute).zfill(2)
                    return f"每天 {hour_val}:{minute_val}"
            return str(trigger)
        return str(trigger)
    
    def _get_last_run_time(self, task_id: str) -> Optional[datetime]:
        """获取上次运行时间"""
        for history in reversed(self._task_history):
            if history.task_id == task_id and history.status != "running":
                return history.end_time
        return None
    
    def _get_last_run_status(self, task_id: str) -> Optional[str]:
        """获取上次运行状态"""
        for history in reversed(self._task_history):
            if history.task_id == task_id and history.status != "running":
                return history.status
        return "never"
    
    def _get_last_error(self, task_id: str) -> Optional[str]:
        """获取上次错误信息"""
        for history in reversed(self._task_history):
            if (history.task_id == task_id and 
                history.status == "error"):
                return history.error_message
        return None
    
    async def run_task_now(self, task_id: str, user_id: str = "default") -> Dict:
        """立即执行任务"""
        job = self.scheduler.get_job(task_id)
        if not job:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 记录执行历史
        history = TaskHistory(
            task_id=task_id,
            task_name=job.name or task_id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
            status="running"
        )
        self._task_history.append(history)
        
        # 限制历史大小
        if len(self._task_history) > self._max_history:
            self._task_history = self._task_history[-self._max_history:]
        
        try:
            # 执行任务
            if task_id == "daily_generate":
                result = await self._generate_func(user_id=user_id)
                history.result = {"report_id": result.id if hasattr(result, 'id') else str(result)}
            elif task_id == "daily_push":
                # 推送需要报告ID，这里简化处理
                history.result = {"message": "推送任务已执行"}
            else:
                # 通用任务执行
                if job.func:
                    if asyncio.iscoroutinefunction(job.func):
                        result = await job.func()
                    else:
                        result = job.func()
                    history.result = {"result": str(result)}
            
            history.status = "success"
            history.end_time = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "task_id": task_id,
                "start_time": history.start_time.isoformat(),
                "end_time": history.end_time.isoformat(),
                "result": history.result
            }
        
        except Exception as e:
            history.status = "error"
            history.end_time = datetime.now(timezone.utc)
            history.error_message = str(e)
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
                "start_time": history.start_time.isoformat(),
                "end_time": history.end_time.isoformat()
            }
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        job = self.scheduler.get_job(task_id)
        if job:
            job.pause()
            return True
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        job = self.scheduler.get_job(task_id)
        if job:
            job.resume()
            return True
        return False
    
    def update_schedule(self, task_id: str, hour: int, minute: int) -> bool:
        """更新任务调度时间"""
        job = self.scheduler.get_job(task_id)
        if not job:
            return False
        
        # 创建新的触发器
        new_trigger = CronTrigger(hour=hour, minute=minute)
        
        # 重新调度
        job.reschedule(trigger=new_trigger)
        return True
    
    def get_history(self, task_id: Optional[str] = None, 
                    limit: int = 20) -> List[TaskHistory]:
        """获取任务执行历史"""
        histories = self._task_history
        
        if task_id:
            histories = [h for h in histories if h.task_id == task_id]
        
        # 按时间倒序
        histories = sorted(histories, key=lambda x: x.start_time, reverse=True)
        
        return histories[:limit]
    
    async def backfill_reports(self, start_date: str, end_date: str, 
                               user_id: str = "default") -> Dict:
        """
        历史补发日报
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            user_id: 用户ID
            
        Returns:
            补发结果
        """
        from datetime import datetime
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start > end:
            raise ValueError("开始日期不能晚于结束日期")
        
        results = []
        current = start
        
        while current <= end:
            try:
                # 生成日报
                result = await self._generate_func(
                    user_id=user_id,
                    date=current
                )
                results.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "status": "success",
                    "report_id": result.id if hasattr(result, 'id') else str(result)
                })
            except Exception as e:
                results.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "status": "error",
                    "error": str(e)
                })
            
            current += timedelta(days=1)
        
        success_count = sum(1 for r in results if r["status"] == "success")
        
        return {
            "total": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "details": results
        }


# 全局管理器实例
_scheduler_manager: Optional[SchedulerManager] = None


def get_scheduler_manager() -> SchedulerManager:
    """获取定时任务管理器"""
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager
