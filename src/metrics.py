"""
性能监控指标模块
收集和记录系统性能指标
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Callable, Dict, List, Optional
import asyncio


@dataclass
class MetricRecord:
    """指标记录"""
    timestamp: datetime
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    

@dataclass
class TimerRecord:
    """计时器记录"""
    operation: str
    duration_ms: float
    timestamp: datetime
    success: bool = True
    error: Optional[str] = None


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.timers: List[TimerRecord] = []
        self.history: List[MetricRecord] = []
        self._lock = asyncio.Lock()
    
    async def increment(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """增加计数器"""
        async with self._lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            
            self._add_history(name, value, labels)
    
    async def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表值"""
        async with self._lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            
            self._add_history(name, value, labels)
    
    async def timer(self, operation: str, duration_ms: float, success: bool = True, 
                    error: Optional[str] = None):
        """记录操作耗时"""
        async with self._lock:
            record = TimerRecord(
                operation=operation,
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc),
                success=success,
                error=error
            )
            self.timers.append(record)
            
            # 限制历史大小
            if len(self.timers) > self.max_history:
                self.timers = self.timers[-self.max_history:]
            
            # 同时记录为指标
            status = "success" if success else "error"
            await self.increment(f"operation_total", 1, {"operation": operation, "status": status})
            await self.gauge(f"operation_duration_ms", duration_ms, {"operation": operation})
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """生成指标键"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _add_history(self, name: str, value: float, labels: Optional[Dict[str, str]]):
        """添加到历史记录"""
        record = MetricRecord(
            timestamp=datetime.now(timezone.utc),
            name=name,
            value=value,
            labels=labels or {}
        )
        self.history.append(record)
        
        # 限制历史大小
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    async def get_stats(self) -> Dict:
        """获取统计信息"""
        async with self._lock:
            # 计算平均耗时
            avg_times = defaultdict(list)
            for timer in self.timers[-100:]:  # 最近 100 条
                avg_times[timer.operation].append(timer.duration_ms)
            
            avg_stats = {}
            for op, times in avg_times.items():
                if times:
                    avg_stats[op] = {
                        "avg_ms": sum(times) / len(times),
                        "min_ms": min(times),
                        "max_ms": max(times),
                        "count": len(times)
                    }
            
            # 成功率
            recent_timers = self.timers[-100:]
            if recent_timers:
                success_rate = sum(1 for t in recent_timers if t.success) / len(recent_timers)
            else:
                success_rate = 1.0
            
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "avg_times": avg_stats,
                "success_rate": success_rate,
                "total_timers": len(self.timers)
            }
    
    async def get_collector_stats(self, collector_name: str) -> Dict:
        """获取采集器统计"""
        async with self._lock:
            # 筛选采集器相关指标
            prefix = f"collector_"
            
            calls = self.counters.get(f"{prefix}{collector_name}_calls", 0)
            errors = self.counters.get(f"{prefix}{collector_name}_errors", 0)
            
            # 查找耗时记录
            times = [t.duration_ms for t in self.timers 
                    if t.operation == f"collect_{collector_name}"]
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
            else:
                avg_time = max_time = 0
            
            return {
                "name": collector_name,
                "calls": calls,
                "errors": errors,
                "success_rate": (calls - errors) / calls if calls > 0 else 1.0,
                "avg_time_ms": avg_time,
                "max_time_ms": max_time
            }


# 全局指标收集器
metrics_collector = MetricsCollector()


def timed(operation: str):
    """
    装饰器：记录函数执行时间
    
    用法:
        @timed("my_operation")
        async def my_function():
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                await metrics_collector.timer(operation, duration_ms, success=True)
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                await metrics_collector.timer(operation, duration_ms, success=False, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                asyncio.create_task(metrics_collector.timer(operation, duration_ms, success=True))
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                asyncio.create_task(metrics_collector.timer(operation, duration_ms, success=False, error=str(e)))
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class CollectorMetrics:
    """采集器指标装饰器"""
    
    def __init__(self, collector_name: str):
        self.collector_name = collector_name
    
    async def record_call(self, success: bool = True, error: Optional[str] = None,
                         item_count: int = 0, duration_ms: float = 0):
        """记录采集调用"""
        prefix = f"collector_{self.collector_name}"
        
        await metrics_collector.increment(f"{prefix}_calls")
        
        if not success:
            await metrics_collector.increment(f"{prefix}_errors")
        
        await metrics_collector.gauge(f"{prefix}_items", item_count)
        await metrics_collector.gauge(f"{prefix}_duration_ms", duration_ms)


# 便捷函数
async def record_collection(collector_name: str, duration_ms: float, 
                            item_count: int, success: bool = True):
    """记录采集指标"""
    await metrics_collector.timer(
        f"collect_{collector_name}", 
        duration_ms, 
        success=success
    )
    
    prefix = f"collector_{collector_name}"
    await metrics_collector.increment(f"{prefix}_total")
    await metrics_collector.gauge(f"{prefix}_last_items", item_count)


async def get_performance_report() -> Dict:
    """获取性能报告"""
    stats = await metrics_collector.get_stats()
    
    # 采集器统计
    from src.config import get_column_config
    col_config = get_column_config()
    columns = col_config.get_columns(enabled_only=False)
    
    collector_stats = []
    source_names = set()
    
    for col in columns:
        for source in col.get("sources", []):
            name = source.get("name")
            if name and name not in source_names:
                source_names.add(name)
                stat = await metrics_collector.get_collector_stats(name)
                collector_stats.append(stat)
    
    return {
        "summary": {
            "total_operations": stats["total_timers"],
            "overall_success_rate": f"{stats['success_rate']*100:.1f}%",
            "active_collectors": len(collector_stats)
        },
        "operation_times": stats["avg_times"],
        "collectors": collector_stats
    }


# CLI 输出函数
async def print_performance_report():
    """打印性能报告（CLI 用）"""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    report = await get_performance_report()
    
    console.print("\n[bold]📊 性能监控报告[/bold]")
    console.print("━" * 60)
    
    # 概览
    summary = report["summary"]
    console.print(Panel(
        f"总操作数: {summary['total_operations']}\n"
        f"整体成功率: {summary['overall_success_rate']}\n"
        f"活跃采集器: {summary['active_collectors']}",
        title="概览"
    ))
    
    # 操作耗时
    if report["operation_times"]:
        console.print("\n[bold]⏱️ 操作耗时 (最近100次平均)[/bold]")
        table = Table()
        table.add_column("操作", style="cyan")
        table.add_column("平均(ms)", justify="right")
        table.add_column("最小(ms)", justify="right")
        table.add_column("最大(ms)", justify="right")
        table.add_column("次数", justify="right")
        
        for op, stats in report["operation_times"].items():
            table.add_row(
                op,
                f"{stats['avg_ms']:.1f}",
                f"{stats['min_ms']:.1f}",
                f"{stats['max_ms']:.1f}",
                str(stats['count'])
            )
        
        console.print(table)
    
    # 采集器统计
    if report["collectors"]:
        console.print("\n[bold]📡 采集器统计[/bold]")
        table = Table()
        table.add_column("采集器", style="cyan")
        table.add_column("调用次数", justify="right")
        table.add_column("成功率", justify="right")
        table.add_column("平均耗时(ms)", justify="right")
        
        for stat in report["collectors"]:
            if stat["calls"] > 0:
                table.add_row(
                    stat["name"],
                    str(stat["calls"]),
                    f"{stat['success_rate']*100:.1f}%",
                    f"{stat['avg_time_ms']:.1f}"
                )
        
        console.print(table)
