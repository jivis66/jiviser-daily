"""
金融数据终端采集器
支持 Wind、同花顺等金融数据终端的数据采集

注意：这些平台是专业级金融数据服务，需要付费订阅
本采集器提供基础框架，实际使用需要：
1. 有效的付费账号
2. 相应的 API 权限
3. 合规使用数据
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.collector.base import BaseCollector, CollectorResult
from src.models import ContentItem, SourceType


class WindCollector(BaseCollector):
    """
    Wind 金融终端采集器
    
    特点：
    - 金融从业者标配
    - 专业级金融数据
    - 需要付费订阅
    
    采集方式：Wind API（Python SDK）
    注意：需要安装 WindPy 并登录
    
    使用要求：
    1. 安装 WindPy: pip install WindPy
    2. 有有效的 Wind 账号
    3. 登录 Wind 终端或 API
    """
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.API, config)
        self.data_type = config.get("data_type", "news")  # news, announcement, research
        self.symbols = config.get("symbols", [])  # 股票代码列表
        self.start_date = config.get("start_date")
        self.end_date = config.get("end_date")
        self.limit = config.get("limit", 50)
        
        # Wind API 需要登录
        self.wind_account = config.get("wind_account")
        self.wind_password = config.get("wind_password")
        self.auto_login = config.get("auto_login", False)
        
        self._wind_api = None
    
    async def collect(self) -> CollectorResult:
        """采集 Wind 数据"""
        result = CollectorResult()
        
        try:
            # 检查是否安装了 WindPy
            try:
                from WindPy import w
                self._wind_api = w
            except ImportError:
                result.success = False
                result.message = "未安装 WindPy，请使用 'pip install WindPy' 安装"
                return result
            
            # 登录
            if self.auto_login and self.wind_account and self.wind_password:
                login_result = self._wind_api.start()
                if login_result.ErrorCode != 0:
                    result.success = False
                    result.message = f"Wind 登录失败: {login_result.Data}"
                    return result
            elif not self._wind_api.isconnected():
                result.success = False
                result.message = "Wind 未连接，请先登录 Wind 终端或设置 auto_login"
                return result
            
            # 根据数据类型采集
            if self.data_type == "news":
                items = await self._collect_news()
            elif self.data_type == "announcement":
                items = await self._collect_announcements()
            elif self.data_type == "research":
                items = await self._collect_research()
            else:
                result.success = False
                result.message = f"不支持的数据类型: {self.data_type}"
                return result
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条 Wind 数据"
            
        except Exception as e:
            result.success = False
            result.message = f"Wind 采集失败: {str(e)}"
        
        finally:
            # 如果自动登录，登出
            if self.auto_login and self._wind_api and self._wind_api.isconnected():
                self._wind_api.close()
        
        return result
    
    async def _collect_news(self) -> List[ContentItem]:
        """采集新闻资讯"""
        # 使用 Wind API 获取新闻
        # 示例：获取指定股票的相关新闻
        
        items = []
        
        # 设置日期范围
        end_date = self.end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = self.start_date or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 获取新闻
        # 注意：实际的 Wind API 调用方式可能不同
        for symbol in self.symbols[:5]:  # 限制股票数量
            try:
                # 这里使用示例 API，实际请参考 Wind API 文档
                result = self._wind_api.wsd(
                    symbol,
                    "news",
                    start_date,
                    end_date,
                    f"limit={self.limit}"
                )
                
                if result.ErrorCode == 0 and result.Data:
                    for news_item in result.Data:
                        item = self._parse_wind_news(news_item, symbol)
                        if item:
                            items.append(item)
                            
            except Exception as e:
                print(f"[Wind] 获取 {symbol} 新闻失败: {e}")
                continue
        
        return items
    
    async def _collect_announcements(self) -> List[ContentItem]:
        """采集公告"""
        items = []
        
        end_date = self.end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = self.start_date or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        for symbol in self.symbols[:5]:
            try:
                # 获取公告
                result = self._wind_api.wsd(
                    symbol,
                    "announcement",
                    start_date,
                    end_date,
                    f"limit={self.limit}"
                )
                
                if result.ErrorCode == 0 and result.Data:
                    for ann in result.Data:
                        item = self._parse_wind_announcement(ann, symbol)
                        if item:
                            items.append(item)
                            
            except Exception as e:
                print(f"[Wind] 获取 {symbol} 公告失败: {e}")
                continue
        
        return items
    
    async def _collect_research(self) -> List[ContentItem]:
        """采集研究报告"""
        items = []
        
        # 获取研究报告通常有专门的接口
        # 这里提供框架，实际实现需参考 Wind API 文档
        
        return items
    
    def _parse_wind_news(self, data: Dict, symbol: str) -> Optional[ContentItem]:
        """解析 Wind 新闻数据"""
        title = data.get("title", "无标题")
        content = data.get("content", "")
        publish_time = data.get("publish_time")
        source = data.get("source", "Wind")
        
        return self.create_content_item(
            title=title,
            url=data.get("url", ""),
            content=content[:500] + "..." if len(content) > 500 else content,
            author=source,
            publish_time=publish_time,
            source=f"Wind-{source}",
            keywords=[symbol, "财经", "Wind"],
            extra={
                "symbol": symbol,
                "data_type": "news",
                "platform": "wind"
            }
        )
    
    def _parse_wind_announcement(self, data: Dict, symbol: str) -> Optional[ContentItem]:
        """解析 Wind 公告数据"""
        title = data.get("title", "无标题")
        content = data.get("content", "")
        publish_time = data.get("publish_time")
        ann_type = data.get("type", "公告")
        
        return self.create_content_item(
            title=f"[{ann_type}] {title}",
            url=data.get("url", ""),
            content=content[:500] + "..." if len(content) > 500 else content,
            author=data.get("issuer", symbol),
            publish_time=publish_time,
            source="Wind-公告",
            keywords=[symbol, "公告", ann_type],
            extra={
                "symbol": symbol,
                "ann_type": ann_type,
                "data_type": "announcement",
                "platform": "wind"
            }
        )


class TonghuashunCollector(BaseCollector):
    """
    同花顺采集器
    
    特点：
    - 国内主流金融数据终端
    - 需要付费订阅
    
    采集方式：API 或网页解析
    注意：同花顺提供 iFinD API，需要单独申请
    """
    
    BASE_URL = "https://basic.10jqka.com.cn"
    API_URL = "https://d.10jqka.com.cn"
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, SourceType.API, config)
        self.data_type = config.get("data_type", "news")  # news, notice, report
        self.symbols = config.get("symbols", [])
        self.limit = config.get("limit", 50)
        
        # iFinD API 配置
        self.ifind_username = config.get("ifind_username")
        self.ifind_password = config.get("ifind_password")
        
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://basic.10jqka.com.cn/",
        }
    
    async def collect(self) -> CollectorResult:
        """采集同花顺数据"""
        result = CollectorResult()
        
        try:
            # 优先使用 iFinD API
            if self.ifind_username and self.ifind_password:
                items = await self._collect_via_ifind()
            else:
                # 降级为网页采集
                items = await self._collect_via_web()
            
            for item in items:
                if self.should_include(item):
                    result.items.append(item)
                else:
                    result.total_filtered += 1
            
            result.total_found = len(items)
            result.success = True
            result.message = f"成功采集 {len(result.items)} 条同花顺数据"
            
        except Exception as e:
            result.success = False
            result.message = f"同花顺采集失败: {str(e)}"
        
        return result
    
    async def _collect_via_ifind(self) -> List[ContentItem]:
        """通过 iFinD API 采集"""
        try:
            from iFinDPy import THS_iFinDLogin, THS_iFinDLogout, THS_HistoryNews
        except ImportError:
            print("[Tonghuashun] 未安装 iFinDPy")
            return []
        
        items = []
        
        # 登录
        login_result = THS_iFinDLogin(self.ifind_username, self.ifind_password)
        if login_result != 0:
            print("[Tonghuashun] iFinD 登录失败")
            return []
        
        try:
            for symbol in self.symbols[:5]:
                # 获取历史新闻
                result = THS_HistoryNews(symbol, "", "", "", f"limit={self.limit}")
                # 解析结果...
                
        finally:
            THS_iFinDLogout()
        
        return items
    
    async def _collect_via_web(self) -> List[ContentItem]:
        """通过网页采集"""
        items = []
        
        # 同花顺网页版可以获取一些公开数据
        # 但大部分数据需要登录
        
        for symbol in self.symbols[:3]:
            try:
                # 获取个股新闻
                url = f"{self.BASE_URL}/{symbol}/news.html"
                response = await self.fetch_url(url, headers=self._headers)
                
                # 解析新闻列表
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 这里需要根据实际页面结构解析
                # 示例代码
                news_list = soup.find_all("div", class_="news-item")
                
                for news in news_list[:self.limit]:
                    item = self._parse_web_news(news, symbol)
                    if item:
                        items.append(item)
                        
            except Exception as e:
                print(f"[Tonghuashun] 网页采集 {symbol} 失败: {e}")
                continue
        
        return items
    
    def _parse_web_news(self, element, symbol: str) -> Optional[ContentItem]:
        """解析网页新闻"""
        from bs4 import BeautifulSoup
        
        title_elem = element.find("a", class_="title")
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        url = title_elem.get("href", "")
        if url.startswith("//"):
            url = "https:" + url
        
        time_elem = element.find("span", class_="time")
        publish_time = None
        if time_elem:
            time_str = time_elem.get_text(strip=True)
            try:
                publish_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            except:
                pass
        
        return self.create_content_item(
            title=title,
            url=url,
            content="",
            publish_time=publish_time,
            source="同花顺",
            keywords=[symbol, "财经"],
            extra={
                "symbol": symbol,
                "platform": "tonghuashun"
            }
        )
