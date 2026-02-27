"""
API 采集器
支持各种 REST API 数据源
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class APICollector(BaseCollector):
    """通用 API 采集器"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.API, config)
        self.endpoint = config.get("endpoint")
        self.params = config.get("params", {})
        self.headers = config.get("headers", {})
        
        if not self.endpoint:
            raise ValueError(f"API采集器 {name} 必须配置 endpoint")
    
    async def collect(self) -> CollectorResult:
        """采集 API 数据"""
        result = CollectorResult()
        
        try:
            response = await self.fetch_url(
                self.endpoint,
                params=self.params,
                headers=self.headers
            )
            data = response.json()
            
            items = self._parse_response(data)
            result.total_found = len(items)
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"
            
        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"
        
        return result
    
    def _parse_response(self, data: Any) -> List[ContentItem]:
        """
        解析 API 响应
        
        子类可以重写此方法以适配不同的 API 格式
        """
        # 默认假设返回的是列表
        if isinstance(data, list):
            return [self._create_item_from_dict(item) for item in data]
        
        # 或者包含 items/results 字段的对象
        if isinstance(data, dict):
            for key in ["items", "results", "data", "articles", "stories"]:
                if key in data and isinstance(data[key], list):
                    return [self._create_item_from_dict(item) for item in data[key]]
        
        return []
    
    def _create_item_from_dict(self, data: Dict) -> ContentItem:
        """从字典创建内容条目"""
        # 通用字段映射
        title = data.get("title", "无标题")
        url = data.get("url", data.get("link", ""))
        content = data.get("content", data.get("description", ""))
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content,
            raw_data=data
        )


class HackerNewsCollector(BaseCollector):
    """Hacker News 采集器"""
    
    API_BASE = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.API, config)
        self.min_score = config.get("filter", {}).get("min_score", 100)
        self.max_items = config.get("max_items", 30)
    
    async def collect(self) -> CollectorResult:
        """采集 Hacker News 热门内容"""
        result = CollectorResult()
        
        try:
            # 获取热门故事 ID 列表
            response = await self.fetch_url(f"{self.API_BASE}/topstories.json")
            story_ids = response.json()[:self.max_items]
            
            result.total_found = len(story_ids)
            
            # 获取每个故事的详情
            for story_id in story_ids:
                try:
                    story = await self._get_story(story_id)
                    if not story:
                        continue
                    
                    # 过滤低分内容
                    if story.get("score", 0) < self.min_score:
                        result.total_filtered += 1
                        continue
                    
                    item = self._parse_story(story)
                    if self.should_include(item):
                        result.items.append(item)
                    else:
                        result.total_filtered += 1
                        
                except Exception as e:
                    continue
            
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"
            
        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"
        
        return result
    
    async def _get_story(self, story_id: int) -> Optional[Dict]:
        """获取故事详情"""
        response = await self.fetch_url(f"{self.API_BASE}/item/{story_id}.json")
        return response.json()
    
    def _parse_story(self, story: Dict) -> ContentItem:
        """解析故事数据"""
        title = story.get("title", "无标题")
        
        # HN 可能有外部 URL 或讨论页面
        url = story.get("url", "")
        if not url:
            # 使用 HN 讨论页面
            url = f"https://news.ycombinator.com/item?id={story.get('id')}"
        
        content = story.get("text", "")  # 有文本内容的帖子
        score = story.get("score", 0)
        descendants = story.get("descendants", 0)  # 评论数
        
        # 作者
        author = story.get("by", "")
        
        # 时间
        time_unix = story.get("time", 0)
        publish_time = datetime.utcfromtimestamp(time_unix) if time_unix else None
        
        return self.create_content_item(
            title=title,
            url=url,
            content=content,
            author=author,
            publish_time=publish_time,
            popularity_score=float(score),
            extra={
                "score": score,
                "comments": descendants,
                "hn_id": story.get("id")
            }
        )


class GitHubTrendingCollector(BaseCollector):
    """GitHub Trending 采集器"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.GITHUB, config)
        self.language = config.get("language", "")
        self.since = config.get("since", "daily")  # daily, weekly, monthly
    
    async def collect(self) -> CollectorResult:
        """
        采集 GitHub Trending
        注意：GitHub 官方没有 Trending API，需要爬取网页
        """
        result = CollectorResult()
        
        try:
            # GitHub trending 页面
            url = "https://github.com/trending"
            if self.language:
                url += f"/{self.language}"
            url += f"?since={self.since}"
            
            from bs4 import BeautifulSoup
            
            response = await self.fetch_url(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 解析 trending 仓库
            articles = soup.find_all("article", class_="Box-row")
            result.total_found = len(articles)
            
            for article in articles:
                try:
                    item = self._parse_repo(article)
                    if self.should_include(item):
                        result.items.append(item)
                    else:
                        result.total_filtered += 1
                except Exception as e:
                    continue
            
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条内容"
            
        except Exception as e:
            result.success = False
            result.message = f"采集失败: {str(e)}"
        
        return result
    
    def _parse_repo(self, article) -> ContentItem:
        """解析仓库信息"""
        from bs4 import BeautifulSoup
        
        # 仓库名称
        h2 = article.find("h2")
        repo_name = h2.get_text(strip=True).replace(" ", "").replace("\n", "")
        
        # 链接
        link = h2.find("a")["href"]
        url = f"https://github.com{link}"
        
        # 描述
        desc_p = article.find("p", class_="col-9")
        description = desc_p.get_text(strip=True) if desc_p else ""
        
        # 语言
        lang_span = article.find("span", itemprop="programmingLanguage")
        language = lang_span.get_text(strip=True) if lang_span else "Unknown"
        
        # Stars
        stars_div = article.find("a", class_="Link--muted")
        stars_text = stars_div.get_text(strip=True) if stars_div else "0"
        stars = self._parse_count(stars_text)
        
        return self.create_content_item(
            title=f"{repo_name} - Trending",
            url=url,
            content=description,
            keywords=[language],
            popularity_score=float(stars),
            extra={
                "language": language,
                "stars_today": stars_text,
                "type": "github_repo"
            }
        )
    
    def _parse_count(self, text: str) -> int:
        """解析数字（处理 k/m 后缀）"""
        text = text.lower().replace(",", "")
        try:
            if "k" in text:
                return int(float(text.replace("k", "")) * 1000)
            elif "m" in text:
                return int(float(text.replace("m", "")) * 1000000)
            else:
                return int(text)
        except ValueError:
            return 0
