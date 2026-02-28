"""
规则测试器模块
测试过滤规则效果，预览哪些内容会被选中
"""
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


@dataclass
class RuleTestResult:
    """规则测试结果"""
    total_items: int
    passed_items: int
    failed_items: int
    details: List[Dict]
    

class RuleTester:
    """规则测试器"""
    
    def __init__(self):
        self.results = []
    
    def test_keyword_filter(self, items: List[Dict], keywords: List[str], 
                            exclude: List[str] = None) -> RuleTestResult:
        """
        测试关键词过滤规则
        
        Args:
            items: 内容列表
            keywords: 必须包含的关键词
            exclude: 排除的关键词
            
        Returns:
            RuleTestResult: 测试结果
        """
        exclude = exclude or []
        passed = []
        failed = []
        
        for item in items:
            title = item.get("title", "")
            content = item.get("content", "")
            text = f"{title} {content}".lower()
            
            # 检查必须关键词
            has_keyword = not keywords or any(kw.lower() in text for kw in keywords)
            
            # 检查排除关键词
            has_exclude = any(ex.lower() in text for ex in exclude)
            
            if has_keyword and not has_exclude:
                passed.append(item)
            else:
                failed.append({
                    **item,
                    "reason": "缺少关键词" if not has_keyword else "包含排除词"
                })
        
        return RuleTestResult(
            total_items=len(items),
            passed_items=len(passed),
            failed_items=len(failed),
            details=passed
        )
    
    def test_quality_filter(self, items: List[Dict], 
                           min_score: int = 60) -> RuleTestResult:
        """
        测试质量评分过滤
        
        Args:
            items: 内容列表
            min_score: 最低质量分数
            
        Returns:
            RuleTestResult: 测试结果
        """
        passed = []
        failed = []
        
        for item in items:
            score = item.get("quality_score", 0) or item.get("popularity_score", 0) or 50
            
            if score >= min_score:
                passed.append(item)
            else:
                failed.append({
                    **item,
                    "reason": f"质量分 {score} < {min_score}"
                })
        
        return RuleTestResult(
            total_items=len(items),
            passed_items=len(passed),
            failed_items=len(failed),
            details=passed
        )
    
    def test_source_diversity(self, items: List[Dict], 
                             max_ratio: float = 0.4) -> RuleTestResult:
        """
        测试来源多样性规则
        
        Args:
            items: 内容列表
            max_ratio: 单一来源最大比例
            
        Returns:
            RuleTestResult: 测试结果
        """
        # 统计来源
        source_count = {}
        for item in items:
            source = item.get("source", "unknown")
            source_count[source] = source_count.get(source, 0) + 1
        
        total = len(items)
        passed = []
        
        for item in items:
            source = item.get("source", "unknown")
            ratio = source_count[source] / total if total > 0 else 0
            
            if ratio <= max_ratio:
                passed.append(item)
        
        return RuleTestResult(
            total_items=len(items),
            passed_items=len(passed),
            failed_items=len(items) - len(passed),
            details=passed
        )
    
    def print_report(self, result: RuleTestResult, rule_name: str = "规则测试"):
        """打印测试报告"""
        console.print(f"\n[bold]{rule_name}[/bold]")
        console.print("━" * 50)
        
        # 统计
        pass_rate = (result.passed_items / result.total_items * 100) if result.total_items > 0 else 0
        
        console.print(f"总条目: {result.total_items}")
        console.print(f"通过: [green]{result.passed_items}[/green] ({pass_rate:.1f}%)")
        console.print(f"过滤: [red]{result.failed_items}[/red]")
        console.print()
        
        # 通过的条目
        if result.details:
            console.print("[bold]通过的条目:[/bold]")
            table = Table()
            table.add_column("标题", style="cyan", max_width=50)
            table.add_column("来源", style="green")
            table.add_column("质量分", justify="right")
            
            for item in result.details[:10]:  # 最多显示10条
                table.add_row(
                    item.get("title", "")[:50],
                    item.get("source", ""),
                    str(item.get("quality_score", "-"))
                )
            
            console.print(table)
            
            if len(result.details) > 10:
                console.print(f"\n[dim]... 还有 {len(result.details) - 10} 条[/dim]")


