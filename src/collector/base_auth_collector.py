"""
带认证的采集器基类
用于需要登录认证的信息渠道
"""
import json
from abc import abstractmethod
from typing import Any, Dict, Optional

import httpx

from src.auth_manager import decrypt_credentials, get_auth_manager
from src.collector.base import BaseCollector, CollectorResult
from src.database import get_session
from src.models import ContentItem, SourceType


class AuthError(Exception):
    """认证错误"""
    pass


class AuthExpiredError(AuthError):
    """认证过期错误"""
    pass


class AuthRequiredError(AuthError):
    """需要认证错误"""
    pass


class AuthenticatedCollector(BaseCollector):
    """
    带认证的采集器基类
    
    用于需要登录认证的信息渠道（如即刻、知乎等）
    """
    
    def __init__(self, name: str, source_type: SourceType, config: Optional[Dict] = None):
        super().__init__(name, source_type, config)
        self.auth_source = config.get("auth_source", name) if config else name
        self._auth_headers: Optional[Dict[str, str]] = None
        self._auth_cookies: Optional[str] = None
    
    async def _load_auth(self) -> bool:
        """
        加载认证信息
        
        Returns:
            是否成功加载有效认证
            
        Raises:
            AuthRequiredError: 未配置认证
            AuthExpiredError: 认证已过期
        """
        async with get_session() as session:
            from src.database import AuthCredentialRepository
            repo = AuthCredentialRepository(session)
            credential = await repo.get_by_source(self.auth_source)
        
        if not credential:
            raise AuthRequiredError(
                f"[{self.name}] 需要认证信息，请运行: python -m src.cli auth add {self.auth_source}"
            )
        
        if not credential.is_valid:
            raise AuthExpiredError(
                f"[{self.name}] 认证已失效，请更新: python -m src.cli auth update {self.auth_source}"
            )
        
        # 解密凭证
        try:
            self._auth_cookies = decrypt_credentials(credential.credentials)
            self._auth_headers = json.loads(credential.headers or "{}")
            self._auth_headers["Cookie"] = self._auth_cookies
            return True
        except Exception as e:
            raise AuthError(f"加载认证信息失败: {str(e)}")
    
    def get_auth_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        获取带认证的请求头
        
        Args:
            extra_headers: 额外的请求头
            
        Returns:
            完整的请求头字典
        """
        if not self._auth_headers:
            raise AuthError("认证信息未加载，请先调用 _load_auth()")
        
        headers = dict(self._auth_headers)
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    async def mark_auth_invalid(self, reason: str = None):
        """标记认证为失效"""
        async with get_session() as session:
            from src.database import AuthCredentialRepository
            repo = AuthCredentialRepository(session)
            await repo.mark_invalid(self.auth_source, reason)
    
    async def fetch_with_auth(
        self, 
        url: str, 
        method: str = "GET",
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        发送带认证的 HTTP 请求
        
        Args:
            url: 请求 URL
            method: HTTP 方法
            extra_headers: 额外的请求头
            **kwargs: 其他请求参数
            
        Returns:
            HTTP 响应
            
        Raises:
            AuthExpiredError: 认证过期（HTTP 401/403）
        """
        headers = self.get_auth_headers(extra_headers)
        
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            follow_redirects=True,
            **kwargs
        )
        
        # 检查认证失效
        if response.status_code in (401, 403):
            await self.mark_auth_invalid(f"HTTP {response.status_code}")
            raise AuthExpiredError(
                f"[{self.name}] 认证已失效 (HTTP {response.status_code})，"
                f"请更新: python -m src.cli auth update {self.auth_source}"
            )
        
        response.raise_for_status()
        return response
    
    async def collect(self) -> CollectorResult:
        """
        执行采集（带认证检查）
        
        Returns:
            CollectorResult: 采集结果
        """
        try:
            # 加载认证
            await self._load_auth()
            
            # 执行实际采集
            return await self.collect_with_auth()
            
        except AuthRequiredError as e:
            return CollectorResult(
                success=False,
                message=str(e),
                items=[]
            )
        except AuthExpiredError as e:
            return CollectorResult(
                success=False,
                message=str(e),
                items=[]
            )
        except Exception as e:
            return CollectorResult(
                success=False,
                message=f"采集失败: {str(e)}",
                items=[]
            )
    
    @abstractmethod
    async def collect_with_auth(self) -> CollectorResult:
        """
        执行实际采集（子类必须实现）
        
        此方法在认证信息已加载后调用，可以直接使用 self._auth_headers
        
        Returns:
            CollectorResult: 采集结果
        """
        pass


