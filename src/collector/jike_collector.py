"""
即刻采集器
支持采集即刻热门动态、圈子内容等
即刻是兴趣圈子社区，信息筛选效率高
"""
from datetime import datetime
from typing import Dict, List, Optional
import json

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class JikeCollector(BaseCollector):
    """
    即刻采集器
    
    特点：
    - 兴趣圈子社区
    - 信息筛选效率高
    - 内容质量相对较高
    
    采集方式：API + 网页解析
    注意：即刻需要登录才能访问大部分内容
    """
    
    BASE_URL = "https://web.okjike.com"
    API_URL = "https://api.okjike.com/api/graphql"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.SOCIAL, config)
        self.collect_type = config.get("collect_type", "topic")  # topic, user, recommend
        self.topic_id = config.get("topic_id")  # 圈子/话题ID
        self.username = config.get("username")
        self.limit = config.get("limit", 10)
        
        # 即刻需要登录
        self.token = config.get("token")
        self.refresh_token = config.get("refresh_token")
        
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://web.okjike.com/",
            "Content-Type": "application/json",
        }
        
        if self.token:
            self._headers["x-jike-access-token"] = self.token
    
    async def collect(self) -> CollectorResult:
        """采集即刻内容"""
        result = CollectorResult()
        
        try:
            if self.collect_type == "topic" and self.topic_id:
                items = await self._collect_by_topic()
            elif self.collect_type == "user" and self.username:
                items = await self._collect_by_user()
            elif self.collect_type == "recommend":
                items = await self._collect_recommend()
            else:
                result.success = False
                result.message = "配置错误：请提供有效的 collect_type 和对应参数"
                return result
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条即刻内容"
            
        except Exception as e:
            result.success = False
            result.message = f"即刻采集失败: {str(e)}"
        
        return result
    
    async def _collect_by_topic(self) -> List[ContentItem]:
        """采集指定圈子的内容"""
        # GraphQL 查询
        query = """
        query GetTopicMessages($id: ID!, $limit: Int!) {
          topic(id: $id) {
            feeds(limit: $limit) {
              ... on MessageConnection {
                nodes {
                  id
                  content
                  createdAt
                  likeCount
                  commentCount
                  repostCount
                  shareCount
                  pictures {
                    picUrl
                  }
                  topic {
                    content
                    id
                  }
                  user {
                    screenName
                    username
                    avatarImage {
                      picUrl
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        payload = {
            "query": query,
            "variables": {
                "id": self.topic_id,
                "limit": self.limit
            }
        }
        
        response = await self.fetch_url(
            self.API_URL,
            method="POST",
            json=payload,
            headers=self._headers
        )
        
        data = response.json()
        
        items = []
        if data.get("data", {}).get("topic", {}).get("feeds", {}).get("nodes"):
            for message in data["data"]["topic"]["feeds"]["nodes"]:
                item = self._parse_message(message)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_by_user(self) -> List[ContentItem]:
        """采集指定用户的内容"""
        query = """
        query GetUserMessages($username: String!, $limit: Int!) {
          userProfile(username: $username) {
            posts(limit: $limit) {
              ... on MessageConnection {
                nodes {
                  id
                  content
                  createdAt
                  likeCount
                  commentCount
                  repostCount
                  pictures {
                    picUrl
                  }
                  topic {
                    content
                    id
                  }
                }
              }
            }
          }
        }
        """
        
        payload = {
            "query": query,
            "variables": {
                "username": self.username,
                "limit": self.limit
            }
        }
        
        response = await self.fetch_url(
            self.API_URL,
            method="POST",
            json=payload,
            headers=self._headers
        )
        
        data = response.json()
        
        items = []
        if data.get("data", {}).get("userProfile", {}).get("posts", {}).get("nodes"):
            for message in data["data"]["userProfile"]["posts"]["nodes"]:
                item = self._parse_message(message)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_recommend(self) -> List[ContentItem]:
        """采集推荐内容"""
        # 推荐内容需要登录
        if not self.token:
            return []
        
        query = """
        query GetRecommendedMessages($limit: Int!) {
          recommendFeeds(limit: $limit) {
            ... on MessageConnection {
              nodes {
                id
                content
                createdAt
                likeCount
                commentCount
                repostCount
                pictures {
                  picUrl
                }
                topic {
                  content
                  id
                }
                user {
                  screenName
                  username
                }
              }
            }
          }
        }
        """
        
        payload = {
            "query": query,
            "variables": {"limit": self.limit}
        }
        
        response = await self.fetch_url(
            self.API_URL,
            method="POST",
            json=payload,
            headers=self._headers
        )
        
        data = response.json()
        
        items = []
        if data.get("data", {}).get("recommendFeeds", {}).get("nodes"):
            for message in data["data"]["recommendFeeds"]["nodes"]:
                item = self._parse_message(message)
                if item:
                    items.append(item)
        
        return items
    
    def _parse_message(self, message: Dict) -> Optional[ContentItem]:
        """解析即刻消息"""
        message_id = message.get("id")
        if not message_id:
            return None
        
        content = message.get("content", "")
        if not content:
            return None
        
        # 标题：取内容前50字
        title = content[:50] + "..." if len(content) > 50 else content
        
        # 链接
        url = f"{self.BASE_URL}/post-detail/{message_id}/originalPost"
        
        # 作者
        author = ""
        user = message.get("user", {})
        if user:
            author = user.get("screenName", user.get("username", ""))
        
        # 发布时间
        publish_time = None
        created_at = message.get("createdAt")
        if created_at:
            try:
                publish_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                pass
        
        # 统计数据
        like_count = message.get("likeCount", 0)
        comment_count = message.get("commentCount", 0)
        repost_count = message.get("repostCount", 0)
        share_count = message.get("shareCount", 0)
        
        # 图片
        image_url = None
        pictures = message.get("pictures", [])
        if pictures and len(pictures) > 0:
            image_url = pictures[0].get("picUrl")
        
        # 话题/圈子
        topic_name = ""
        topic = message.get("topic", {})
        if topic:
            topic_name = topic.get("content", "")
        
        content_parts = [
            f"作者: @{author}" if author else "",
            f"圈子: {topic_name}" if topic_name else "",
            f"点赞: {like_count} | 评论: {comment_count} | 转发: {repost_count}",
            "",
            content
        ]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(filter(None, content_parts)),
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            source=f"即刻-{topic_name}" if topic_name else "即刻",
            popularity_score=float(like_count + comment_count * 2 + repost_count * 3),
            keywords=["即刻", topic_name] if topic_name else ["即刻"],
            extra={
                "message_id": message_id,
                "topic_id": topic.get("id") if topic else None,
                "topic_name": topic_name,
                "like_count": like_count,
                "comment_count": comment_count,
                "repost_count": repost_count,
                "share_count": share_count,
                "pictures_count": len(pictures),
                "platform": "jike"
            }
        )


class JikeTopicCollector(JikeCollector):
    """
    即刻圈子采集器（简化版）
    """
    
    def __init__(self, name: str, config: Dict):
        config["collect_type"] = "topic"
        if not config.get("topic_id"):
            raise ValueError("必须配置 topic_id")
        super().__init__(name, config)
