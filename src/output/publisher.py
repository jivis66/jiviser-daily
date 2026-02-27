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
        
        Args:
            report: 日报
            columns_config: 分栏配置
            items_by_column: 分栏内容
            channels: 推送渠道列表
            user_config: 用户配置
            
        Returns:
            Dict[ChannelType, PushResult]: 推送结果
        """
        results = {}
        
        for channel in channels:
            try:
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
                
            except Exception as e:
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
        """推送到 Telegram"""
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return PushResult(
                success=False,
                channel=ChannelType.TELEGRAM,
                message="Telegram 配置缺失"
            )
        
        formatter = self.formatters["chat"]
        messages = formatter.format_for_channel(
            report, columns_config, items_by_column, ChannelType.TELEGRAM
        )
        
        client = httpx.AsyncClient(timeout=30.0)
        message_ids = []
        
        try:
            for msg in messages:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": settings.telegram_chat_id,
                        "text": msg,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": False
                    }
                )
                data = response.json()
                if data.get("ok"):
                    message_ids.append(str(data["result"]["message_id"]))
                else:
                    return PushResult(
                        success=False,
                        channel=ChannelType.TELEGRAM,
                        message=f"发送失败: {data.get('description')}"
                    )
            
            return PushResult(
                success=True,
                channel=ChannelType.TELEGRAM,
                message=f"成功发送 {len(messages)} 条消息",
                message_ids=message_ids
            )
            
        except Exception as e:
            return PushResult(
                success=False,
                channel=ChannelType.TELEGRAM,
                message=str(e)
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
        
        # 使用 Markdown 格式
        formatter = self.formatters["markdown"]
        content = formatter.format_report(report, columns_config, items_by_column)
        
        client = httpx.AsyncClient(timeout=30.0)
        
        try:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                json={
                    "channel": settings.slack_channel,
                    "text": content[:3000],  # Slack 有长度限制
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
            # Discord 消息长度限制 2000
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
                message=f"成功发送 {len(chunks)} 条消息",
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
            
            # 生成 HTML 内容
            formatter = self.formatters["html"]
            html_content = formatter.format_report(report, columns_config, items_by_column)
            
            # 构建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{report.title} - {report.date.strftime('%Y-%m-%d')}"
            msg["From"] = settings.email_from or settings.smtp_user
            msg["To"] = settings.email_to
            
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # 发送
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
            
            # 保存到 data/exports
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