class JikeAuthenticatedCollector(AuthenticatedCollector):
    """
    即刻认证采集器
    
    采集用户关注的圈子动态和精选内容
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("jike_feed", SourceType.SOCIAL, config)
        self.auth_source = "jike"
        self.base_url = "https://web.okjike.com"
        self.api_base = "https://api.okjike.com/api/graphql"
    
    async def collect_with_auth(self) -> CollectorResult:
        """采集即刻关注流"""
        items = []
        
        # GraphQL 查询 - 获取关注流
        query = {
            "operationName": "FollowFeed",
            "variables": {
                "limit": 20
            },
            "query": """
                query FollowFeed($limit: Int!) {
                    viewer {
                        followFeed(limit: $limit) {
                            items {
                                ... on Post {
                                    id
                                    content
                                    urlsInContent {
                                        originalUrl
                                        title
                                    }
                                    user {
                                        screenName
                                        briefIntro
                                    }
                                    topic {
                                        content
                                    }
                                    createdAt
                                    likeCount
                                    commentCount
                                    repostCount
                                }
                            }
                        }
                    }
                }
            """
        }
        
        try:
            response = await self.fetch_with_auth(
                self.api_base,
                method="POST",
                json=query,
                extra_headers={
                    "Content-Type": "application/json",
                    "Referer": "https://web.okjike.com/",
                    "Origin": "https://web.okjike.com"
                }
            )
            
            data = response.json()
            feed_items = data.get("data", {}).get("viewer", {}).get("followFeed", {}).get("items", [])
            
            for feed_item in feed_items:
                content = feed_item.get("content", "")
                urls = feed_item.get("urlsInContent", [])
                user = feed_item.get("user", {})
                topic = feed_item.get("topic", {})
                
                # 构建标题
                title = content[:50] + "..." if len(content) > 50 else content
                if not title:
                    title = f"来自 {user.get('screenName', '未知用户')} 的动态"
                
                # 构建 URL
                url = f"https://web.okjike.com/post/{feed_item.get('id')}"
                if urls:
                    url = urls[0].get("originalUrl", url)
                
                # 构建完整内容
                full_content = content
                if topic.get("content"):
                    full_content = f"【{topic['content']}】\n{full_content}"
                
                item = self.create_content_item(
                    title=title,
                    url=url,
                    content=full_content,
                    author=user.get("screenName"),
                    publish_time=self._parse_timestamp(feed_item.get("createdAt")),
                    popularity_score=min(feed_item.get("likeCount", 0) / 100, 10),
                    extra={
                        "likes": feed_item.get("likeCount", 0),
                        "comments": feed_item.get("commentCount", 0),
                        "reposts": feed_item.get("repostCount", 0),
                        "source": "即刻",
                        "topic": topic.get("content", ""),
                        "user_intro": user.get("briefIntro", "")
                    }
                )
                
                if self.should_include(item):
                    items.append(item)
            
            return CollectorResult(
                success=True,
                items=items,
                total_found=len(feed_items),
                total_filtered=len(feed_items) - len(items)
            )
            
        except Exception as e:
            return CollectorResult(
                success=False,
                message=f"即刻采集失败: {str(e)}",
                items=items
            )
    
    def _parse_timestamp(self, ts: Any) -> Optional[Any]:
        """解析时间戳"""
        if not ts:
            return None
        try:
            from datetime import datetime
            # 即刻使用 ISO 8601 格式
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None


class ZhihuAuthenticatedCollector(AuthenticatedCollector):
    """
    知乎认证采集器
    
    采集用户关注动态和推荐内容
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("zhihu_feed", SourceType.SOCIAL, config)
        self.auth_source = "zhihu"
        self.api_base = "https://www.zhihu.com"
    
    async def collect_with_auth(self) -> CollectorResult:
        """采集知乎关注流"""
        items = []
        
        try:
            # 获取关注动态
            response = await self.fetch_with_auth(
                f"{self.api_base}/api/v4/moments?limit=20",
                extra_headers={
                    "Referer": "https://www.zhihu.com/",
                    "X-Requested-With": "fetch"
                }
            )
            
            data = response.json()
            moments = data.get("data", [])
            
            for moment in moments:
                action_text = moment.get("action_text", "")
                target = moment.get("target", {})
                
                if not target:
                    continue
                
                target_type = target.get("type", "")
                
                if target_type == "answer":
                    title = target.get("question", {}).get("title", "")
                    content = target.get("excerpt", "")[:200]
                    url = f"https://www.zhihu.com/question/{target.get('question', {}).get('id', '')}/answer/{target.get('id', '')}"
                    author = target.get("author", {}).get("name", "")
                    
                elif target_type == "article":
                    title = target.get("title", "")
                    content = target.get("excerpt", "")[:200]
                    url = f"https://zhuanlan.zhihu.com/p/{target.get('id', '')}"
                    author = target.get("author", {}).get("name", "")
                    
                elif target_type == "question":
                    title = target.get("title", "")
                    content = ""
                    url = f"https://www.zhihu.com/question/{target.get('id', '')}"
                    author = ""
                else:
                    continue
                
                if not title:
                    continue
                
                item = self.create_content_item(
                    title=title,
                    url=url,
                    content=content,
                    author=author,
                    extra={
                        "action": action_text,
                        "type": target_type,
                        "source": "知乎",
                        "voteup_count": target.get("voteup_count", 0),
                        "comment_count": target.get("comment_count", 0)
                    }
                )
                
                if self.should_include(item):
                    items.append(item)
            
            return CollectorResult(
                success=True,
                items=items,
                total_found=len(moments),
                total_filtered=len(moments) - len(items)
            )
            
        except Exception as e:
            return CollectorResult(
                success=False,
                message=f"知乎采集失败: {str(e)}",
                items=items
            )


