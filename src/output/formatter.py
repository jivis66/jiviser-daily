"""
内容格式化器
支持 Markdown、HTML、Chat 等多种格式
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Template

from src.models import ChannelType, ContentItem, DailyReport


class BaseFormatter(ABC):
    """格式化器基类"""
    
    @abstractmethod
    def format_report(
        self, 
        report: DailyReport, 
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> str:
        """格式化日报"""
        pass
    
    @abstractmethod
    def format_item(self, item: ContentItem, index: int = 1) -> str:
        """格式化单条内容"""
        pass


class MarkdownFormatter(BaseFormatter):
    """Markdown 格式化器"""
    
    REPORT_TEMPLATE = """# {{ title }}

> {{ date }} | 共 {{ total_items }} 条精选内容

{% if summary %}
## 📋 今日概述

{{ summary }}

{% endif %}
{% for column in columns %}
## {{ column.name }}

{% for item in column.items %}
### {{ loop.index }}. {{ item.title }}

**来源**: {{ item.source }}{% if item.author %} | **作者**: {{ item.author }}{% endif %}

{% if item.summary %}
{{ item.summary }}
{% endif %}
{% if item.key_points %}
{% for point in item.key_points %}
- {{ point }}
{% endfor %}
{% endif %}

{% if item.read_time %}⏱️ {{ item.read_time }} 分钟 {% endif %}[阅读原文]({{ item.url }})

---

{% endfor %}
{% endfor %}

---

