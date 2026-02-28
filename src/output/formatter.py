"""
输出格式化模块
支持多种格式：Markdown / HTML / JSON / Chat
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import BaseLoader, Environment

from src.models import ContentItem, DailyReport


class MarkdownFormatter:
    """Markdown 格式（适合 Telegram / 邮件纯文本）"""
    
    def format_report(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> str:
        """
        格式化日报为 Markdown
        """
        # 构建分栏数据
        col_data_list = []
        for col_config in columns_config:
            col_id = col_config.get("id")
            if col_id in items_by_column:
                col_data_list.append({
                    "name": col_config.get("name", col_id),
                    "items": items_by_column[col_id]
                })
        
        return self._render_simple(
            title=report.title,
            date=report.date.strftime("%Y年%m月%d日"),
            total_items=report.total_items,
            summary=report.summary,
            col_data_list=col_data_list
        )
    
    def _render_simple(
        self,
        title: str,
        date: str,
        total_items: int,
        summary: Optional[str],
        col_data_list: List[Dict]
    ) -> str:
        """简化版渲染，避免复杂的 Jinja2 模板问题"""
        
        lines = []
        
        # 标题
        lines.append(f"# {title}")
        lines.append(f"")
        lines.append(f"**日期**: {date}")
        lines.append(f"**总条目**: {total_items}")
        lines.append(f"")
        
        # 摘要
        if summary:
            lines.append(f"## 摘要")
            lines.append(f"")
            lines.append(summary)
            lines.append(f"")
        
        # 各分栏
        for col in col_data_list:
            if not col.get("items"):
                continue
                
            col_name = col.get("name", "未知")
            items = col.get("items", [])
            
            lines.append(f"## 📂 {col_name}")
            lines.append(f"")
            
            for item in items:
                lines.extend(self._format_item(item))
                lines.append(f"")
        
        return "\n".join(lines)
    
    def _format_item(self, item: ContentItem) -> List[str]:
        """格式化单个条目"""
        lines = []
        
        # 标题
        title = item.title or "无标题"
        lines.append(f"### {title}")
        
        # 来源和时间
        meta = []
        if item.source:
            meta.append(f"来源: {item.source}")
        if item.published_at:
            meta.append(f"发布时间: {item.published_at.strftime('%Y-%m-%d %H:%M')}")
        if meta:
            lines.append(f"*{', '.join(meta)}*")
        lines.append(f"")
        
        # 摘要
        if item.summary:
            lines.append(item.summary)
            lines.append(f"")
        
        # 关键点
        key_points = self._ensure_list(item.key_points)
        if key_points:
            lines.append(f"**要点**:")
            for point in key_points[:5]:
                lines.append(f"- {point}")
            lines.append(f"")
        
        # 标签
        topics = self._ensure_list(item.topics)
        if topics:
            lines.append(f"**标签**: {', '.join(topics[:5])}")
        
        keywords = self._ensure_list(item.keywords)
        if keywords:
            lines.append(f"**关键词**: {', '.join(keywords[:8])}")
        
        # 链接
        if item.url:
            lines.append(f"")
            lines.append(f"[阅读原文]({item.url})")
        
        return lines
    
    def _ensure_list(self, value: Any) -> List[str]:
        """确保值为列表"""
        if value is None:
            return []
        if callable(value):
            return []
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, (list, tuple)):
            return list(value)
        return []
    
    def format_item(self, item: ContentItem) -> str:
        """格式化单个条目"""
        lines = self._format_item(item)
        return "\n".join(lines)
    
    def format_items(self, items: List[ContentItem]) -> str:
        """格式化多个条目"""
        lines = []
        for item in items:
            lines.extend(self._format_item(item))
            lines.append("---")
            lines.append("")
        return "\n".join(lines)


class HTMLFormatter:
    """HTML 格式（适合邮件）"""
    
    def format_report(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> str:
        """
        格式化日报为 HTML
        """
        # 构建分栏数据
        col_data_list = []
        for col_config in columns_config:
            col_id = col_config.get("id")
            if col_id in items_by_column:
                col_data_list.append({
                    "name": col_config.get("name", col_id),
                    "items": items_by_column[col_id]
                })
        
        html_parts = []
        
        # 头部样式
        html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 28px; }
        .header .meta { margin-top: 10px; opacity: 0.9; }
        .column { background: white; border-radius: 10px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .column-title { color: #667eea; font-size: 20px; margin: 0 0 20px 0; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        .item { margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
        .item:last-child { border-bottom: none; }
        .item-title { font-size: 18px; font-weight: 600; color: #333; margin: 0 0 10px 0; }
        .item-title a { color: #667eea; text-decoration: none; }
        .item-meta { color: #888; font-size: 13px; margin-bottom: 10px; }
        .item-summary { color: #555; line-height: 1.6; margin-bottom: 10px; }
        .item-points { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .item-points li { margin: 5px 0; color: #555; }
        .item-tags { margin-top: 10px; }
        .tag { display: inline-block; background: #e3f2fd; color: #1976d2; padding: 4px 10px; border-radius: 15px; font-size: 12px; margin-right: 5px; margin-bottom: 5px; }
        .footer { text-align: center; color: #888; margin-top: 40px; font-size: 13px; }
    </style>
</head>
<body>
""")
        
        # 标题区域
        html_parts.append(f"""
<div class="header">
    <h1>{self._escape_html(report.title)}</h1>
    <div class="meta">
        📅 {report.date.strftime('%Y年%m月%d日')} | 
        📊 共 {report.total_items} 条精选内容
    </div>
</div>
""")
        
        # 摘要
        if report.summary:
            html_parts.append(f"""
<div class="column">
    <h2 style="color: #667eea; margin-top: 0;">摘要</h2>
    <p>{self._escape_html(report.summary)}</p>
</div>
""")
        
        # 各分栏
        for col in col_data_list:
            if not col.get("items"):
                continue
            
            html_parts.append(f'<div class="column">')
            html_parts.append(f'<h2 class="column-title">📂 {self._escape_html(col["name"])}</h2>')
            
            for item in col.get("items", []):
                html_parts.append(self._format_item_html(item))
            
            html_parts.append('</div>')
        
        # 底部
        html_parts.append("""
<div class="footer">
    <p>由 DailyAgent 自动生成</p>
</div>
</body>
</html>
""")
        
        return "\n".join(html_parts)
    
    def _format_item_html(self, item: ContentItem) -> str:
        """格式化单个条目为 HTML"""
        parts = ['<div class="item">']
        
        # 标题
        title = self._escape_html(item.title or "无标题")
        if item.url:
            parts.append(f'<h3 class="item-title"><a href="{self._escape_html(item.url)}">{title}</a></h3>')
        else:
            parts.append(f'<h3 class="item-title">{title}</h3>')
        
        # 元信息
        meta = []
        if item.source:
            meta.append(f"来源: {self._escape_html(item.source)}")
        if item.published_at:
            meta.append(f"发布时间: {item.published_at.strftime('%Y-%m-%d %H:%M')}")
        if meta:
            parts.append(f'<div class="item-meta">{" | ".join(meta)}</div>')
        
        # 摘要
        if item.summary:
            parts.append(f'<div class="item-summary">{self._escape_html(item.summary)}</div>')
        
        # 关键点
        key_points = self._ensure_list(item.key_points)
        if key_points:
            parts.append('<ul class="item-points">')
            for point in key_points[:5]:
                parts.append(f'<li>{self._escape_html(str(point))}</li>')
            parts.append('</ul>')
        
        # 标签
        tags = []
        topics = self._ensure_list(item.topics)
        keywords = self._ensure_list(item.keywords)
        tags.extend(topics[:5])
        tags.extend(keywords[:5])
        
        if tags:
            parts.append('<div class="item-tags">')
            for tag in tags[:10]:
                parts.append(f'<span class="tag">{self._escape_html(str(tag))}</span>')
            parts.append('</div>')
        
        parts.append('</div>')
        return "\n".join(parts)
    
    def _escape_html(self, text: str) -> str:
        """转义 HTML 特殊字符"""
        if not text:
            return ""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
    
    def _ensure_list(self, value: Any) -> List[str]:
        """确保值为列表"""
        if value is None:
            return []
        if callable(value):
            return []
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, (list, tuple)):
            return list(value)
        return []