class BilibiliAuthenticatedCollector(AuthenticatedCollector):
    """
    B站认证采集器
    
    采集用户关注的 UP 主动态
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("bilibili_following", SourceType.VIDEO, config)
        self.auth_source = "bilibili"
        self.api_base = "https://api.bilibili.com"
    
    async def collect_with_auth(self) -> CollectorResult:
        """采集B站关注动态"""
        items = []
        
        try:
            # 获取关注动态
            response = await self.fetch_with_auth(
                f"{self.api_base}/x/web-interface/dynamic/region?ps=20",
                extra_headers={
                    "Referer": "https://t.bilibili.com/"
                }
            )
            
            data = response.json()
            cards = data.get("data", {}).get("cards", [])
            
            for card in cards:
                card_data = json.loads(card.get("card", "{}"))
                desc = card.get("desc", {})
                
                bvid = desc.get("bvid", "")
                dynamic_type = desc.get("type", 0)
                
                # 只处理视频动态
                if dynamic_type != 8:
                    continue
                
                title = card_data.get("title", "")
                if not title:
                    continue
                
                owner = card_data.get("owner", {})
                
                item = self.create_content_item(
                    title=title,
                    url=f"https://www.bilibili.com/video/{bvid}",
                    content=card_data.get("desc", ""),
                    author=owner.get("name", ""),
                    image_url=card_data.get("pic", ""),
                    extra={
                        "source": "B站",
                        "bvid": bvid,
                        "uid": desc.get("uid", ""),
                        "view": card_data.get("stat", {}).get("view", 0),
                        "like": card_data.get("stat", {}).get("like", 0),
                        "duration": card_data.get("duration", "")
                    }
                )
                
                if self.should_include(item):
                    items.append(item)
            
            return CollectorResult(
                success=True,
                items=items,
                total_found=len(cards),
                total_filtered=len(cards) - len(items)
            )
            
        except Exception as e:
            return CollectorResult(
                success=False,
                message=f"B站采集失败: {str(e)}",
                items=items
            )
