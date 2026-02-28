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
- 需要登录认证的私有渠道（即刻、知乎等）

新增：国内外 Top 30 信息渠道采集器
新增：认证采集器（支持交互式 Cookie 管理）
"""
from src.collector.base import BaseCollector, CollectorManager, CollectorResult

# v2 基类（新版，推荐新采集器使用）
from src.collector.base_v2 import (
    BaseCollectorV2,
    BatchCollector,
    CollectContext,
    SimpleRSSCollector,
    HackerNewsCollectorV2,
)

# 基础采集器
from src.collector.rss_collector import RSSCollector
from src.collector.api_collector import APICollector, HackerNewsCollector, GitHubTrendingCollector

# 国内平台
from src.collector.bilibili_collector import BilibiliCollector, BilibiliHotCollector

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

# 新增：中国科技媒体
from src.collector.china_tech_collector import (
    JuejinCollector,
    OschinaCollector,
    InfoqChinaCollector,
    SegmentFaultCollector,
)

# 新增：中国商业媒体
from src.collector.china_media_collector import (
    HuxiuCollector,
    LeiphoneCollector,
    PingWestCollector,
    GeekParkCollector,
    SinaTechCollector,
    NetEaseTechCollector,
)

# 新增：中国社区
from src.collector.china_community_collector import (
    V2EXCollector,
    XueqiuCollector,
    WallstreetCnCollector,
    ITPubCollector,
    ChinaUnixCollector,
)

# 新增：优质生活方式/工具类媒体
from src.collector.quality_life_collector import (
    SspaiCollector,
    IfanrCollector,
    DgtleCollector,
    AppinnCollector,
    LiqiCollector,
    UisdcCollector,
    ToodaylabCollector,
)

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

# 带认证的采集器
from src.collector.base_auth_collector import (
    AuthenticatedCollector,
    AuthError,
    AuthExpiredError,
    AuthRequiredError,
    JikeAuthenticatedCollector,
    ZhihuAuthenticatedCollector,
    BilibiliAuthenticatedCollector,
)

__all__ = [
    # 基础组件
    "BaseCollector",
    "CollectorManager",
    "CollectorResult",

    # v2 基类
    "BaseCollectorV2",
    "BatchCollector",
    "CollectContext",
    "SimpleRSSCollector",
    "HackerNewsCollectorV2",

    # 基础采集器
    "RSSCollector",
    "APICollector",
    "HackerNewsCollector",
    "GitHubTrendingCollector",
    
    # 国内视频/社交
    "BilibiliCollector",
    "BilibiliHotCollector",
    
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

    # 新增：中国科技媒体
    "JuejinCollector",
    "OschinaCollector",
    "InfoqChinaCollector",
    "SegmentFaultCollector",

    # 新增：中国商业媒体
    "HuxiuCollector",
    "LeiphoneCollector",
    "PingWestCollector",
    "GeekParkCollector",
    "SinaTechCollector",
    "NetEaseTechCollector",

    # 新增：中国社区
    "V2EXCollector",
    "XueqiuCollector",
    "WallstreetCnCollector",
    "ITPubCollector",
    "ChinaUnixCollector",

    # 新增：优质生活方式/工具类媒体
    "SspaiCollector",
    "IfanrCollector",
    "DgtleCollector",
    "AppinnCollector",
    "LiqiCollector",
    "UisdcCollector",
    "ToodaylabCollector",

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
    
    # 带认证的采集器
    "AuthenticatedCollector",
    "AuthError",
    "AuthExpiredError",
    "AuthRequiredError",
    "JikeAuthenticatedCollector",
    "ZhihuAuthenticatedCollector",
    "BilibiliAuthenticatedCollector",
]
