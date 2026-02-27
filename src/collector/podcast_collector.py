"""
播客平台采集器
支持采集小宇宙、喜马拉雅、网易云音乐、苹果播客等平台的播客内容
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class XiaoyuzhouCollector(BaseCollector):
    """
    小宇宙播客采集器
    
    特点：
    - 中文播客绝对头部平台
    - 87.1% 用户首选
    - 内容质量高，以知识类播客为主
    
    采集方式：网页解析（需处理反爬）
    注意：小宇宙网页版需要特殊处理
    """
    
    BASE_URL = "https://www.xiaoyuzhoufm.com"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.VIDEO, config)
        self.podcast_id = config.get("podcast_id")  # 播客节目ID
        self.keyword = config.get("keyword")  # 搜索关键词
        self.category = config.get("category", "popular")  # popular, trending, search
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集小宇宙播客"""
        result = CollectorResult()
        
        try:
            if self.podcast_id:
                items = await self._collect_by_podcast()
            elif self.keyword:
                items = await self._collect_search()
            elif self.category == "popular":
                items = await self._collect_popular()
            elif self.category == "trending":
                items = await self._collect_trending()
            else:
                result.success = False
                result.message = "配置错误：请提供 podcast_id、keyword 或有效的 category"
                return result
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条小宇宙播客"
            
        except Exception as e:
            result.success = False
            result.message = f"小宇宙采集失败: {str(e)}"
        
        return result
    
    async def _collect_by_podcast(self) -> List[ContentItem]:
        """采集指定播客节目的内容"""
        url = f"{self.BASE_URL}/podcast/{self.podcast_id}"
        
        response = await self.fetch_url(url)
        html = response.text
        
        # 从 HTML 中提取播客信息
        return self._parse_episodes(html, podcast_id=self.podcast_id)
    
    async def _collect_search(self) -> List[ContentItem]:
        """搜索播客"""
        url = f"{self.BASE_URL}/search?q={self.keyword}"
        
        response = await self.fetch_url(url)
        html = response.text
        
        return self._parse_episodes(html)
    
    async def _collect_popular(self) -> List[ContentItem]:
        """采集热门播客"""
        # 小宇宙热门页面
        url = f"{self.BASE_URL}/discover"
        
        response = await self.fetch_url(url)
        html = response.text
        
        return self._parse_episodes(html)
    
    async def _collect_trending(self) -> List[ContentItem]:
        """采集趋势播客"""
        url = f"{self.BASE_URL}/discover/trending"
        
        response = await self.fetch_url(url)
        html = response.text
        
        return self._parse_episodes(html)
    
    def _parse_episodes(self, html: str, podcast_id: str = None) -> List[ContentItem]:
        """从 HTML 解析播客单集"""
        from bs4 import BeautifulSoup
        import json
        import re
        
        items = []
        soup = BeautifulSoup(html, "html.parser")
        
        # 尝试从 script 标签中提取数据
        script_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.+?});'
        match = re.search(script_pattern, html)
        
        if match:
            try:
                data = json.loads(match.group(1))
                episodes = self._extract_episodes_from_data(data)
                
                for episode in episodes[:self.limit]:
                    item = self._create_episode_item(episode, podcast_id)
                    if item:
                        items.append(item)
            except Exception as e:
                print(f"[Xiaoyuzhou] 解析数据失败: {e}")
        
        # 备用：从 HTML 中直接解析
        if not items:
            episode_elements = soup.find_all("div", class_="episode-item")
            for elem in episode_elements[:self.limit]:
                try:
                    item = self._parse_episode_element(elem)
                    if item:
                        items.append(item)
                except:
                    continue
        
        return items
    
    def _extract_episodes_from_data(self, data: Dict) -> List[Dict]:
        """从 JSON 数据中提取单集列表"""
        episodes = []
        
        # 尝试不同的数据路径
        if "podcast" in data and "episodes" in data["podcast"]:
            episodes = data["podcast"]["episodes"]
        elif "episodes" in data:
            episodes = data["episodes"]
        elif "searchResults" in data:
            for result in data["searchResults"]:
                if "episode" in result:
                    episodes.append(result["episode"])
        
        return episodes
    
    def _create_episode_item(self, episode: Dict, podcast_id: str = None) -> Optional[ContentItem]:
        """从 JSON 数据创建内容项"""
        eid = episode.get("eid") or episode.get("id")
        if not eid:
            return None
        
        title = episode.get("title", "无标题")
        
        # 构建 URL
        pid = podcast_id or episode.get("podcast", {}).get("pid", "")
        url = f"{self.BASE_URL}/episode/{eid}"
        
        # 播客信息
        podcast_name = ""
        if "podcast" in episode:
            podcast_name = episode["podcast"].get("title", "")
        
        # 描述
        description = episode.get("description", "") or episode.get("shownotes", "")
        
        # 时长（秒）
        duration = episode.get("duration", 0)
        duration_str = self._format_duration(duration)
        
        # 发布时间
        publish_time = None
        if "pubDate" in episode:
            try:
                publish_time = datetime.fromisoformat(episode["pubDate"].replace("Z", "+00:00"))
            except:
                pass
        
        # 播放量
        play_count = episode.get("playCount", 0) or episode.get("playcount", 0)
        
        # 封面图
        image_url = None
        if "cover" in episode:
            image_url = episode["cover"].get("url") or episode["cover"].get("medium", {}).get("url")
        elif "image" in episode:
            image_url = episode["image"]
        
        content_parts = [
            f"播客: {podcast_name}",
            f"时长: {duration_str}",
            f"播放量: {play_count}",
            "",
            description[:200] + "..." if len(description) > 200 else description
        ]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(content_parts),
            author=podcast_name,
            publish_time=publish_time,
            image_url=image_url,
            keywords=["播客", "Podcast", podcast_name],
            extra={
                "episode_id": eid,
                "podcast_id": pid,
                "podcast_name": podcast_name,
                "duration": duration,
                "duration_str": duration_str,
                "play_count": play_count,
                "is_audio": True,
                "platform": "xiaoyuzhou"
            }
        )
    
    def _parse_episode_element(self, elem) -> Optional[ContentItem]:
        """从 HTML 元素解析单集"""
        from bs4 import BeautifulSoup
        
        # 标题
        title_elem = elem.find("h3") or elem.find("div", class_="title")
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        
        # 链接
        link_elem = elem.find("a")
        url = link_elem.get("href", "") if link_elem else ""
        if url.startswith("/"):
            url = f"{self.BASE_URL}{url}"
        
        # 播客名
        podcast_elem = elem.find("div", class_="podcast-name")
        podcast_name = podcast_elem.get_text(strip=True) if podcast_elem else ""
        
        return self.create_content_item(
            title=title,
            url=url,
            content=f"播客: {podcast_name}",
            author=podcast_name,
            keywords=["播客", podcast_name],
            extra={
                "podcast_name": podcast_name,
                "is_audio": True,
                "platform": "xiaoyuzhou"
            }
        )
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分{seconds % 60}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分"