class ChatFormatter:
    """聊天格式（适合 Telegram/Slack 等聊天应用）"""
    
    MAX_LENGTH = 4000
    MAX_ITEMS = 50
    
    def format_report(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> List[str]:
        """
        格式化日报为聊天消息（返回多条消息列表）
        """
        messages = []
        current_msg = []
        current_length = 0
        
        # 标题
        header = f"📰 *{report.title}*\n"
        header += f"📅 {report.date.strftime('%Y年%m月%d日')}\n"
        header += f"📊 共 {report.total_items} 条精选内容\n\n"
        
        current_msg.append(header)
        current_length = len(header)
        
        # 摘要
        if report.summary:
            summary = f"📌 *摘要*\n{report.summary}\n\n"
            current_msg.append(summary)
            current_length += len(summary)
        
        # 各分栏
        for col_config in columns_config:
            col_id = col_config.get("id")
            col_name = col_config.get("name", col_id)
            items = items_by_column.get(col_id, [])
            
            if not items:
                continue
            
            section_header = f"*📂 {col_name}*\n\n"
            
            # 检查是否需要开始新消息
            if current_length + len(section_header) > self.MAX_LENGTH:
                messages.append("".join(current_msg))
                current_msg = [section_header]
                current_length = len(section_header)
            else:
                current_msg.append(section_header)
                current_length += len(section_header)
            
            # 条目
            for item in items[:10]:  # 每栏最多10条
                item_text = self._format_item_chat(item)
                
                if current_length + len(item_text) > self.MAX_LENGTH:
                    messages.append("".join(current_msg))
                    current_msg = [item_text]
                    current_length = len(item_text)
                else:
                    current_msg.append(item_text)
                    current_length += len(item_text)
        
        # 添加剩余内容
        if current_msg:
            messages.append("".join(current_msg))
        
        return messages
    
    def _format_item_chat(self, item: ContentItem) -> str:
        """格式化单个条目为聊天格式"""
        lines = []
        
        # 标题
        title = item.title or "无标题"
        if item.url:
            lines.append(f"• *{title}*")
            lines.append(f"  [阅读原文]({item.url})")
        else:
            lines.append(f"• *{title}*")
        
        # 摘要（缩短）
        if item.summary:
            summary = item.summary[:80] + "..." if len(item.summary) > 80 else item.summary
            lines.append(f"  _{summary}_")
        
        # 标签
        topics = self._ensure_list(item.topics)
        if topics:
            lines.append(f"  🏷 {' '.join(f'`{t}`' for t in topics[:3])}")
        
        lines.append("")
        return "\n".join(lines)
    
    def _ensure_list(self, value: Any) -> List[str]:
        """确保值为列表"""
        if value is None:
            return []
        if callable(value):
            return []
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, (list, tuple)):
            return list(value)
        return []
    
    def format_item(self, item: ContentItem) -> str:
        """格式化单个条目"""
        return self._format_item_chat(item)


class JSONFormatter:
    """JSON 格式"""
    
    def format_report(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> str:
        """
        格式化日报为 JSON
        """
        import json
        
        data = {
            "id": report.id,
            "title": report.title,
            "date": report.date.isoformat(),
            "total_items": report.total_items,
            "summary": report.summary,
            "columns": []
        }
        
        for col_config in columns_config:
            col_id = col_config.get("id")
            col_data = {
                "id": col_id,
                "name": col_config.get("name", col_id),
                "items": []
            }
            
            for item in items_by_column.get(col_id, []):
                col_data["items"].append({
                    "id": item.id,
                    "title": item.title,
                    "url": item.url,
                    "summary": item.summary,
                    "source": item.source,
                    "published_at": item.published_at.isoformat() if item.published_at else None,
                    "topics": self._ensure_list(item.topics),
                    "keywords": self._ensure_list(item.keywords),
                })
            
            data["columns"].append(col_data)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _ensure_list(self, value: Any) -> List:
        """确保值为列表"""
        if value is None:
            return []
        if callable(value):
            return []
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, (list, tuple)):
            return list(value)
        return []
