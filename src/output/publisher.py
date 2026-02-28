"""
内容发布/推送模块
支持多种推送渠道
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from src.config import get_settings
from src.models import ChannelType, ContentItem, DailyReport
from src.output.formatter import ChatFormatter, HTMLFormatter, MarkdownFormatter

settings = get_settings()


@dataclass
class PushResult:
    """推送结果"""
    success: bool
    channel: ChannelType
    message: str
    message_ids: Optional[List[str]] = None


class Publisher:
    """发布器"""
    
    def __init__(self):
        self.formatters = {
            "markdown": MarkdownFormatter(),
            "html": HTMLFormatter(),
            "chat": ChatFormatter(),
        }
        self._clients: Dict[str, Any] = {}
    
    async def publish(
        self, 
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]],
        channels: List[ChannelType],
        user_config: Optional[Dict] = None
    ) -> Dict[ChannelType, PushResult]:
        """
        发布日报到多个渠道
        """
        results = {}
        
        for channel in channels:
            try:
                print(f"[Publisher] 开始推送到 {channel.value}")
                
                if channel == ChannelType.TELEGRAM:
                    result = await self._push_telegram(
                        report, columns_config, items_by_column
                    )
                elif channel == ChannelType.SLACK:
                    result = await self._push_slack(
                        report, columns_config, items_by_column
                    )
                elif channel == ChannelType.DISCORD:
                    result = await self._push_discord(
                        report, columns_config, items_by_column
                    )
                elif channel == ChannelType.EMAIL:
                    result = await self._push_email(
                        report, columns_config, items_by_column
                    )
                elif channel == ChannelType.IMARKDOWN:
                    result = await self._save_markdown(
                        report, columns_config, items_by_column
                    )
                else:
                    result = PushResult(
                        success=False,
                        channel=channel,
                        message=f"不支持的渠道: {channel}"
                    )
                
                results[channel] = result
                print(f"[Publisher] {channel.value} 结果: {result.message}")
                
            except Exception as e:
                import traceback
                print(f"[Publisher] {channel.value} 异常: {e}")
                traceback.print_exc()
                results[channel] = PushResult(
                    success=False,
                    channel=channel,
                    message=str(e)
                )
        
        return results
    
    async def _push_telegram(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> PushResult:
        """推送到 Telegram（简化版）"""
        print(f"[Telegram] 开始推送，报告 ID: {report.id}")
        
        # 检查配置
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return PushResult(
                success=False,
                channel=ChannelType.TELEGRAM,
                message="Telegram 配置缺失"
            )
        
        # 检查内容
        has_content = any(items for items in items_by_column.values() if items)
        if not has_content:
            return PushResult(
                success=False,
                channel=ChannelType.TELEGRAM,
                message="日报没有内容"
            )
        
        # 直接构建简单消息，不使用复杂模板
        messages = []
        
        # 标题
        header = f"📰 *{report.title}*\n"
        header += f"📅 {report.date.strftime('%Y年%m月%d日')}\n"
        header += f"📊 共 {report.total_items} 条精选内容\n\n"
        messages.append(header)
        
        # 各分栏内容
        for col_config in columns_config:
            col_id = col_config.get("id")
            col_name = col_config.get("name", col_id)
            items = items_by_column.get(col_id, [])
            
            if not items:
                continue
            
            section = f"*📂 {col_name}*\n\n"
            
            for item in items[:5]:  # 每栏最多5条
                # 安全获取字段
                title = str(item.title) if item.title else "无标题"
                url = str(item.url) if item.url else ""
                summary = ""
                if hasattr(item, 'summary') and item.summary:
                    summary = str(item.summary)[:100] + "..."
                
                section += f"• *{title}*\n"
                if summary:
                    section += f"  {summary}\n"
                if url:
                    section += f"  [阅读原文]({url})\n"
                section += "\n"
            
            messages.append(section)
        
        # 合并消息（如果不太长）
        full_message = "\n".join(messages)
        
        # Telegram 限制 4096 字符
        MAX_LENGTH = 4000
        if len(full_message) > MAX_LENGTH:
            # 分段发送
            chunks = []
            current = ""
            for msg in messages:
                if len(current) + len(msg) > MAX_LENGTH:
                    if current:
                        chunks.append(current)
                    current = msg
                else:
                    current += msg
            if current:
                chunks.append(current)
        else:
            chunks = [full_message]
        
        print(f"[Telegram] 分成 {len(chunks)} 段发送")
        
        # 发送
        client = httpx.AsyncClient(timeout=30.0)
        message_ids = []
        
        try:
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": settings.telegram_chat_id,
                        "text": chunk,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                        "disable_notification": i > 0
                    }
                )
                
                data = response.json()
                
                if data.get("ok"):
                    msg_id = data.get("result", {}).get("message_id")
                    if msg_id:
                        message_ids.append(str(msg_id))
                else:
                    error_msg = data.get("description", "未知错误")
                    print(f"[Telegram] 发送失败: {error_msg}")
                    
                    # 尝试纯文本
                    if "parse" in error_msg.lower() or "markdown" in error_msg.lower():
                        plain_response = await client.post(
                            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                            json={
                                "chat_id": settings.telegram_chat_id,
                                "text": chunk[:MAX_LENGTH],
                                "disable_notification": i > 0
                            }
                        )
                        plain_data = plain_response.json()
                        if plain_data.get("ok"):
                            msg_id = plain_data.get("result", {}).get("message_id")
                            if msg_id:
                                message_ids.append(str(msg_id))
            
            if message_ids:
                return PushResult(
                    success=True,
                    channel=ChannelType.TELEGRAM,
                    message=f"成功发送 {len(message_ids)} 条消息",
                    message_ids=message_ids
                )
            else:
                return PushResult(
                    success=False,
                    channel=ChannelType.TELEGRAM,
                    message="发送失败"
                )
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return PushResult(
                success=False,
                channel=ChannelType.TELEGRAM,
                message=f"异常: {str(e)}"
            )
        finally:
            await client.aclose()
    
    async def _push_slack(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> PushResult:
        """推送到 Slack"""
        if not settings.slack_bot_token or not settings.slack_channel:
            return PushResult(
                success=False,
                channel=ChannelType.SLACK,
                message="Slack 配置缺失"
            )
        
        formatter = self.formatters["markdown"]
        content = formatter.format_report(report, columns_config, items_by_column)
        
        client = httpx.AsyncClient(timeout=30.0)
        
        try:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                json={
                    "channel": settings.slack_channel,
                    "text": content[:3000],
                    "unfurl_links": True
                }
            )
            data = response.json()
            
            if data.get("ok"):
                return PushResult(
                    success=True,
                    channel=ChannelType.SLACK,
                    message="发送成功",
                    message_ids=[data["ts"]]
                )
            else:
                return PushResult(
                    success=False,
                    channel=ChannelType.SLACK,
                    message=f"发送失败: {data.get('error')}"
                )
        except Exception as e:
            return PushResult(
                success=False,
                channel=ChannelType.SLACK,
                message=str(e)
            )
        finally:
            await client.aclose()
    
    async def _push_discord(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> PushResult:
        """推送到 Discord"""
        if not settings.discord_bot_token or not settings.discord_channel_id:
            return PushResult(
                success=False,
                channel=ChannelType.DISCORD,
                message="Discord 配置缺失"
            )
        
        formatter = self.formatters["markdown"]
        content = formatter.format_report(report, columns_config, items_by_column)
        
        client = httpx.AsyncClient(timeout=30.0)
        
        try:
            chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
            message_ids = []
            
            for chunk in chunks:
                response = await client.post(
                    f"https://discord.com/api/v10/channels/{settings.discord_channel_id}/messages",
                    headers={"Authorization": f"Bot {settings.discord_bot_token}"},
                    json={"content": chunk}
                )
                data = response.json()
                
                if response.status_code == 200:
                    message_ids.append(data["id"])
                else:
                    return PushResult(
                        success=False,
                        channel=ChannelType.DISCORD,
                        message=f"发送失败: {data}"
                    )
            
            return PushResult(
                success=True,
                channel=ChannelType.DISCORD,
                message=f"成功发送 {len(message_ids)} 条消息",
                message_ids=message_ids
            )
        except Exception as e:
            return PushResult(
                success=False,
                channel=ChannelType.DISCORD,
                message=str(e)
            )
        finally:
            await client.aclose()
    
    async def _push_email(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> PushResult:
        """发送邮件"""
        if not settings.smtp_host or not settings.email_to:
            return PushResult(
                success=False,
                channel=ChannelType.EMAIL,
                message="邮件配置缺失"
            )
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            formatter = self.formatters["html"]
            html_content = formatter.format_report(report, columns_config, items_by_column)
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{report.title} - {report.date.strftime('%Y-%m-%d')}"
            msg["From"] = settings.email_from or settings.smtp_user
            msg["To"] = settings.email_to
            
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True
            )
            
            return PushResult(
                success=True,
                channel=ChannelType.EMAIL,
                message="邮件发送成功"
            )
        except Exception as e:
            return PushResult(
                success=False,
                channel=ChannelType.EMAIL,
                message=str(e)
            )
    
    async def _save_markdown(
        self,
        report: DailyReport,
        columns_config: List[Dict],
        items_by_column: Dict[str, List[ContentItem]]
    ) -> PushResult:
        """保存为 Markdown 文件"""
        import os
        from datetime import datetime
        
        try:
            formatter = self.formatters["markdown"]
            content = formatter.format_report(report, columns_config, items_by_column)
            
            exports_dir = "data/exports"
            os.makedirs(exports_dir, exist_ok=True)
            
            filename = f"daily_report_{report.date.strftime('%Y%m%d')}.md"
            filepath = os.path.join(exports_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            return PushResult(
                success=True,
                channel=ChannelType.IMARKDOWN,
                message=f"已保存到 {filepath}"
            )
        except Exception as e:
            return PushResult(
                success=False,
                channel=ChannelType.IMARKDOWN,
                message=str(e)
            )