class XimalayaCollector(BaseCollector):
    """
    喜马拉雅采集器
    
    特点：
    - 综合音频平台
    - 播客+有声书+知识课程
    - 内容丰富多样
    
    采集方式：API + 网页解析
    """
    
    BASE_URL = "https://www.ximalaya.com"
    API_URL = "https://mobile.ximalaya.com"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.VIDEO, config)
        self.album_id = config.get("album_id")  # 专辑ID
        self.keyword = config.get("keyword")
        self.category = config.get("category", "hot")  # hot, new
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集喜马拉雅内容"""
        result = CollectorResult()
        
        try:
            if self.album_id:
                items = await self._collect_by_album()
            elif self.keyword:
                items = await self._collect_search()
            else:
                result.success = False
                result.message = "配置错误：请提供 album_id 或 keyword"
                return result
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条喜马拉雅内容"
            
        except Exception as e:
            result.success = False
            result.message = f"喜马拉雅采集失败: {str(e)}"
        
        return result
    
    async def _collect_by_album(self) -> List[ContentItem]:
        """采集指定专辑内容"""
        url = f"{self.BASE_URL}/revision/album/v1/getTracksList"
        params = {
            "albumId": self.album_id,
            "pageNum": 1,
            "pageSize": self.limit
        }
        
        response = await self.fetch_url(url, params=params)
        data = response.json()
        
        items = []
        if data.get("ret") == 200 and data.get("data", {}).get("tracks"):
            for track in data["data"]["tracks"][:self.limit]:
                item = self._parse_track(track)
                if item:
                    items.append(item)
        
        return items
    
    async def _collect_search(self) -> List[ContentItem]:
        """搜索内容"""
        url = f"{self.BASE_URL}/revision/search"
        params = {
            "core": "all",
            "kw": self.keyword,
            "page": 1,
            "rows": self.limit
        }
        
        response = await self.fetch_url(url, params=params)
        data = response.json()
        
        items = []
        if data.get("ret") == 200:
            results = data.get("data", {}).get("result", {}).get("response", {}).get("docs", [])
            for doc in results[:self.limit]:
                item = self._parse_search_result(doc)
                if item:
                    items.append(item)
        
        return items
    
    def _parse_track(self, track: Dict) -> Optional[ContentItem]:
        """解析音频轨道"""
        track_id = track.get("trackId")
        if not track_id:
            return None
        
        title = track.get("title", "无标题")
        url = f"{self.BASE_URL}/sound/{track_id}"
        
        # 专辑信息
        album_title = track.get("albumTitle", "")
        album_id = track.get("albumId", "")
        
        # 时长
        duration = track.get("duration", 0)
        duration_str = self._format_duration(duration)
        
        # 播放量
        play_count = track.get("playCount", 0)
        
        # 发布时间
        publish_time = None
        if track.get("createDateFormat"):
            try:
                publish_time = datetime.strptime(track["createDateFormat"], "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        # 封面
        image_url = track.get("coverUrl") or track.get("albumCover")
        
        content_parts = [
            f"专辑: {album_title}",
            f"时长: {duration_str}",
            f"播放量: {self._format_number(play_count)}",
            "",
            track.get("intro", "")[:200]
        ]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(filter(None, content_parts)),
            author=album_title,
            publish_time=publish_time,
            image_url=image_url,
            keywords=["音频", "播客", album_title],
            extra={
                "track_id": track_id,
                "album_id": album_id,
                "album_title": album_title,
                "duration": duration,
                "play_count": play_count,
                "is_audio": True,
                "platform": "ximalaya"
            }
        )
    
    def _parse_search_result(self, doc: Dict) -> Optional[ContentItem]:
        """解析搜索结果"""
        title = doc.get("title", "无标题")
        
        # 移除高亮标签
        title = title.replace("<em>", "").replace("</em>", "")
        
        doc_id = doc.get("id")
        doc_type = doc.get("doc_type")
        
        if doc_type == "track":
            url = f"{self.BASE_URL}/sound/{doc_id}"
        elif doc_type == "album":
            url = f"{self.BASE_URL}/album/{doc_id}"
        else:
            url = doc.get("link", "")
        
        return self.create_content_item(
            title=title,
            url=url,
            content=doc.get("intro", "")[:300],
            author=doc.get("nickname", ""),
            image_url=doc.get("cover_path"),
            keywords=[doc_type] if doc_type else [],
            extra={
                "doc_type": doc_type,
                "play_count": doc.get("play_count", 0),
                "is_audio": doc_type == "track",
                "platform": "ximalaya"
            }
        )
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分{seconds % 60}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分"
    
    def _format_number(self, num: int) -> str:
        """格式化数字"""
        if num >= 100000000:
            return f"{num / 100000000:.1f}亿"
        elif num >= 10000:
            return f"{num / 10000:.1f}万"
        return str(num)


class NeteasePodcastCollector(BaseCollector):
    """
    网易云音乐播客采集器
    
    特点：
    - 播客板块增长迅速
    - 音乐+音频融合
    
    采集方式：API
    """
    
    BASE_URL = "https://music.163.com"
    API_URL = "https://interface.music.163.com"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.VIDEO, config)
        self.radio_id = config.get("radio_id")  # 电台ID
        self.limit = config.get("limit", 10)
    
    async def collect(self) -> CollectorResult:
        """采集网易云音乐播客"""
        result = CollectorResult()
        
        try:
            if not self.radio_id:
                result.success = False
                result.message = "配置错误：请提供 radio_id"
                return result
            
            items = await self._collect_by_radio()
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条网易云播客"
            
        except Exception as e:
            result.success = False
            result.message = f"网易云播客采集失败: {str(e)}"
        
        return result
    
    async def _collect_by_radio(self) -> List[ContentItem]:
        """采集指定电台节目"""
        # 网易云音乐 API
        url = f"{self.API_URL}/weapi/dj/program/byradio"
        
        # 需要加密的参数
        params = {
            "radioId": self.radio_id,
            "limit": self.limit,
            "offset": 0
        }
        
        # 注意：网易云音乐 API 需要加密，这里简化处理
        # 实际使用时需要实现加密逻辑或使用第三方库
        
        response = await self.fetch_url(
            url,
            method="POST",
            data=params,
            headers={
                "Referer": "https://music.163.com/",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        data = response.json()
        
        items = []
        if data.get("code") == 200 and data.get("programs"):
            for program in data["programs"][:self.limit]:
                item = self._parse_program(program)
                if item:
                    items.append(item)
        
        return items
    
    def _parse_program(self, program: Dict) -> Optional[ContentItem]:
        """解析电台节目"""
        program_id = program.get("id")
        if not program_id:
            return None
        
        title = program.get("name", "无标题")
        url = f"{self.BASE_URL}/program/{program_id}"
        
        # 电台信息
        radio = program.get("radio", {})
        radio_name = radio.get("name", "")
        
        # 描述
        description = program.get("description", "")
        
        # 时长
        duration = program.get("duration", 0) // 1000  # 毫秒转秒
        duration_str = self._format_duration(duration)
        
        # 播放量
        listener_count = program.get("listenerCount", 0)
        
        # 发布时间
        publish_time = None
        if program.get("createTime"):
            try:
                publish_time = datetime.fromtimestamp(program["createTime"] / 1000)
            except:
                pass
        
        # 封面
        image_url = program.get("coverUrl")
        if not image_url:
            image_url = radio.get("picUrl")
        
        content_parts = [
            f"电台: {radio_name}",
            f"时长: {duration_str}",
            f"收听: {listener_count}次",
            "",
            description[:200] if description else ""
        ]
        
        return self.create_content_item(
            title=title,
            url=url,
            content="\n".join(filter(None, content_parts)),
            author=radio_name,
            publish_time=publish_time,
            image_url=image_url,
            keywords=["播客", "电台", radio_name],
            extra={
                "program_id": program_id,
                "radio_id": radio.get("id"),
                "radio_name": radio_name,
                "duration": duration,
                "listener_count": listener_count,
                "is_audio": True,
                "platform": "netease"
            }
        )
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分{seconds % 60}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分"


class ApplePodcastCNCollector(BaseCollector):
    """
    苹果播客(中国区)采集器
    
    特点：
    - iOS 用户高质量播客入口
    - 可直接使用 RSS 订阅
    
    采集方式：RSS Feed
    """
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.RSS, config)
        self.feed_url = config.get("feed_url")
        self.podcast_name = config.get("podcast_name", "播客")
        self.limit = config.get("limit", 10)
        
        if not self.feed_url:
            raise ValueError("苹果播客采集器必须配置 feed_url")
    
    async def collect(self) -> CollectorResult:
        """采集苹果播客"""
        result = CollectorResult()
        
        try:
            import feedparser
            from bs4 import BeautifulSoup
            
            loop = __import__('asyncio').get_event_loop()
            feed = await loop.run_in_executor(None, lambda: feedparser.parse(self.feed_url))
            
            result.total_found = len(feed.entries)
            
            for entry in feed.entries[:self.limit]:
                try:
                    item = self._parse_entry(entry, feed)
                    if self.should_include(item):
                        result.items.append(item)
                    else:
                        result.total_filtered += 1
                except Exception as e:
                    continue
            
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条播客内容"
            
        except Exception as e:
            result.success = False
            result.message = f"苹果播客采集失败: {str(e)}"
        
        return result
    
    def _parse_entry(self, entry: Dict, feed) -> ContentItem:
        """解析 RSS 条目"""
        from bs4 import BeautifulSoup
        
        title = entry.get("title", "无标题")
        url = entry.get("link", "")
        
        # 音频文件
        audio_url = ""
        if "enclosures" in entry and entry["enclosures"]:
            audio_url = entry["enclosures"][0].get("href", "")
        
        # 提取描述
        content = ""
        if "description" in entry:
            content = entry["description"]
        elif "summary" in entry:
            content = entry["summary"]
        elif "content" in entry and entry["content"]:
            content = entry["content"][0].get("value", "")
        
        # 清理 HTML
        if content:
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(strip=True)
        
        # 时长
        duration = entry.get("itunes_duration", "")
        
        # 发布时间
        publish_time = None
        if "published_parsed" in entry:
            try:
                parsed = entry["published_parsed"]
                publish_time = datetime(*parsed[:6])
            except:
                pass
        
        # 播客封面
        image_url = None
        if "image" in entry and entry["image"].get("href"):
            image_url = entry["image"]["href"]
        elif feed.feed.get("image", {}).get("href"):
            image_url = feed.feed["image"]["href"]
        
        # 作者
        author = entry.get("author", "")
        if not author:
            author = feed.feed.get("author", self.podcast_name)
        
        content_parts = [
            f"播客: {self.podcast_name}",
            f"时长: {duration}",
            "",
            content[:300] + "..." if len(content) > 300 else content
        ]
        
        return self.create_content_item(
            title=title,
            url=url or audio_url,
            content="\n".join(filter(None, content_parts)),
            author=author,
            publish_time=publish_time,
            image_url=image_url,
            keywords=["播客", "Podcast", self.podcast_name],
            extra={
                "podcast_name": self.podcast_name,
                "duration": duration,
                "audio_url": audio_url,
                "is_audio": True,
                "platform": "apple_podcasts"
            }
        )