async def test_column_rules(column_id: str):
    """
    测试指定分栏的规则
    
    Args:
        column_id: 分栏 ID
    """
    from src.config import get_column_config
    from src.database import get_session, ContentRepository
    from datetime import datetime, timedelta, timezone
    
    console.print(f"[bold]🧪 测试分栏规则: {column_id}[/bold]\n")
    
    # 获取分栏配置
    col_config = get_column_config()
    column = col_config.get_column(column_id)
    
    if not column:
        console.print(f"[red]分栏不存在: {column_id}[/red]")
        return
    
    # 显示分栏配置
    console.print(Panel(
        f"[bold]{column.get('name')}[/bold]\n"
        f"最大条目: {column.get('max_items', 5)}\n"
        f"排序方式: {column.get('organization', {}).get('sort_by', 'relevance')}\n"
        f"去重策略: {column.get('organization', {}).get('dedup_strategy', 'semantic')}",
        title="分栏配置"
    ))
    
    # 获取最近的内容
    async with get_session() as session:
        content_repo = ContentRepository(session)
        
        # 获取该分栏的内容
        items = await content_repo.get_by_column(
            column_id=column_id,
            limit=50
        )
        
        if not items:
            console.print("[yellow]该分栏暂无内容[/yellow]")
            return
        
        # 转换为字典
        item_dicts = [
            {
                "id": item.id,
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "quality_score": item.quality_score or 50,
                "popularity_score": item.popularity_score or 50,
                "content": item.content or ""
            }
            for item in items
        ]
        
        console.print(f"[dim]测试样本: {len(item_dicts)} 条内容[/dim]\n")
        
        # 测试质量过滤
        min_quality = column.get("organization", {}).get("min_quality", 60)
        tester = RuleTester()
        
        quality_result = tester.test_quality_filter(item_dicts, min_quality)
        tester.print_report(quality_result, f"质量过滤 (>= {min_quality})")
        
        # 测试来源多样性
        diversity_result = tester.test_source_diversity(item_dicts)
        tester.print_report(diversity_result, "来源多样性")
        
        # 模拟最终选择
        max_items = column.get("max_items", 5)
        console.print(f"\n[bold]最终选择 (最多 {max_items} 条):[/bold]")
        
        # 综合过滤后的结果
        passed_items = quality_result.details
        
        if passed_items:
            table = Table()
            table.add_column("#", justify="right")
            table.add_column("标题", style="cyan", max_width=50)
            table.add_column("来源", style="green")
            table.add_column("质量分", justify="right")
            
            for i, item in enumerate(passed_items[:max_items], 1):
                table.add_row(
                    str(i),
                    item.get("title", "")[:50],
                    item.get("source", ""),
                    str(item.get("quality_score", "-"))
                )
            
            console.print(table)
            
            if len(passed_items) > max_items:
                console.print(f"\n[yellow]注意: {len(passed_items)} 条内容通过过滤，"
                            f"但只选择前 {max_items} 条[/yellow]")
        else:
            console.print("[red]没有内容通过所有过滤规则[/red]")


async def test_source_filter(source_name: str):
    """
    测试指定数据源的过滤规则
    
    Args:
        source_name: 数据源名称
    """
    from src.config import get_column_config
    
    console.print(f"[bold]🧪 测试数据源过滤: {source_name}[/bold]\n")
    
    # 查找数据源配置
    col_config = get_column_config()
    columns = col_config.get_columns(enabled_only=False)
    
    source_config = None
    for col in columns:
        for source in col.get("sources", []):
            if source.get("name") == source_name:
                source_config = source
                break
        if source_config:
            break
    
    if not source_config:
        console.print(f"[red]数据源不存在: {source_name}[/red]")
        return
    
    # 显示配置
    filter_config = source_config.get("filter", {})
    
    console.print(Panel(
        f"类型: {source_config.get('type')}\n"
        f"关键词: {', '.join(filter_config.get('keywords', [])) or '无'}\n"
        f"排除词: {', '.join(filter_config.get('exclude', [])) or '无'}\n"
        f"最小分数: {filter_config.get('min_score', '无')}",
        title="过滤配置"
    ))
    
    # 采集测试数据
    console.print("\n[dim]正在采集测试数据...[/dim]")
    
    from src.collector import CollectorManager
    
    collector_manager = CollectorManager()
    
    # 创建采集器
    source_type = source_config.get("type")
    try:
        if source_type == "rss":
            from src.collector.rss_collector import RSSCollector
            collector = RSSCollector(source_name, source_config)
        elif source_type == "api":
            from src.collector.api_collector import HackerNewsCollector
            collector = HackerNewsCollector(source_name, source_config)
        else:
            console.print(f"[yellow]暂不支持测试 {source_type} 类型[/yellow]")
            return
        
        result = await collector.collect()
        
        console.print(f"采集结果: {len(result.items)} 条内容\n")
        
        if not result.items:
            console.print("[yellow]未采集到内容[/yellow]")
            return
        
        # 转换为字典
        item_dicts = [
            {
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "content": item.content or ""
            }
            for item in result.items
        ]
        
        # 测试过滤
        keywords = filter_config.get("keywords", [])
        exclude = filter_config.get("exclude", [])
        
        if keywords or exclude:
            tester = RuleTester()
            result = tester.test_keyword_filter(item_dicts, keywords, exclude)
            tester.print_report(result, "关键词过滤")
        else:
            console.print("[dim]该数据源未配置关键词过滤[/dim]")
            
            # 显示所有内容
            table = Table()
            table.add_column("标题", style="cyan", max_width=60)
            table.add_column("来源", style="green")
            
            for item in item_dicts[:10]:
                table.add_row(
                    item.get("title", "")[:60],
                    item.get("source", "")
                )
            
            console.print(table)
    
    except Exception as e:
        console.print(f"[red]测试失败: {e}[/red]")
    
    finally:
        if 'collector' in locals():
            await collector.close()


# CLI 命令函数
def cli_test_rules(column_id: Optional[str] = None, 
                   source_name: Optional[str] = None):
    """CLI 入口"""
    if column_id:
        asyncio.run(test_column_rules(column_id))
    elif source_name:
        asyncio.run(test_source_filter(source_name))
    else:
        console.print("[yellow]请指定 --column 或 --source[/yellow]")