*由 Daily Agent 自动生成*
"""
    
    def format_report(
        self, 
        report: DailyReport, 
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> str:
        """格式化日报为 Markdown"""
        # 构建模板数据
        columns = []
        for col_config in columns_config:
            col_id = col_config.get("id")
            if col_id in items_by_column and items_by_column[col_id]:
                columns.append({
                    "name": col_config.get("name", col_id),
                    "items": items_by_column[col_id]
                })
        
        template = Template(self.REPORT_TEMPLATE)
        return template.render(
            title=report.title,
            date=report.date.strftime("%Y年%m月%d日"),
            total_items=report.total_items,
            summary=report.summary,
            columns=columns
        )
    
    def format_item(self, item: ContentItem, index: int = 1) -> str:
        """格式化单条内容"""
        lines = [
            f"### {index}. {item.title}",
            "",
            f"**来源**: {item.source}",
            "",
        ]
        
        if item.summary:
            lines.append(item.summary)
            lines.append("")
        
        lines.append(f"[阅读原文]({item.url})")
        
        return "\n".join(lines)
    
    def format_simple_list(
        self, 
        items: List[ContentItem], 
        title: str = "内容列表"
    ) -> str:
        """格式化为简单列表"""
        lines = [f"# {title}", ""]
        
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. **{item.title}** - {item.source}")
            if item.summary:
                summary = item.summary.replace("\n", " ")
                if len(summary) > 100:
                    summary = summary[:100] + "..."
                lines.append(f"   {summary}")
            lines.append("")
        
        return "\n".join(lines)


class HTMLFormatter(BaseFormatter):
    """HTML 格式化器"""
    
    REPORT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        h1 { color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { color: #2c3e50; margin-top: 30px; }
        h3 { color: #34495e; margin-top: 20px; }
        .meta { color: #666; font-size: 0.9em; }
        .summary { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .item { border-bottom: 1px solid #eee; padding: 15px 0; }
        .source { color: #666; font-size: 0.85em; }
        .summary-text { margin: 10px 0; }
        .key-points { margin: 10px 0; padding-left: 20px; }
        .key-points li { margin: 5px 0; }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 0.85em; text-align: center; }
        .tag { display: inline-block; background: #e9ecef; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; margin-right: 5px; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p class="meta">{{ date }} | 共 {{ total_items }} 条精选内容</p>
    
    {% if summary %}
    <div class="summary">
        <strong>📋 今日概述</strong>
        <p>{{ summary }}</p>
    </div>
    {% endif %}
    
    {% for column in columns %}
    <h2>{{ column.name }}</h2>
    
    {% for item in column.items %}
    <div class="item">
        <h3>{{ loop.index }}. {{ item.title }}</h3>
        <p class="source">来源: {{ item.source }}{% if item.author %} | 作者: {{ item.author }}{% endif %}</p>
        
        {% if item.summary %}
        <div class="summary-text">{{ item.summary|replace('\n', '<br>') }}</div>
        {% endif %}
        
        {% if item.key_points %}
        <ul class="key-points">
            {% for point in item.key_points %}
            <li>{{ point }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        <p>
            {% if item.topics %}
            {% for topic in item.topics %}
            <span class="tag">{{ topic }}</span>
            {% endfor %}
            {% endif %}
            {% if item.read_time %}⏱️ {{ item.read_time }} 分钟 {% endif %}
            <a href="{{ item.url }}" target="_blank">阅读原文 →</a>
        </p>
    </div>
    {% endfor %}
    {% endfor %}
    
    <div class="footer">
        由 Daily Agent 自动生成
    </div>
</body>
</html>
"""
    
    def format_report(
        self, 
        report: DailyReport, 
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> str:
        """格式化日报为 HTML"""
        columns = []
        for col_config in columns_config:
            col_id = col_config.get("id")
            if col_id in items_by_column and items_by_column[col_id]:
                columns.append({
                    "name": col_config.get("name", col_id),
                    "items": items_by_column[col_id]
                })
        
        template = Template(self.REPORT_TEMPLATE)
        return template.render(
            title=report.title,
            date=report.date.strftime("%Y年%m月%d日"),
            total_items=report.total_items,
            summary=report.summary,
            columns=columns
        )
    
    def format_item(self, item: ContentItem, index: int = 1) -> str:
        """格式化单条内容为 HTML"""
        return f"""
        <div class="item">
            <h3>{index}. {item.title}</h3>
            <p class="source">来源: {item.source}</p>
            <p>{item.summary or ''}</p>
            <a href="{item.url}">阅读原文</a>
        </div>
        """


class ChatFormatter:
    """Chat 渠道格式化器（适配 iMessage/Telegram/WhatsApp）"""
    
    # 单条长度限制
    LIMITS = {
        ChannelType.IMESSAGE: 2000,
        ChannelType.TELEGRAM: 4096,
        ChannelType.WHATSAPP: 65536,
    }
    
    def format_for_channel(
        self, 
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]],
        channel: ChannelType
    ) -> List[str]:
        """
        格式化为指定渠道的消息列表
        
        Returns:
            List[str]: 消息列表（每条消息是一个字符串）
        """
        formatters = {
            ChannelType.IMESSAGE: self._format_imessage,
            ChannelType.TELEGRAM: self._format_telegram,
            ChannelType.WHATSAPP: self._format_whatsapp,
        }
        
        formatter = formatters.get(channel, self._format_imessage)
        return formatter(report, columns_config, items_by_column)
    
    def _format_imessage(
        self, 
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> List[str]:
        """格式化为 iMessage 风格"""
        messages = []
        
        # 第一条：标题和概述
        header = f"""📰 {report.title} │ {report.date.strftime("%m月%d日")}
━━━━━━━━━━━━━━

共 {report.total_items} 条精选内容
"""
        if report.summary:
            header += f"\n{report.summary[:100]}..."
        
        messages.append(header)
        
        # 每个分栏
        for col_config in columns_config:
            col_id = col_config.get("id")
            items = items_by_column.get(col_id, [])
            if not items:
                continue
            
            col_msg = f"\n📂 {col_config.get('name', col_id)}\n"
            
            for i, item in enumerate(items[:3], 1):  # iMessage 每栏最多3条
                col_msg += f"\n{i}. {item.title}\n"
                if item.summary:
                    summary = item.summary.split("\n")[0][:80]
                    col_msg += f"   {summary}...\n"
                col_msg += f"   👉 {item.url[:60]}...\n"
            
            messages.append(col_msg)
        
        # 结尾
        messages.append("\n━━━━━━━━━━━━━━\n回复「详细」获取完整日报")
        
        return self._split_messages(messages, ChannelType.IMESSAGE)
    
    def _format_telegram(
        self, 
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> List[str]:
        """格式化为 Telegram 风格（支持 Markdown v2）"""
        messages = []
        
        # 标题
        header = f"""📰 *{report.title}* │ {report.date.strftime("%m月%d日")}

共 *{report.total_items}* 条精选内容
"""
        if report.summary:
            header += f"\n_{report.summary[:150]}..._"
        
        messages.append(header)
        
        # 分栏内容
        for col_config in columns_config:
            col_id = col_config.get("id")
            items = items_by_column.get(col_id, [])
            if not items:
                continue
            
            col_msg = f"\n📂 *{col_config.get('name', col_id)}*\n"
            
            for item in items[:5]:  # Telegram 每栏最多5条
                col_msg += f"\n*{item.title}*\n"
                if item.summary:
                    # Telegram Markdown v2 需要转义
                    summary = item.summary[:150].replace("_", "\\_").replace("*", "\\*")
                    col_msg += f"{summary}...\n"
                col_msg += f"[阅读全文]({item.url})\n"
            
            messages.append(col_msg)
        
        return self._split_messages(messages, ChannelType.TELEGRAM)
    
    def _format_whatsapp(
        self, 
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> List[str]:
        """格式化为 WhatsApp 风格"""
        messages = []
        
        # 标题
        header = f"""📰 *{report.title}* _{report.date.strftime("%m月%d日")}_

共 {report.total_items} 条精选内容
"""
        messages.append(header)
        
        # 分栏
        counter = 0
        for col_config in columns_config:
            col_id = col_config.get("id")
            items = items_by_column.get(col_id, [])
            if not items:
                continue
            
            col_msg = f"\n📂 *{col_config.get('name', col_id)}*\n"
            
            for item in items[:4]:  # WhatsApp 每栏最多4条
                counter += 1
                col_msg += f"\n*{counter}.* {item.title}\n"
                if item.summary:
                    col_msg += f"_{item.summary[:100]}..._\n"
            
            messages.append(col_msg)
        
        # 导航
        nav = "\n回复数字查看详情:\n"
        for i in range(1, min(counter + 1, 10)):
            nav += f"{i}️⃣ 第{i}条详情\n"
        
        messages.append(nav)
        
        return messages
    
    def _split_messages(
        self, 
        messages: List[str], 
        channel: ChannelType
    ) -> List[str]:
        """分割超长消息"""
        limit = self.LIMITS.get(channel, 2000)
        result = []
        
        for msg in messages:
            if len(msg) <= limit:
                result.append(msg)
            else:
                # 分割长消息
                while len(msg) > limit:
                    # 在换行处分割
                    split_pos = msg.rfind("\n", 0, limit - 10)
                    if split_pos < limit * 0.5:
                        split_pos = limit - 10
                    
                    result.append(msg[:split_pos] + "\n（续）")
                    msg = msg[split_pos:].lstrip()
                
                if msg:
                    result.append(msg)
        
        return result
    
    def format_single_item(
        self, 
        item: ContentItem, 
        channel: ChannelType
    ) -> str:
        """格式化单条内容用于详细展示"""
        if channel == ChannelType.TELEGRAM:
            return f"""*{item.title}*

来源: {item.source}

{item.summary or '暂无摘要'}

[阅读原文]({item.url})
"""
        else:
            return f"""{item.title}

来源: {item.source}

{item.summary or '暂无摘要'}

👉 {item.url}
"""
