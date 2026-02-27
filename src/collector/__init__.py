"""
采集模块 - 负责从各种数据源收集信息

支持的数据源：
- RSS 订阅源
- API 接口
- 网页抓取
- 社交媒体
- 视频平台
- 播客平台
- 在线教育平台

新增：国内外 Top 30 信息渠道采集器
"""
from src.collector.base import BaseCollector, CollectorManager, CollectorResult

# 基础采集器
from src.collector.rss_collector import RSSCollector
from src.collector.api_collector import APICollector, HackerNewsCollector, GitHubTrendingCollector

# 国内平台
from src.collector.bilibili_collector import BilibiliCollector, BilibiliHotCollector
from src.collector.xiaohongshu_collector import XiaohongshuCollector, XiaohongshuSearchCollector

# 国内文字媒体
from src.collector.caixin_collector import CaixinCollector, CaixinPremiumCollector
from src.collector.yicai_collector import YicaiCollector, YicaiVideoCollector
from src.collector.jiemian_collector import JiemianCollector, JiemianProfileCollector
from src.collector.ftchinese_collector import FTChineseCollector, FTChineseEnglishCollector

# 国内播客/音频平台
from src.collector.podcast_collector import (
    XiaoyuzhouCollector,
    XimalayaCollector,
    NeteasePodcastCollector,
    ApplePodcastCNCollector,
)

# 国内视频平台
from src.collector.douyin_collector import DouyinCollector, DouyinKnowledgeCollector
from src.collector.wechat_channels_collector import (
    WechatChannelsCollector,
    WechatChannelsRSSCollector,
)

# 国内社区/数据
from src.collector.zhihu_collector import ZhihuCollector, ZhihuHotCollector
from src.collector.jike_collector import JikeCollector, JikeTopicCollector
from src.collector.financial_data_collector import WindCollector, TonghuashunCollector

# 国际新闻媒体
from src.collector.intl_news_collector import (
    BloombergCollector,
    ReutersCollector,
    EconomistCollector,
    NYTCollector,
)

# 国际播客/视频/教育平台
from src.collector.intl_podcast_collector import (
    SpotifyPodcastCollector,
    YouTubePodcastCollector,
    TEDCollector,
    OnlineCourseCollector,
    NetflixEducationalCollector,
    MasterClassCollector,
)

__all__ = [
    # 基础组件
    "BaseCollector",
    "CollectorManager",
    "CollectorResult",
    
    # 基础采集器
    "RSSCollector",
    "APICollector",
    "HackerNewsCollector",
    "GitHubTrendingCollector",
    
    # 国内视频/社交
    "BilibiliCollector",
    "BilibiliHotCollector",
    "XiaohongshuCollector",
    "XiaohongshuSearchCollector",
    
    # 国内文字媒体
    "CaixinCollector",
    "CaixinPremiumCollector",
    "YicaiCollector",
    "YicaiVideoCollector",
    "JiemianCollector",
    "JiemianProfileCollector",
    "FTChineseCollector",
    "FTChineseEnglishCollector",
    
    # 国内播客/音频
    "XiaoyuzhouCollector",
    "XimalayaCollector",
    "NeteasePodcastCollector",
    "ApplePodcastCNCollector",
    
    # 国内视频平台
    "DouyinCollector",
    "DouyinKnowledgeCollector",
    "WechatChannelsCollector",
    "WechatChannelsRSSCollector",
    
    # 国内社区/数据
    "ZhihuCollector",
    "ZhihuHotCollector",
    "JikeCollector",
    "JikeTopicCollector",
    "WindCollector",
    "TonghuashunCollector",
    
    # 国际新闻媒体
    "BloombergCollector",
    "ReutersCollector",
    "EconomistCollector",
    "NYTCollector",
    
    # 国际播客/视频/教育
    "SpotifyPodcastCollector",
    "YouTubePodcastCollector",
    "TEDCollector",
    "OnlineCourseCollector",
    "NetflixEducationalCollector",
    "MasterClassCollector",
]
