# 完美个性化日报信息收集 Agent 能力图谱

> 构建一个智能、高效、个性化的日报信息收集 Agent 所需的核心能力集合

---

## 📋 目录

1. [信息收集能力](#1-信息收集能力)
2. [个性化能力](#2-个性化能力)
3. [内容理解与处理](#3-内容理解与处理)
4. [信息筛选与排序](#4-信息筛选与排序)
5. [输出与呈现](#5-输出与呈现)
6. [交互与反馈](#6-交互与反馈)
7. [系统与工程能力](#7-系统与工程能力)
8. [智能化能力](#8-智能化能力)
9. [启动设置与交互式配置](#9-启动设置与交互式配置)
10. [OpenClaw Skill 规范](#10-openclaw-skill-规范)

---

## 1. 信息收集能力

### 1.1 多源信息获取

| 能力项 | 说明 | 示例来源 |
|--------|------|----------|
| **新闻聚合** | 抓取主流新闻媒体、垂直领域媒体 | RSS、News API、爬虫 |
| **社交媒体监听** | 追踪社交媒体热点、行业动态 | Twitter/X、微博、LinkedIn |
| **学术/技术追踪** | 监控论文、技术博客、开源项目 | arXiv、GitHub、Medium |
| **内部系统集成** | 连接企业内部信息源 | 邮件、Slack、飞书、钉钉 |
| **播客/视频转录** | 处理多媒体内容 | YouTube、播客平台 |

### 1.1.1 推荐信息源清单

#### 🇨🇳 国内 Top 15 信息渠道

**📰 文字/图文媒体**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **财新网** | 财经新闻 | 调查 journalism 标杆，付费内容质量极高 | RSS + 网页解析 | ⭐⭐⭐ |
| **第一财经** | 财经媒体 | 财经视频+图文深度结合 | RSS + API | ⭐⭐ |
| **界面新闻** | 商业媒体 | 商业人物报道出色 | RSS + 网页解析 | ⭐⭐ |
| **FT中文网** | 国际财经 | 国际视野+本土洞察 | RSS | ⭐ |

**🎧 音频/播客平台**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **小宇宙** | 播客平台 | 中文播客绝对头部，87.1%用户首选 | API + 网页解析 | ⭐⭐⭐ |
| **喜马拉雅** | 综合音频 | 综合音频平台，播客+有声书+知识课程 | RSS + API | ⭐⭐ |
| **网易云音乐** | 音乐播客 | 播客板块增长迅速，音乐+音频融合 | API | ⭐⭐ |
| **苹果播客(中国区)** | 播客平台 | iOS用户高质量播客入口 | RSS Feed | ⭐ |

**📺 视频平台**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **B站 (哔哩哔哩)** | 视频社区 | 知识区崛起，深度长视频+视频播客新赛道 | 官方 API | ⭐⭐ |
| **抖音** | 短视频 | 泛知识内容占比20%，1.5亿知识创作者 | 网页版 + API | ⭐⭐⭐ |
| **视频号** | 短视频 | 微信生态，社交推荐+直播知识内容 | 反爬严格，需特殊处理 | ⭐⭐⭐⭐ |
| **小红书** | 生活方式 | 生活方式、消费决策、职场经验一手信息 | 网页解析 | ⭐⭐⭐ |

**👥 社区/数据**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **知乎** | 问答社区 | 专业问答社区，深度长文 | 官方 API | ⭐⭐ |
| **即刻** | 兴趣社区 | 兴趣圈子，信息筛选效率高 | API + 网页解析 | ⭐⭐⭐ |
| **Wind/同花顺** | 金融数据 | 金融数据终端（专业级） | 付费 API | ⭐⭐ |

#### 🌍 国际 Top 15 信息渠道

**📰 文字媒体**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **Bloomberg** | 财经新闻 | 金融从业者标配 | RSS + API (付费) | ⭐⭐ |
| **Reuters** | 通讯社 | 全球新闻网络最广 | RSS + API | ⭐ |
| **The Economist** | 周刊杂志 | 深度分析+独特观点 | RSS | ⭐ |
| **The New York Times** | 综合媒体 | 调查报道标杆 | API (需Key) | ⭐⭐ |

**🎧 音频/播客平台**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **Spotify** | 播客平台 | 全球最大播客平台，市场份额34.2% | RSS 聚合 | ⭐ |
| **Apple Podcasts** | 播客平台 | iOS生态播客入口，15%美国用户首选 | RSS Feed | ⭐ |
| **YouTube** | 视频播客 | 视频播客第一平台，月播放超4亿小时 | RSS + API | ⭐⭐ |
| **Audible** | 有声书 | 有声书+音频内容，Amazon生态 | 需订阅 | ⭐⭐⭐ |

**📺 视频/流媒体平台**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **YouTube** | 视频平台 | 全球最大视频平台，知识类内容生态成熟 | API (需Key) | ⭐⭐ |
| **Netflix** | 流媒体 | 纪录片教育资源，提供教育版内容 | 受限 | ⭐⭐⭐ |
| **TED** | 演讲视频 | 思想领袖演讲，18分钟深度分享 | RSS + API | ⭐ |
| **MasterClass** | 大师课 | 名人大师课，电影级制作 | 需订阅 | ⭐⭐⭐ |

**🎓 在线教育/知识平台**

| 渠道名称 | 类型 | 特点 | 采集方式 | 难度 |
|----------|------|------|----------|------|
| **Coursera** | MOOC平台 | 名校MOOC，3000+课程，学位认证 | API (有限) | ⭐⭐ |
| **Udemy** | 技能课程 | 实用技能课程，性价比高 | API (需Key) | ⭐⭐ |
| **Skillshare** | 创意教育 | 创意领域，社区互动强 | 需订阅 | ⭐⭐⭐ |

---

**采集策略建议：**

```yaml
# 国内渠道优先级
china_sources:
  high_priority:  # 每日必采
    - 财新网 (付费内容质量高)
    - 第一财经 (实时财经)
    - B站知识区 (深度内容)
    - 知乎 (专业讨论)
  
  medium_priority:  # 每日采集
    - 界面新闻
    - FT中文网
    - 小红书
    - 即刻
  
  low_priority:  # 按需采集
    - 抖音 (泛知识)
    - 视频号
    - 音频平台 (转文字后处理)

# 国际渠道优先级
international_sources:
  high_priority:
    - Bloomberg
    - Reuters
    - The Economist
  
  medium_priority:
    - NYT
    - YouTube 知识频道
    - TED
  
  low_priority:
    - 播客平台 (需转录)
    - 教育平台 (课程更新慢)
```

### 1.2 实时与批量采集

- **实时流式采集**：WebSocket、SSE、Webhook 接收实时推送
- **定时批量采集**：Cron 任务、调度器管理采集任务
- **增量更新机制**：基于时间戳、ETag、哈希的去重采集
- **反爬对抗**：代理池、请求频率控制、User-Agent 轮换、验证码处理

### 1.3 登录鉴权信息渠道采集

针对需要登录认证的私有信息渠道（如即刻、小红书、知乎、B站关注流等），提供完整的认证管理能力。

#### 1.3.1 认证方式支持

| 认证方式 | 适用平台 | 技术实现 | 安全性 |
|----------|----------|----------|--------|
| **Cookie 认证** | 网页版平台 | 浏览器 Cookie 复制 | ⭐⭐⭐ |
| **Token 认证** | 移动端 API | JWT/Access Token | ⭐⭐⭐⭐ |
| **OAuth 2.0** | 开放平台 | 标准 OAuth 流程 | ⭐⭐⭐⭐⭐ |
| **扫码登录** | 微信生态 | 二维码扫描授权 | ⭐⭐⭐⭐⭐ |
| **短信验证码** | 手机号登录 | 交互式验证码输入 | ⭐⭐⭐⭐ |

#### 1.3.2 交互式 Cookie 获取与更新

**CLI 交互流程：**

```bash
# 查看已配置的认证渠道
$ python -m src.cli auth list
┌─────────────┬──────────┬─────────────────────┬────────┐
│ 渠道名称    │ 认证方式 │ 过期时间            │ 状态   │
├─────────────┼──────────┼─────────────────────┼────────┤
│ 即刻        │ Cookie   │ 2026-03-05 14:30:00 │ ✅ 有效 │
│ 小红书      │ Cookie   │ 2026-02-28 09:15:00 │ ⚠️ 即将过期 │
│ 知乎        │ Token    │ 2026-03-10 20:00:00 │ ✅ 有效 │
└─────────────┴──────────┴─────────────────────┴────────┘

# 添加新的认证渠道（交互式）
$ python -m src.cli auth add jike
🌐 正在为 [即刻] 配置认证信息
📖 请按以下步骤获取 Cookie：
   1. 使用 Chrome/Edge 浏览器登录即刻网页版 (https://web.okjike.com)
   2. 按 F12 打开开发者工具，切换到 Network 标签
   3. 刷新页面，找到任意 API 请求（如 /api/users/me）
   4. 右键点击请求 → Copy → Copy as cURL
   5. 粘贴 cURL 命令或仅提取 Cookie 字段

📝 请输入 Cookie 或 cURL 命令: 
> curl 'https://web.okjike.com/api/users/me' -H 'cookie: your-cookie-here...'

✅ Cookie 解析成功！
   用户: @username
   过期: 30 天后
   是否保存? [Y/n]: Y

✅ [即刻] 认证配置已保存

# 测试认证是否有效
$ python -m src.cli auth test jike
🧪 测试 [即刻] 认证状态...
✅ 认证有效！用户信息: @username

# 更新认证信息
$ python -m src.cli auth update jike
📖 当前认证将于 2 天后过期，请更新 Cookie...
[交互式更新流程]

# 删除认证配置
$ python -m src.cli auth remove jike
⚠️ 确定要删除 [即刻] 的认证配置吗? [y/N]: y
✅ 已删除
```

#### 1.3.3 Cookie 安全管理

**存储机制：**
```python
# 加密存储在 SQLite 数据库中
{
    "source_name": "jike",
    "auth_type": "cookie",
    "credentials": "加密存储的 Cookie 字符串",
    "headers": {
        "User-Agent": "...",
        "Referer": "..."
    },
    "expires_at": "2026-03-05T14:30:00",
    "created_at": "2026-02-03T14:30:00",
    "last_verified": "2026-02-05T09:00:00",
    "metadata": {
        "username": "@username",
        "user_id": "xxx"
    }
}
```

**安全特性：**
- **加密存储**：使用 Fernet 对称加密保护敏感凭证
- **自动过期提醒**：过期前 3 天、1 天、当天提醒
- **定期验证**：采集前自动验证认证有效性
- **自动刷新**：支持 Token 自动续期（如 Refresh Token 机制）

#### 1.3.4 需要登录的渠道列表

**国内平台：**

| 渠道 | 认证方式 | 内容类型 | 更新频率 |
|------|----------|----------|----------|
| **即刻** | Cookie | 圈子动态、精选 | 实时 |
| **小红书** | Cookie | 关注流、搜索 | 实时 |
| **知乎** | Cookie/Token | 关注、推荐 | 实时 |
| **B站关注** | Cookie | 关注UP主动态 | 实时 |
| **微博** | Cookie | 关注流、热搜 | 实时 |
| **抖音** | Cookie | 关注、推荐 | 实时 |
| **微信读书** | Cookie | 阅读动态、书单 | 每日 |
| **豆瓣** | Cookie | 书影音动态 | 每日 |

**国际平台：**

| 渠道 | 认证方式 | 内容类型 | 更新频率 |
|------|----------|----------|----------|
| **Twitter/X** | OAuth/Token | 关注时间线 | 实时 |
| **LinkedIn** | Cookie | 行业动态 | 每日 |
| **Reddit** | OAuth | 订阅 Subreddit | 实时 |
| **YouTube** | OAuth | 订阅频道 | 实时 |
| **GitHub** | Token | 关注项目动态 | 实时 |

#### 1.3.5 认证失效处理策略

```yaml
auth_failure_handling:
  # 检测方式
  detection:
    - http_status: 401  # Unauthorized
    - http_status: 403  # Forbidden
    - response_keyword: "登录已过期"
    - response_keyword: "请重新登录"
  
  # 处理策略
  strategies:
    # 策略1: 标记失效并通知
    - action: mark_invalid
      notify: true
      continue_other_collectors: true
    
    # 策略2: 尝试使用缓存数据
    - action: use_cached
      max_age: "24h"
    
    # 策略3: 降级到公开数据
    - action: fallback
      to: "public_feed"
```

### 1.4 数据解析与清洗

- **结构化数据**：JSON、XML、YAML 解析
- **非结构化数据**：HTML 解析、PDF 提取、图片 OCR
- **数据清洗**：去噪、格式标准化、编码统一
- **元数据提取**：发布时间、作者、来源、标签

---

## 2. 个性化能力

### 2.1 用户画像构建

```
用户画像维度：
├── 基础属性：行业、职位、专业领域
├── 兴趣标签：技术栈、关注话题、偏好媒体
├── 行为模式：阅读时段、内容偏好、互动习惯
├── 社交关系：关注的人、加入的社群
└── 显式配置：黑名单、白名单、优先级设置
```

### 2.2 兴趣偏好学习

- **显式反馈收集**：点赞、收藏、分享、标记无用
- **隐式行为分析**：阅读时长、滚动深度、点击率
- **协同过滤**：相似用户兴趣推荐
- **内容向量表示**：将内容嵌入向量空间进行相似度计算

### 2.3 自适应调整

- **动态权重调整**：根据反馈实时调整内容权重
- **冷启动策略**：新用户的默认推荐策略
- **兴趣漂移检测**：识别用户兴趣变化并调整推荐
- **多维度平衡**：热门 vs 长尾、时效 vs 深度、广度 vs 精准

---

## 3. 内容理解与处理

### 3.1 自然语言理解

| 技术能力 | 应用场景 |
|----------|----------|
| **实体识别 (NER)** | 提取人名、公司、技术术语、地点 |
| **关键词提取** | TF-IDF、TextRank、LLM 提取关键词 |
| **主题分类** | 将内容归类到预设或自动发现的主题 |
| **语义理解** | 理解内容深层含义，而非仅关键词匹配 |
| **多语言处理** | 跨语言内容理解与翻译 |

### 3.2 内容摘要生成

- **抽取式摘要**：提取关键句子组合成摘要
- **生成式摘要**：使用 LLM 生成高质量摘要
- **多粒度摘要**：一句话摘要、段落摘要、全文摘要
- **个性化摘要**：根据用户关注点生成针对性摘要

### 3.3 信息结构化

```json
{
  "title": "文章标题",
  "source": "信息来源",
  "publish_time": "发布时间",
  "author": "作者",
  "summary": "内容摘要",
  "key_points": ["要点1", "要点2", "要点3"],
  "entities": ["相关实体"],
  "sentiment": "情感倾向",
  "topics": ["主题标签"],
  "read_time": "预估阅读时长",
  "url": "原文链接"
}
```

---

## 4. 信息筛选与排序

### 4.1 智能去重

- **精确去重**：URL、哈希值比对
- **语义去重**：相似内容检测（余弦相似度、SimHash）
- **事件聚类**：同一事件的多报道聚合
- **去重策略**：保留最权威来源或最完整版本

### 4.2 重要性评估

| 评估维度 | 指标 |
|----------|------|
| **来源权威性** | 域名权重、历史质量评分 |
| **传播热度** | 社交媒体分享数、评论数 |
| **时效性** | 内容新鲜度、事件紧迫性 |
| **用户相关性** | 与用户画像匹配度 |
| **内容质量** | 原创性、深度、信息量 |

### 4.3 智能排序

- **个性化排序**：基于用户偏好的综合评分排序
- **时间线排序**：按时间顺序展示
- **热度排序**：按当前热度排序
- **混合排序**：综合多种因素的平衡排序

---

## 5. 输出与呈现

### 5.1 多格式输出

| 输出格式 | 适用场景 |
|----------|----------|
| **Markdown** | 本地阅读、知识库归档 |
| **PDF** | 正式报告、打印存档 |
| **HTML/网页** | Web 浏览、交互展示 |
| **邮件** | 定时推送、移动阅读 |
| **API/JSON** | 系统集成、第三方调用 |
| **即时消息** | 微信、Slack、Discord 推送 |

### 5.2 可视化展示

- **信息图谱**：展示内容间的关联关系
- **时间轴视图**：按时间线组织事件
- **热力图**：展示阅读时段、主题分布
- **词云/标签云**：直观展示当日热点

### 5.3 多终端适配

- **桌面端**：浏览器、桌面应用
- **移动端**：手机 App、小程序、响应式网页
- **阅读器适配**：Kindle、Pocket、Readwise
- **语音输出**：TTS 语音播报支持

### 5.4 推送策略

- **定时推送**：每日固定时间发送日报
- **实时推送**：重要突发新闻即时通知
- **智能提醒**：基于用户习惯的推送时机
- **摘要优先**：推送精简版，详情点击查看

### 5.5 Chat 渠道适配规范

针对 iMessage、Telegram、WhatsApp 等即时通讯平台的输出优化规范。

#### 5.5.1 平台特性对比

| 特性 | iMessage | Telegram | WhatsApp |
|------|----------|----------|----------|
| **单条长度限制** | 约 2000 字符（自动截断） | 4096 字符 | 65536 字符 |
| **Markdown 支持** | 有限（*粗体*、_斜体_） | 完整（v2） | 仅 *粗体*、_斜体_、~删除线~ |
| **链接预览** | 自动生成 | 自动生成 | 自动生成 |
| **按钮/交互** | 不支持 | 内联键盘按钮 | 交互式按钮 |
| **图片发送** | 支持 | 支持（文件可传送） | 支持 |
| **话题分组** | 不支持 | 话题组 | 社区话题 |

#### 5.5.2 内容格式规范

**通用原则：**
- 首条消息放标题和概述
- 单条消息控制在 1000 字符以内（保证可读性）
- 使用 emoji 作为视觉分隔符
- 重要内容前置

**iMessage 适配：**
```
📰 今日AI日报 │ 12月15日
━━━━━━━━━━━━━━

🔥 头条：OpenAI 发布 GPT-5 预览
• 多模态能力大幅提升
• 代码生成准确率提升40%
• 详情：https://example.com/1

📱 共5条精选，回复「查看更多」获取完整日报
```

**Telegram 适配：**
```markdown
📰 *今日 AI 日报* │ 12月15日

🔥 *头条：OpenAI 发布 GPT-5 预览*
• 多模态能力大幅提升
• 代码生成准确率提升 40%

[📖 阅读全文](https://example.com/1)

━━━━━━━━━━━━━━
📊 今日概览：5 条精选 · 3 个领域

[⬅️ 上一页] [➡️ 下一页] [🔖 收藏]
```

**WhatsApp 适配：**
```
📰 *今日AI日报* _12月15日_

*🔥 头条：OpenAI发布GPT-5预览*
• 多模态能力大幅提升
• 代码生成准确率提升40%

回复数字查看详情：
1️⃣ GPT-5发布详情
2️⃣ 更多头条新闻
3️⃣ 获取完整日报
```

#### 5.5.3 分页与导航策略

**超长内容处理：**
```yaml
分页策略:
  每页条目数:
    iMessage: 3-5 条（考虑屏幕高度）
    Telegram: 5-8 条（支持长消息）
    WhatsApp: 3-5 条（简洁优先）
  
  导航方式:
    iMessage: 
      - 文字指令："下一页"、"详细"
      - 快捷回复建议
    Telegram:
      - 内联按钮：[⬅️] [➡️] [📑 目录]
      - 跳转按钮直接定位
    WhatsApp:
      - 交互式按钮
      - 列表菜单（最多10项）
      - 数字回复导航
```

**示例导航结构：**
```
【Telegram 内联键盘】
[🔥 头条] [💻 技术] [📊 商业]
[⬅️ 上一页] [📑 1/5] [➡️ 下一页]

【WhatsApp 列表菜单】
请选择查看内容：
1️⃣ 🔥 今日头条 (3)
2️⃣ 💻 技术动态 (5)
3️⃣ 📊 商业资讯 (2)
4️⃣ 🎯 深度阅读 (1)
5️⃣ 📑 获取完整日报
```

#### 5.5.4 多媒体内容适配

| 媒体类型 | iMessage | Telegram | WhatsApp |
|----------|----------|----------|----------|
| **图片** | 直接发送，自动适配 | 直接发送，可发送原图 | 压缩后发送 |
| **链接预览** | 系统生成，无法控制 | 可禁用预览，自定义按钮 | 系统生成 |
| **文件** | 支持，但有大小限制 | 支持大文件（2GB） | 支持（100MB） |
| **视频** | 支持 | 支持 | 支持 |

**图片消息优化：**
- 配图尺寸：1200x630px（1.91:1 比例，适合预览）
- 文件大小：压缩至 500KB 以内
- 添加文字说明作为独立消息

#### 5.5.5 个性化呈现策略

**阅读时间适配：**
```yaml
早晨推送 (8:00):
  内容: 一句话摘要 + 3条要点
  交互: 「详细」「稍后阅读」

午休时间 (12:00):
  内容: 完整摘要（分2-3条消息）
  交互: 分类导航按钮

晚间推送 (20:00):
  内容: 深度长文（分页发送）
  交互: 完整目录导航
```

**用户偏好记忆：**
- 记录用户偏好的摘要长度
- 记住上次阅读位置
- 收藏内容快速召回

#### 5.5.6 平台专属特性利用

**Telegram 专属：**
- **话题组 (Topics)**：按日期或主题归档日报
- **定时消息 (Schedule)**：预设发送时间
- **静音发送 (Silent)**：免打扰推送
- **消息固定 (Pin)**：置顶重要日报

**WhatsApp 专属：**
- **状态更新 (Status)**：简报形式的24小时状态
- **社区 (Community)**：多分组管理不同主题
- **反应表情 (Reactions)**：快速反馈内容质量

**iMessage 专属：**
- **Tapback 反应**：快速点赞/标记
- **富链接预览**：优化链接卡片展示
- **拟我表情**：个性化互动

#### 5.5.7 错误处理与降级策略

```yaml
发送失败处理:
  长度超限:
    - 自动分段发送
    - 关键内容优先保留
    - 添加"（续）"标记
  
  格式不支持:
    - Markdown 降级为纯文本
    - 按钮降级为数字指令
    - 保留核心内容可读性
  
  用户未响应:
    - 24小时后发送提醒
    - 提供「跳过本期」选项
    - 记录为下次优化依据
```

---

## 6. 交互与反馈

### 6.1 用户反馈收集

- **显式反馈**：👍/👎、星标评分、评论
- **隐式反馈**：阅读行为追踪
- **反馈归因**：关联反馈到具体算法模块

### 6.2 交互式定制

```
定制维度：
├── 内容源管理：添加/删除信息源
├── 主题订阅：关注/取消主题
├── 关键词过滤：包含/排除特定关键词
├── 推送设置：时间、频率、渠道
├── 摘要长度：简短/适中/详细
└── 呈现样式：布局、配色、字体
```

### 6.3 用户设置中心

#### 6.3.1 内容要求配置

用户可自定义日报的结构、来源和组织形式。

**分栏配置：**
```yaml
columns:
  - id: "headlines"
    name: "🔥 今日头条"
    enabled: true
    max_items: 5
    order: 1
    
  - id: "tech"
    name: "💻 技术前沿"
    enabled: true
    max_items: 8
    order: 2
    
  - id: "business"
    name: "📈 商业动态"
    enabled: true
    max_items: 5
    order: 3
    
  - id: "deep_dive"
    name: "📚 深度阅读"
    enabled: false        # 可选分栏
    max_items: 3
    order: 4
    schedule: "weekly"   # 特定频率显示
```

**分栏数据源配置：**
```yaml
column_sources:
  headlines:
    sources:
      - type: "rss"
        url: "https://techcrunch.com/feed/"
        weight: 1.0
        filter:
          keywords: ["AI", "人工智能", "大模型"]
          exclude: ["广告", "推广"]
      
      - type: "api"
        provider: "newsapi"
        category: "technology"
        weight: 0.8
      
      - type: "twitter"
        accounts: ["@OpenAI", "@DeepMind"]
        weight: 0.6
        filter:
          min_likes: 100
    
    organization:
      sort_by: "relevance"    # relevance | time | popularity
      dedup_strategy: "semantic"  # exact | semantic | none
      summarize: "3_points"   # none | 1_sentence | 3_points | paragraph
      highlight_key_info: true
  
  tech:
    sources:
      - type: "github"
        repos: ["trending"]
        weight: 1.0
      
      - type: "arxiv"
        categories: ["cs.AI", "cs.CL"]
        weight: 0.9
      
      - type: "hackernews"
        min_score: 100
        weight: 0.8
    
    organization:
      sort_by: "time"
      group_by: "topic"       # topic | source | none
      dedup_strategy: "exact"
      summarize: "paragraph"
```

**内容获取与组织形式：**

| 组织维度 | 选项 | 说明 |
|----------|------|------|
| **排序方式** | relevance / time / popularity | 按相关性、时间或热度排序 |
| **去重策略** | exact / semantic / none | 精确去重、语义去重或不去重 |
| **分组方式** | topic / source / none | 按主题、来源分组或平铺 |
| **摘要形式** | none / 1_sentence / 3_points / paragraph | 不摘要、一句话、三点、段落 |
| **筛选条件** | keywords / time_range / min_score | 关键词、时间范围、最低分数 |
| **数量限制** | 1-20 条 | 每个分栏的最大条目数 |

**智能组合规则：**
```yaml
composition_rules:
  # 内容平衡：避免单一来源占比过高
  source_diversity:
    max_ratio_per_source: 0.4    # 单个来源不超过40%
    min_source_count: 3          # 至少来自3个不同来源
  
  # 时间分布：优先最新内容，但保留重要旧闻
  time_distribution:
    recency_weight: 0.7
    importance_weight: 0.3
    max_age_hours: 48
  
  # 主题覆盖：确保主题多样性
  topic_coverage:
    min_topics: 3
    avoid_topic_overlap: true
```

#### 6.3.2 非公开渠道鉴权设置

用于配置需要身份验证的私有信息源。

**鉴权配置结构：**
```yaml
authenticated_sources:
  # Slack 工作区
  - type: "slack"
    name: "公司技术频道"
    enabled: true
    auth:
      method: "oauth2"
      credentials:
        token: "${SLACK_BOT_TOKEN}"    # 环境变量引用
        workspace: "mycompany"
    scopes:
      - "channels:read"
      - "channels:history"
    sources:
      - channel: "#tech-news"
        weight: 1.0
      - channel: "#announcements"
        weight: 0.8
    filters:
      exclude_bots: true
      min_reactions: 3
  
  # Discord 服务器
  - type: "discord"
    name: "开源社区"
    enabled: true
    auth:
      method: "bot_token"
      credentials:
        token: "${DISCORD_BOT_TOKEN}"
    sources:
      - guild: "OpenSourceCommunity"
        channels: ["#general", "#announcements"]
    filters:
      pinned_only: false
      include_attachments: true
  
  # 企业微信
  - type: "wecom"
    name: "企业内部"
    enabled: true
    auth:
      method: "corp_secret"
      credentials:
        corp_id: "${WECOM_CORP_ID}"
        corp_secret: "${WECOM_SECRET}"
        agent_id: "${WECOM_AGENT_ID}"
    sources:
      - chat_type: "group"
        chat_ids: ["tech_group_001"]
  
  # 飞书
  - type: "lark"
    name: "团队知识库"
    enabled: true
    auth:
      method: "app_credentials"
      credentials:
        app_id: "${LARK_APP_ID}"
        app_secret: "${LARK_APP_SECRET}"
    sources:
      - type: "wiki"
        space_id: "tech_docs"
      - type: "chat"
        chat_ids: ["oc_xxx"]
  
  # Notion 数据库
  - type: "notion"
    name: "产品知识库"
    enabled: true
    auth:
      method: "integration_token"
      credentials:
        token: "${NOTION_INTEGRATION_TOKEN}"
    sources:
      - database_id: "abc123"
        filter:
          property: "Status"
          equals: "Published"
  
  # 私有 RSS（需认证）
  - type: "rss_auth"
    name: "付费资讯"
    enabled: true
    auth:
      method: "basic_auth"
      credentials:
        username: "${PAID_NEWS_USER}"
        password: "${PAID_NEWS_PASS}"
    sources:
      - url: "https://paid-news.com/feed"
```

**部署场景与配置方式：**

本系统支持两种部署模式，鉴权配置需根据部署方式调整：

| 部署方式 | 适用场景 | 配置方式 |
|----------|----------|----------|
| **独立部署** | 个人服务器一键部署 | `.env` 文件 + 环境变量 |
| **OpenClaw Skill** | 集成到 OpenClaw 生态 | Skill 配置文件 + 环境变量注入 |

#### 独立部署配置（Docker 方式）

**1. 环境变量配置（.env 文件）**

```bash
# .env 文件示例
# 复制 .env.example 为 .env 并填写实际值

# ===== Slack 配置 =====
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_WORKSPACE=mycompany

# ===== Discord 配置 =====
DISCORD_BOT_TOKEN=your-bot-token

# ===== 企业微信配置 =====
WECOM_CORP_ID=wwxxxxxxxxxxxxxxxx
WECOM_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WECOM_AGENT_ID=1000002

# ===== 飞书配置 =====
LARK_APP_ID=cli_xxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ===== Notion 配置 =====
NOTION_INTEGRATION_TOKEN=secret_xxxxxxxxxx

# ===== 私有 RSS =====
PAID_NEWS_USER=your-username
PAID_NEWS_PASS=your-password
```

**2. Docker 部署命令**

```bash
# 1. 克隆仓库
git clone https://github.com/user/daily-agent.git
cd daily-agent

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件填入你的 Token

# 3. 启动服务
docker-compose up -d
```

**3. Docker Compose 配置**

```yaml
version: '3.8'
services:
  daily-agent:
    image: daily-agent:latest
    container_name: daily-agent
    env_file:
      - .env
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    restart: unless-stopped
    
  # 可选：配合 Redis 缓存
  redis:
    image: redis:alpine
    container_name: daily-redis
    restart: unless-stopped
```

#### OpenClaw Skill 集成配置

当作为 OpenClaw Skill 集成时，配置通过 Skill 的 `config.yaml` 声明，实际凭证由 OpenClaw 运行时注入。

**Skill 配置文件（config.yaml）：**

```yaml
skill:
  name: daily-agent
  version: "1.0.0"
  
  # 声明需要的环境变量
  required_env:
    - SLACK_BOT_TOKEN
    - DISCORD_BOT_TOKEN
    - WECOM_CORP_ID
    - WECOM_SECRET
    # ... 其他所需变量
  
  # 可选环境变量（有默认值）
  optional_env:
    DAILY_PUSH_TIME: "09:00"
    MAX_ITEMS_PER_COLUMN: "10"
    LOG_LEVEL: "info"

  # 配置结构定义（用于 OpenClaw UI 生成配置表单）
  config_schema:
    columns:
      type: array
      description: "日报分栏配置"
      # ... 详见 6.3.1 内容要求配置
    
    authenticated_sources:
      type: array
      description: "鉴权数据源"
      items:
        - type: object
          properties:
            type: { enum: [slack, discord, wecom, lark, notion] }
            name: { type: string }
            enabled: { type: boolean }
            # 凭证字段通过 env 映射，不在此处硬编码
```

**OpenClaw 集成时的凭证注入：**

```yaml
# openclaw.yaml（OpenClaw 主配置）
skills:
  daily-agent:
    enabled: true
    env:
      # 方式1：直接内联（开发测试用，生产不推荐）
      SLACK_BOT_TOKEN: "${VAULT:slack_token}"
      
      # 方式2：引用 OpenClaw 密钥管理
      DISCORD_BOT_TOKEN: "${secrets.discord_token}"
      
      # 方式3：从 .env 文件加载
      env_file: "/path/to/daily-agent.env"
```

#### 凭证安全规范

由于部署场景限制，安全方案简化为：

| 安全措施 | 实现方式 | 说明 |
|----------|----------|------|
| **存储** | 环境变量 | Token 仅保存在服务器环境变量或 `.env` 文件 |
| **传输** | HTTPS/TLS | 所有 API 调用强制 HTTPS |
| **日志脱敏** | 自动过滤 | 日志中自动隐藏 Token 等敏感信息 |
| **权限最小化** | 按需申请 | 各平台 Token 仅申请必要权限 |
| **文件权限** | 600 | `.env` 文件权限设为仅所有者可读写 |

**`.env` 文件安全设置：**

```bash
# 创建时设置权限
chmod 600 .env

# .gitignore 中排除
echo ".env" >> .gitignore
echo "*.env" >> .gitignore
```

**日志脱敏示例：**

```python
# 配置日志时自动脱敏敏感字段
SENSITIVE_FIELDS = ['token', 'secret', 'password', 'key']

# 脱敏后日志示例
# 原始: "Request to Slack API with token: xoxb-1234-5678"
# 脱敏: "Request to Slack API with token: xoxb-****-****"
```

#### 配置验证与启动检查

**启动时自动检查：**

```bash
$ docker-compose up

[INFO] Daily Agent v1.0.0 starting...
[INFO] Loading configuration from environment variables

[CHECK] Slack Bot Token: ✓ Valid
[CHECK] Discord Bot Token: ⚠ Not configured (skipped)
[CHECK] WeCom Corp ID: ✓ Valid
[CHECK] WeCom Secret: ✓ Valid
[CHECK] Lark App ID: ✓ Valid
[CHECK] Notion Token: ✗ Invalid or expired

[WARN] Notion source disabled due to auth failure
[INFO] Successfully loaded 4/5 authenticated sources
[INFO] Server started on port 8080
```

**手动验证命令：**

```bash
# 验证所有配置
docker exec daily-agent python -m cli verify-config

# 测试特定源连接
docker exec daily-agent python -m cli test-source slack
```

#### 配置热更新（无需重启）

对于非凭证类配置（如分栏设置、过滤规则），支持热更新：

```bash
# 修改 config/columns.yaml 后触发热更新
curl -X POST http://localhost:8080/api/v1/reload

# 或通过 CLI
docker exec daily-agent python -m cli reload
```

**热更新范围：**
- ✅ 分栏配置（columns）
- ✅ 过滤规则（filters）
- ✅ 推送设置（schedule）
- ❌ 环境变量（需重启容器）
- ❌ 鉴权凭证（需重启容器）

### 6.4 智能问答

- **内容问答**：基于当日内容回答用户问题
- **历史检索**：搜索过往日报内容
- **推荐解释**：说明为什么推荐某条内容
- **意图识别**：理解用户查询意图

### 6.4 多模态交互

- **文本交互**：命令行、聊天界面
- **语音交互**：语音指令、语音播报
- **手势/触控**：移动端交互

---

## 7. 系统与工程能力

### 7.1 架构设计

#### 简化架构（一键部署版）

```
单机/容器架构：
┌─────────────────────────────────────────┐
│           FastAPI 应用服务                │
│  ┌─────────┬─────────┬─────────┐       │
│  │ 采集器  │ 处理器  │ 推送器  │       │
│  └────┬────┴────┬────┴────┬────┘       │
│       └─────────┼─────────┘            │
│              调度器(APScheduler)        │
├─────────────────────────────────────────┤
│  SQLite/PostgreSQL  │  Redis(可选)     │
└─────────────────────────────────────────┘
```

#### OpenClaw Skill 架构

```
OpenClaw 集成模式：
┌─────────────────────────────────────────┐
│           OpenClaw 运行时                │
│  ┌─────────────────────────────────┐   │
│  │      Daily Agent Skill          │   │
│  │  ┌───────┬───────┬───────┐     │   │
│  │  │ Skill │ Skill │ Skill │ ... │   │
│  │  │Config │ Logic │ Hooks │     │   │
│  │  └───┬───┴───┬───┴───┬───┘     │   │
│  └──────┼───────┼───────┼─────────┘   │
│         └───────┼───────┘              │
│            OpenClaw 基础设施            │
│     (调度、存储、配置、凭证管理)          │
└─────────────────────────────────────────┘
```

### 7.2 数据存储

| 存储类型 | 用途 | 推荐方案 |
|----------|------|----------|
| **关系型数据库** | 用户配置、内容元数据 | SQLite(单机) / PostgreSQL |
| **缓存** | 热点数据、会话、去重 | Python dict / Redis |
| **文件存储** | 配置、日志、导出文件 | 本地文件系统 |

**数据目录结构：**
```
data/
├── daily.db              # SQLite 数据库
├── cache/                # 缓存文件
├── exports/              # 导出的日报
├── logs/                 # 日志文件
└── config/
    ├── columns.yaml      # 分栏配置（热更新）
    └── filters.yaml      # 过滤规则
```

### 7.3 性能与可靠性

| 场景 | 策略 | 实现方式 |
|------|------|----------|
| **并发采集** | 异步 IO | `httpx.AsyncClient` + `asyncio` |
| **失败重试** | 指数退避 | `tenacity` 装饰器 |
| **任务调度** | 定时触发 | `APScheduler` |
| **服务健康** | 心跳检测 | `/health` 端点 |

**资源限制（适合 2核4G 服务器）：**
- 并发采集数：5-10 个源同时
- 单条内容最大长度：100KB
- 保留天数：30 天（可配置）
- 日志轮转：每天一份，保留 7 天

### 7.4 安全与隐私

| 层面 | 措施 | 实现 |
|------|------|------|
| **凭证存储** | 环境变量 | `.env` 文件 + `os.environ` |
| **传输安全** | HTTPS 强制 | 对外 API 全走 HTTPS |
| **日志脱敏** | 自动过滤 | 敏感字段正则替换 |
| **访问控制** | Token 校验 | API 请求头校验 |
| **数据隔离** | 用户隔离 | 单用户部署天然隔离 |

---

## 8. 智能化能力

### 8.1 机器学习应用

| 应用场景 | 技术方法 |
|----------|----------|
| **内容分类** | 文本分类模型 (BERT、FastText) |
| **点击率预测** | 排序学习 (Learning to Rank) |
| **用户分群** | 聚类算法 (K-Means、DBSCAN) |
| **异常检测** | 孤立森林、统计方法 |
| **趋势预测** | 时间序列分析、LSTM |

### 8.2 大语言模型 (LLM) 集成

- **内容理解**：深度语义理解、推理能力
- **智能摘要**：高质量内容提炼
- **问答系统**：基于内容的智能问答
- **内容生成**：自动撰写评论、分析
- **多轮对话**：复杂交互场景处理

### 8.3 持续学习优化

- **在线学习**：实时更新模型参数
- **A/B 测试**：对比不同策略效果
- **效果评估**：准确率、召回率、用户满意度
- **模型迭代**：定期重训练、版本管理

### 8.4 智能工作流

```
智能化流程：
采集 → 清洗 → 理解 → 筛选 → 个性化 → 摘要 → 排版 → 推送
  ↑________________________________________________↓
              反馈循环优化
```

### 8.5 LLM 内容处理引擎

#### 8.5.1 智能分辨能力

| 能力项 | 说明 | 应用场景 |
|--------|------|----------|
| **内容质量评估** | 评估文章原创性、深度、专业性 | 过滤低质、营销、AI 洗稿内容 |
| **可信度分析** | 识别虚假信息、谣言、偏见 | 标注信息来源可信度等级 |
| **相关性判断** | 判断内容与用户兴趣匹配度 | 精准筛选高相关度内容 |
| **时效性评估** | 识别内容新鲜度、是否过时 | 优先推送最新资讯 |
| **情感倾向分析** | 识别内容情感极性、立场 | 平衡正负观点，避免信息茧房 |
| **广告识别** | 识别软广、营销内容 | 过滤干扰性商业内容 |

**质量评分维度：**
```json
{
  "quality_score": {
    "originality": 0.85,      // 原创性
    "depth": 0.72,            // 深度
    "credibility": 0.90,      // 可信度
    "relevance": 0.88,        // 相关性
    "freshness": 0.95,        // 时效性
    "readability": 0.80,      // 可读性
    "overall": 0.85           // 综合评分
  },
  "flags": {
    "is_advertisement": false,
    "is_clickbait": false,
    "is_outdated": false,
    "contains_misinformation": false
  }
}
```

#### 8.5.2 智能整理能力

| 能力项 | 说明 | 技术方法 |
|--------|------|----------|
| **主题聚类** | 将相似内容自动归类 | 语义相似度 + LLM 主题提取 |
| **逻辑重组** | 重新组织信息结构 | 因果链重建、时间线梳理 |
| **多源融合** | 合并多来源报道 | 事件对齐、去重补全 |
| **标签体系生成** | 自动提取并归类标签 | 动态标签生成与层级构建 |
| **知识图谱构建** | 提取实体关系构建图谱 | 实体识别 + 关系抽取 + 图谱推理 |
| **冲突检测** | 识别不同来源的矛盾信息 | 事实核查与多源比对 |

**内容整理流程：**
```
原始内容 → 实体提取 → 关系识别 → 主题聚类 → 冲突检测 → 结构重组 → 知识融合
                ↓
         动态标签体系 ← 主题建模
                ↓
         知识图谱更新 ← 实体链接
```

#### 8.5.3 智能摘要能力

| 摘要类型 | 说明 | 适用场景 |
|----------|------|----------|
| **一句话摘要** | 最精炼的核心观点 | 标题生成、快速预览 |
| **要点摘要** | 3-5 个关键要点 | 快速了解核心内容 |
| **段落摘要** | 1-2 段简短总结 | 邮件推送、通知栏 |
| **详细摘要** | 保留关键细节的总结 | 深度阅读前的预览 |
| **多文档摘要** | 合并多篇内容的综合摘要 | 专题汇总、事件追踪 |
| **对比摘要** | 对比不同观点的摘要 | 争议话题、多视角呈现 |

**个性化摘要策略：**
```yaml
摘要生成:
  用户画像驱动:
    - 技术背景: 保留技术细节、专业术语
    - 管理层: 突出商业影响、决策建议
    - 初学者: 解释术语、补充背景知识
  
  场景适配:
    - 通勤场景: 语音友好、段落简短
    - 深度阅读: 结构完整、保留引用
    - 快速浏览: 要点优先、层级清晰
  
  风格选择:
    - 简洁风格: "一句话 + 3要点"
    - 详细风格: 分段总结 + 关键引用
    - 故事风格: 按时间线叙述事件发展
```

**多语言摘要：**
- **跨语言摘要**：英文内容生成中文摘要
- **多语言输出**：同一内容生成多语言版本
- **文化适配**：根据目标语言调整表达习惯

#### 8.5.4 LLM 处理流程架构

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM 内容处理引擎                         │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   分辨模块   │   整理模块   │   摘要模块   │    质量控制模块    │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ • 质量评估   │ • 实体提取   │ • 内容理解   │ • 幻觉检测        │
│ • 可信度分析 │ • 关系识别   │ • 要点提取   │ • 事实核查        │
│ • 相关性判断 │ • 主题聚类   │ • 语言生成   │ • 一致性检查      │
│ • 情感分析   │ • 结构重组   │ • 风格适配   │ • 人工复核接口    │
└─────────────┴─────────────┴─────────────┴───────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ↓                   ↓
              反馈学习循环          用户偏好适配
```

#### 8.5.5 Prompt 工程最佳实践

| 场景 | Prompt 策略 | 示例 |
|------|-------------|------|
| **分辨** | 角色设定 + 评估标准 + 输出格式 | "作为内容质量评估专家，请从原创性、深度、可信度三个维度评分..." |
| **整理** | 任务定义 + 输入格式 + 输出结构 | "请将以下新闻按主题聚类，每类提取核心主题词和关键事件..." |
| **摘要** | 角色 + 受众 + 长度 + 风格 | "为技术管理者生成一份简洁摘要（100字以内），突出技术趋势和业务影响..." |

**Prompt 优化技巧：**
- **少样本学习 (Few-shot)**：提供 2-3 个示例引导输出格式
- **思维链 (CoT)**：要求模型展示推理过程，提高准确性
- **角色扮演**：设定专家角色提升专业性
- **输出约束**：明确格式要求（JSON、Markdown、表格等）

---

## 9. 启动设置与交互式配置

提供友好的交互式向导，帮助用户快速完成初始配置，包括用户画像设置、兴趣偏好学习和日报内容定制。

### 9.1 启动设置向导

**启动命令：**

```bash
# 首次启动交互式设置
$ python -m src.cli setup

# 重新配置特定模块
$ python -m src.cli setup --profile      # 仅用户画像
$ python -m src.cli setup --interests    # 仅兴趣偏好
$ python -m src.cli setup --daily        # 仅日报内容
$ python -m src.cli setup --all          # 完整重新配置
```

**交互式启动流程：**

```bash
$ python -m src.cli setup

🎉 欢迎使用 Daily Agent 个性化日报系统

这是一个交互式设置向导，将帮助您完成初始配置。
整个过程大约需要 3-5 分钟。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 设置步骤概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 👤 用户画像设置 (约 1 分钟)
  2. 🎯 兴趣偏好配置 (约 2 分钟)
  3. 📰 日报内容定制 (约 1 分钟)
  4. 🔗 推送渠道配置 (可选)

按 Enter 开始设置...
```

### 9.2 用户画像交互式设置

**设置流程：**

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 步骤 1/4: 用户画像设置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

这些基础信息将帮助我为您筛选更相关的内容。

📝 您当前从事的行业是？
   [1] 互联网/科技
   [2] 金融/投资
   [3] 咨询/商业分析
   [4] 媒体/内容创作
   [5] 学术研究
   [6] 医疗健康
   [7] 制造业
   [8] 教育/培训
   [9] 其他

请选择 [1-9]: 1

📝 您的职位或角色是？
   [1] 技术开发者/工程师
   [2] 产品经理
   [3] 创业者/高管
   [4] 投资人/分析师
   [5] 设计师
   [6] 市场/运营
   [7] 学生
   [8] 自由职业者
   [9] 其他

请选择 [1-9]: 2

📝 您的专业领域或技术栈是？（多选，空格分隔）
   例如: AI 机器学习 Python 产品设计

请输入: AI 大语言模型 产品设计 Python

✅ 已记录专业领域: AI、大语言模型、产品设计、Python

📝 您每天大约有多少时间阅读日报？
   [1] 5-10 分钟（精简版）
   [2] 15-20 分钟（标准版）
   [3] 30 分钟以上（深度版）

请选择 [1-3]: 2

✅ 用户画像设置完成！
```

**用户画像数据结构：**

```python
{
    "user_id": "default",
    "profile": {
        "industry": "互联网/科技",
        "position": "产品经理",
        "expertise": ["AI", "大语言模型", "产品设计", "Python"],
        "experience_level": "senior",  # junior/mid/senior/expert
        "company_size": "startup",     # startup/mid/enterprise
        "location": "北京"             # 用于本地化内容
    },
    "reading_preferences": {
        "daily_time_minutes": 20,
        "preferred_time": "09:00",
        "timezone": "Asia/Shanghai"
    }
}
```

### 9.3 兴趣偏好交互式配置

**设置流程：**

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 步骤 2/4: 兴趣偏好配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

我将通过几个简单的问题了解您的兴趣偏好。
您也可以直接选择预设模板。

📝 选择配置方式：
   [1] 🚀 快速配置 - 选择预设模板
   [2] 🎨 自定义配置 - 详细设置每一项

请选择 [1-2]: 1

📝 选择预设模板：
   [1] 👨‍💻 技术开发者 - 关注 AI、开源、编程语言
   [2] 💼 产品经理 - 关注产品设计、用户增长、行业动态
   [3] 💰 投资人 - 关注市场趋势、创业公司、财报数据
   [4] 📊 商业分析师 - 关注行业研究、市场数据、竞争分析
   [5] 🎨 设计师 - 关注设计趋势、创意灵感、设计工具
   [6] 📰 综合资讯 - 平衡的科技、商业、社会资讯

请选择 [1-6]: 2

✅ 已选择模板: [产品经理]

📋 模板包含以下兴趣标签：
   核心兴趣: 产品设计、用户增长、用户体验、产品策略
   关注行业: 互联网、SaaS、消费电子
   关注话题: AI应用、商业模式、市场趋势

📝 是否添加自定义兴趣标签？
   输入标签（空格分隔），或直接按 Enter 跳过

请输入: 数据分析 低代码平台

✅ 已添加: 数据分析、低代码平台
```

**自定义配置流程：**

```bash
🎨 自定义兴趣配置

📝 核心关注领域（最多选 5 个）：
   [x] 人工智能/机器学习
   [x] 大语言模型/AIGC
   [ ] 区块链/Web3
   [x] 云计算/云原生
   [ ] 网络安全
   [x] 移动互联网
   [ ] 物联网/硬件
   [ ] 生物科技
   [ ] 新能源
   [ ] 其他

📝 感兴趣的内容类型：
   [x] 行业新闻和动态
   [x] 深度分析文章
   [x] 技术教程/实践案例
   [x] 产品发布和评测
   [ ] 创业公司融资信息
   [ ] 学术研究报告
   [x] 观点/评论文章

📝 偏好来源类型：
   [x] 主流媒体（36氪、虎嗅等）
   [x] 开发者社区（GitHub、Hacker News）
   [x] 社交媒体（即刻、Twitter）
   [ ] 学术论文/技术博客
   [x] 视频/播客内容

📝 内容语言偏好：
   [1] 仅中文
   [2] 仅英文
   [3] 中英文混合（优先中文）
   [4] 中英文混合（优先英文）

请选择 [1-4]: 3
```

**兴趣偏好数据结构：**

```python
{
    "interests": {
        "core_topics": [
            {"name": "产品设计", "weight": 1.0},
            {"name": "用户增长", "weight": 0.9},
            {"name": "AI应用", "weight": 0.9},
            {"name": "数据分析", "weight": 0.8},
            {"name": "低代码平台", "weight": 0.7}
        ],
        "content_types": ["news", "analysis", "tutorial", "product_review"],
        "source_preferences": {
            "media": 0.8,
            "community": 0.9,
            "social": 0.7,
            "academic": 0.3
        },
        "language_preference": "zh_first",
        "content_depth": "medium",  # light/medium/deep
        "novelty_preference": "balanced"  # trending/balanced/timeless
    }
}
```

### 9.4 日报内容交互式定制

**设置流程：**

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 步骤 3/4: 日报内容定制
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

定制您的日报结构、分栏和内容筛选规则。

📝 日报风格选择：
   [1] 📰 新闻简报型 - 标题+摘要，快速浏览
   [2] 📖 深度阅读型 - 详细摘要+关键要点
   [3] 💬 对话简报型 - 聊天式摘要，适合移动端
   [4] 📊 数据驱动型 - 图表+数据，适合分析师

请选择 [1-4]: 2

📝 日报分栏设置：

   [x] 🔥 今日头条 - 重要科技/商业新闻
       └─ 条数: [3]条（1-10）
   
   [x] 🤖 AI/技术 - AI进展、技术趋势
       └─ 条数: [5]条（1-10）
   
   [x] 💰 商业/投资 - 融资、财报、市场动态
       └─ 条数: [3]条（1-10）
   
   [x] 🛠️ 产品/工具 - 新产品、工具推荐
       └─ 条数: [2]条（1-10）
   
   [ ] 📚 深度阅读 - 长文推荐
       └─ 条数: [1]条（1-5）
   
   [ ] 💬 社区热议 - 社交媒体热门讨论
       └─ 条数: [3]条（1-10）

📝 内容筛选规则：

   最低质量分数: [60]/100
   （越高内容越精选，越低内容越丰富）

   时间范围: [24]小时
   （只采集最近 N 小时的内容）

   去重敏感度: [中等]
   [1] 宽松 - 保留相似内容
   [2] 中等 - 平衡去重
   [3] 严格 - 只保留独特内容

📝 摘要生成设置：
   [1] 规则摘要 - 快速、稳定
   [2] LLM摘要 - 高质量、需要API Key

请选择 [1-2]: 2

⚠️ 未检测到 OPENAI_API_KEY，将使用规则摘要。
   如需使用 LLM 摘要，请在 .env 中配置 API Key。
```

**日报配置数据结构：**

```python
{
    "daily_report": {
        "style": "detailed",  # brief/detailed/chat/data
        "columns": [
            {
                "id": "headlines",
                "name": "今日头条",
                "enabled": True,
                "max_items": 3,
                "order": 1
            },
            {
                "id": "ai_tech",
                "name": "AI/技术",
                "enabled": True,
                "max_items": 5,
                "order": 2
            },
            {
                "id": "business",
                "name": "商业/投资",
                "enabled": True,
                "max_items": 3,
                "order": 3
            },
            {
                "id": "products",
                "name": "产品/工具",
                "enabled": True,
                "max_items": 2,
                "order": 4
            }
        ],
        "filter_rules": {
            "min_quality_score": 60,
            "time_window_hours": 24,
            "dedup_level": "medium"  # low/medium/high
        },
        "summary": {
            "method": "llm",  # rule/llm
            "length": "medium",  # short/medium/long
            "include_key_points": True
        }
    }
}
```

### 9.5 配置模板库

**预设模板：**

```yaml
# 模板: 技术开发者 (tech_developer)
tech_developer:
  name: "👨‍💻 技术开发者"
  description: "专注技术趋势、开源项目、编程实践"
  profile:
    industry: "互联网/科技"
    position: "技术开发者"
    expertise: ["软件开发", "开源技术", "系统架构"]
  interests:
    core_topics:
      - {name: "人工智能", weight: 1.0}
      - {name: "大语言模型", weight: 0.95}
      - {name: "开源项目", weight: 0.9}
      - {name: "编程语言", weight: 0.85}
      - {name: "云原生", weight: 0.8}
    content_types: ["tutorial", "news", "analysis"]
  daily:
    style: "detailed"
    columns:
      - {id: "github", name: "🔥 GitHub 趋势", max_items: 5}
      - {id: "ai_tech", name: "🤖 AI/技术", max_items: 5}
      - {id: "dev_tools", name: "🛠️ 开发工具", max_items: 3}
      - {id: "tech_news", name: "📰 科技新闻", max_items: 3}

# 模板: 产品经理 (product_manager)
product_manager:
  name: "💼 产品经理"
  description: "关注产品设计、用户增长、行业动态"
  profile:
    industry: "互联网/科技"
    position: "产品经理"
    expertise: ["产品设计", "用户研究", "数据分析"]
  interests:
    core_topics:
      - {name: "产品设计", weight: 1.0}
      - {name: "用户增长", weight: 0.9}
      - {name: "用户体验", weight: 0.9}
      - {name: "商业模式", weight: 0.8}
      - {name: "AI应用", weight: 0.85}
    content_types: ["analysis", "product_review", "news"]
  daily:
    style: "brief"
    columns:
      - {id: "headlines", name: "🔥 今日头条", max_items: 3}
      - {id: "product_hunt", name: "🚀 Product Hunt", max_items: 5}
      - {id: "ai_apps", name: "🤖 AI应用", max_items: 4}
      - {id: "business", name: "💰 商业动态", max_items: 3}

# 模板: 投资人 (investor)
investor:
  name: "💰 投资人"
  description: "关注市场趋势、创业公司、财报数据"
  profile:
    industry: "金融/投资"
    position: "投资人/分析师"
    expertise: ["投资分析", "市场研究", "财务分析"]
  interests:
    core_topics:
      - {name: "创业公司", weight: 1.0}
      - {name: "投融资", weight: 0.95}
      - {name: "市场趋势", weight: 0.9}
      - {name: "财报分析", weight: 0.85}
      - {name: "宏观经济", weight: 0.7}
    content_types: ["news", "analysis"]
  daily:
    style: "data"
    columns:
      - {id: "market", name: "📈 市场动态", max_items: 5}
      - {id: "funding", name: "💰 融资信息", max_items: 5}
      - {id: "earnings", name: "📊 财报速递", max_items: 3}
      - {id: "analysis", name: "🔍 深度分析", max_items: 3}

# 模板: 综合资讯 (general)
general:
  name: "📰 综合资讯"
  description: "平衡的科技、商业、社会资讯"
  profile:
    industry: "其他"
    position: "其他"
    expertise: []
  interests:
    core_topics:
      - {name: "科技", weight: 0.8}
      - {name: "商业", weight: 0.8}
      - {name: "社会", weight: 0.6}
      - {name: "文化", weight: 0.5}
    content_types: ["news", "analysis"]
  daily:
    style: "brief"
    columns:
      - {id: "headlines", name: "🔥 今日头条", max_items: 5}
      - {id: "tech", name: "💻 科技", max_items: 4}
      - {id: "business", name: "💼 商业", max_items: 3}
      - {id: "lifestyle", name: "🌟 生活方式", max_items: 3}
```

### 9.6 配置导入导出

**导出配置：**

```bash
$ python -m src.cli setup export --format yaml --output my-config.yaml
✅ 配置已导出到: my-config.yaml
```

**导入配置：**

```bash
$ python -m src.cli setup import my-config.yaml
📋 检测到配置文件，包含以下设置：
   - 用户画像: 产品经理
   - 兴趣标签: 5 个
   - 日报分栏: 4 个

📝 是否覆盖现有配置? [y/N]: y
✅ 配置导入成功
```

### 9.5 交互式 LLM 配置

提供友好的交互式向导，帮助用户配置大语言模型（LLM），支持多种提供商和模型选择。

#### 9.5.1 LLM 配置命令

```bash
# 启动 LLM 配置向导
$ python -m src.cli llm setup

# 查看当前 LLM 配置
$ python -m src.cli llm status

# 测试 LLM 连接
$ python -m src.cli llm test

# 切换模型
$ python -m src.cli llm switch

# 查看支持的模型列表
$ python -m src.cli llm models
```

#### 9.5.2 交互式配置流程

```bash
$ python -m src.cli llm setup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 LLM 配置向导
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

本向导将帮助您配置大语言模型，用于：
  • 智能内容摘要生成
  • 内容质量评估
  • 个性化推荐优化

按 Enter 开始配置...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
步骤 1/3: 选择 LLM 提供商
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 选择 LLM 提供商：

   [1] 🌐 OpenAI (推荐)
       模型: GPT-4o, GPT-4o-mini, GPT-4
       特点: 稳定、高质量、速度快
   
   [2] 🔗 OpenRouter
       模型: Claude, GPT-4, 国产模型
       特点: 聚合多厂商、性价比高
   
   [3] 🏠 Ollama (本地部署)
       模型: Llama, Mistral, Qwen 等
       特点: 免费、隐私安全、无需网络
   
   [4] ☁️ Azure OpenAI
       模型: GPT-4, GPT-3.5
       特点: 企业级、SLA保障
   
   [5] 🌙 Kimi (Moonshot)
       模型: kimi-k2, moonshot-v1-128k
       特点: 长文本处理专家，支持200万字上下文
   
   [6] 🔷 通义千问 (Qwen)
       模型: qwen-max, qwen-plus, qwen-turbo
       特点: 阿里出品，中文理解优秀，代码能力强
   
   [7] 🔶 智谱 GLM
       模型: glm-4-plus, glm-4, glm-4-air
       特点: 清华出品，国内最早的开源大模型
   
   [8] ⏭️  跳过 - 暂不配置 LLM
       将使用规则摘要（功能受限）

请选择 [1-6]: 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
步骤 2/3: 配置 API 密钥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 您选择了 [OpenAI]

📖 获取 API Key 步骤：
   1. 访问 https://platform.openai.com/api-keys
   2. 登录您的 OpenAI 账号
   3. 点击 "Create new secret key"
   4. 复制生成的密钥

⚠️  提示：密钥仅保存在本地 .env 文件，不会上传

请输入 OpenAI API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

✅ API Key 格式验证通过

📝 选择默认模型：

   [1] gpt-4o-mini (推荐)
       性价比高，适合日常使用
       价格: $0.15 / 1M tokens
   
   [2] gpt-4o
       最强性能，适合重要内容
       价格: $5.00 / 1M tokens
   
   [3] gpt-4-turbo
       平衡性能与价格
       价格: $10.00 / 1M tokens

请选择 [1-3]: 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
步骤 3/3: 功能配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 启用 LLM 增强功能：

   [x] 智能摘要生成
       使用 LLM 生成高质量内容摘要
   
   [x] 内容质量评估
       自动评估文章原创性、深度
   
   [ ] 智能标签提取
       自动提取精准内容标签
   
   [ ] 个性化推荐优化
       基于 LLM 的个性化排序

是否启用上述功能？ [Y/n]: Y

📝 摘要长度偏好：
   [1] 简洁 - 一句话摘要
   [2] 标准 - 3-5个要点
   [3] 详细 - 完整段落摘要

请选择 [1-3]: 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
配置预览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  提供商: OpenAI
  模型: gpt-4o-mini
  API Key: sk-****-xxxx (已脱敏)
  功能: 智能摘要、质量评估
  摘要长度: 标准 (3-5要点)

是否保存配置? [Y/n]: Y

🧪 正在测试 API 连接...
✅ 连接成功！模型 gpt-4o-mini 可用

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ LLM 配置完成！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

配置已保存到 .env 文件

💡 提示：
  • 运行 'python -m src.cli llm status' 查看配置状态
  • 运行 'python -m src.cli llm test' 测试连接
  • 如需更改配置，重新运行 'python -m src.cli llm setup'
```

#### 9.5.3 LLM 提供商配置详情

**OpenAI 配置：**
```yaml
provider: openai
api_key: sk-xxxxxxxx
base_url: https://api.openai.com/v1  # 可选，用于代理
model: gpt-4o-mini
models_available:
  - gpt-4o-mini    # 推荐日常使用
  - gpt-4o         # 高性能需求
  - gpt-4-turbo    # 复杂任务
  - gpt-3.5-turbo  # 成本敏感
```

**OpenRouter 配置：**
```yaml
provider: openrouter
api_key: sk-or-xxxxxxxx
base_url: https://openrouter.ai/api/v1
model: anthropic/claude-3.5-sonnet
models_available:
  - anthropic/claude-3.5-sonnet  # 推荐
  - openai/gpt-4o
  - google/gemini-pro
  - moonshot/kimi-k2  # 国产
```

**Ollama 本地配置：**
```yaml
provider: ollama
base_url: http://localhost:11434
model: qwen2.5:14b
models_available:
  - qwen2.5:14b      # 中文推荐
  - llama3.2:8b      # 英文推荐
  - mistral:7b       # 平衡选择
install_guide: |
  1. 安装 Ollama: curl -fsSL https://ollama.com/install.sh | sh
  2. 拉取模型: ollama pull qwen2.5:14b
  3. 验证: ollama run qwen2.5:14b
```

**Azure OpenAI 配置：**
```yaml
provider: azure
api_key: xxxxxxxxxxxxxxxx
base_url: https://your-resource.openai.azure.com
api_version: 2024-02-15-preview
deployment: gpt-4o
```

**🇨🇳 国内大模型配置：**

```yaml
# Kimi (Moonshot) - 长文本处理专家
# 获取 API Key: https://platform.moonshot.cn/
provider: moonshot
api_key: sk-xxxxxxxx
default_model: kimi-k2
models_available:
  - kimi-k2              # 最新旗舰，综合能力强（推荐）
  - moonshot-v1-128k     # 支持128K长上下文
  - moonshot-v1-32k      # 支持32K上下文
  - moonshot-v1-8k       # 标准版，性价比高
features:
  - 支持200万字长文本输入
  - 适合深度文章分析和多文档对比
  - 中文写作能力强

# 通义千问 (Qwen) - 阿里出品
# 获取 API Key: https://help.aliyun.com/zh/dashscope/
provider: dashscope
api_key: sk-xxxxxxxx
default_model: qwen-max
models_available:
  - qwen-max             # 最强性能，复杂任务（推荐）
  - qwen-plus            # 平衡性能与成本
  - qwen-turbo           # 极速响应，高性价比
  - qwen-coder-plus      # 代码专用
features:
  - 中文理解能力行业领先
  - 代码生成和解释能力强
  - 支持工具调用(Function Calling)

# 智谱 GLM - 清华出品
# 获取 API Key: https://open.bigmodel.cn/
provider: zhipu
api_key: xxxxxxxx
default_model: glm-4-plus
models_available:
  - glm-4-plus           # 最新旗舰，综合能力最强（推荐）
  - glm-4                # 标准版，高质量输出
  - glm-4-air            # 高性价比版本
  - glm-4-flash          # 极速版，成本最低
features:
  - 国内最早的开源大模型
  - 对齐中文语境和文化背景
  - 支持实时联网搜索

# 其他国内模型（可选）
# 文心一言 (百度): https://cloud.baidu.com/doc/WENXINWORKSHOP/
provider: baidu
api_key: xxxxxxxx
secret_key: xxxxxxxx
model: ernie-bot-4
```

#### 9.5.4 多模型配置策略

支持配置多个 LLM，按需切换：

```yaml
llm_configs:
  # 默认配置
  default:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o-mini
  
  # 高质量摘要专用
  premium:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o
  
  # 备用配置
  fallback:
    provider: openrouter
    api_key: ${OPENROUTER_API_KEY}
    model: anthropic/claude-3.5-sonnet
  
  # 本地隐私模式
  local:
    provider: ollama
    base_url: http://localhost:11434
    model: qwen2.5:14b

# 使用策略
usage_strategy:
  summary: default      # 日常摘要使用默认
  quality_check: premium  # 质量评估使用高质量
  fallback_order: [default, fallback, local]  # 失败时 fallback
```

#### 9.5.5 智能模型选择建议

系统根据场景自动推荐模型：

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 日常摘要 | gpt-4o-mini | 性价比高，速度快 |
| 深度分析 | gpt-4o / Claude 3.5 | 推理能力强 |
| 中文内容 | Kimi / Qwen / GLM | 中文优化，国内访问快 |
| 隐私敏感 | Ollama 本地模型 | 数据不出本地 |
| 离线环境 | Ollama 本地模型 | 无需网络连接 |
| 预算敏感 | gpt-4o-mini / 本地模型 | 成本低 |

#### 9.5.6 LLM 状态查看命令

```bash
$ python -m src.cli llm status

🤖 LLM 配置状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

当前配置:
  提供商:   OpenAI
  模型:     gpt-4o-mini
  状态:     ✅ 正常
  上次测试: 2024-01-15 09:30:00

功能状态:
  智能摘要:   ✅ 已启用
  质量评估:   ✅ 已启用
  智能标签:   ⚪ 未启用
  推荐优化:   ⚪ 未启用

使用量统计（本月）:
  API 调用:   1,234 次
  Token 消耗: 456K
  预估费用:   $0.07

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 9.5.7 模型切换命令

```bash
$ python -m src.cli llm switch

📝 选择要使用的模型：

当前: gpt-4o-mini

   [1] gpt-4o-mini (当前)
   [2] gpt-4o
   [3] gpt-4-turbo
   [4] 配置新模型...

请选择 [1-4]: 2

✅ 已切换到 gpt-4o

🧪 测试新模型...
✅ 模型可用
```

### 9.6 冷启动推荐策略

对于新用户，系统提供多种冷启动方式：

| 方式 | 描述 | 适用场景 |
|------|------|----------|
| **模板选择** | 选择预设模板快速开始 | 不确定具体偏好 |
| **社交导入** | 从 Twitter/GitHub 导入关注 | 已有社交图谱 |
| **阅读测试** | 展示10篇文章，根据反馈学习 | 希望精准定制 |
| **手动配置** | 逐项详细设置 | 明确知道自己要什么 |
| **热门推荐** | 先按热门内容推送，逐步学习 | 希望立即开始使用 |

---

## 10. OpenClaw Skill 规范

### 9.1 Skill 定义与结构

```yaml
Skill:
  metadata:
    name: skill-name           # Skill 唯一标识符
    version: "1.0.0"          # 语义化版本
    description: "描述"        # 功能描述
    author: "作者"             # 开发者
    category: "category"      # 分类标签
    language: "zh/en"         # 支持语言
  
  capabilities:               # 能力声明
    inputs:                   # 输入参数
      - name: "param1"
        type: "string"
        required: true
        description: "参数说明"
    
    outputs:                  # 输出结果
      - name: "result"
        type: "object"
        description: "输出说明"
    
    triggers:                 # 触发方式
      - schedule: "0 9 * * *"  # 定时触发
      - webhook: "/endpoint"   # Webhook 触发
      - event: "on_new_content" # 事件触发
  
  dependencies:               # 依赖声明
    skills: ["base-skill"]    # 依赖的其他 Skill
    apis: ["news-api"]        # 外部 API
    models: ["gpt-4"]         # 需要的模型
```

### 9.2 Skill 分类体系

| 分类 | 说明 | 示例 |
|------|------|------|
| **采集类 (Collector)** | 信息获取与抓取 | RSS采集、API拉取、网页爬虫 |
| **处理类 (Processor)** | 内容处理与转换 | 清洗、摘要、翻译、分类 |
| **分析类 (Analyzer)** | 智能分析与推理 | 情感分析、实体识别、趋势预测 |
| **输出类 (Output)** | 结果输出与呈现 | 邮件推送、报告生成、可视化 |
| **交互类 (Interactive)** | 用户交互与反馈 | 问答、指令处理、反馈收集 |
| **编排类 (Orchestrator)** | 工作流编排与调度 | 任务调度、流程控制、异常处理 |

### 9.3 Skill 开发规范

#### 目录结构
```
skill-name/
├── SKILL.md              # Skill 定义文档（必需）
├── config.yaml           # 配置文件
├── src/                  # 源代码目录
│   ├── __init__.py
│   ├── main.py           # 主入口
│   └── utils.py          # 工具函数
├── tests/                # 测试目录
│   └── test_skill.py
├── requirements.txt      # Python 依赖
└── README.md             # 使用说明
```

#### SKILL.md 模板
```markdown
# Skill: skill-name

## 概述
简要描述 Skill 的功能和用途。

## 能力
- 能力1：描述
- 能力2：描述

## 输入/输出
### 输入
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| param1 | string | 是 | 参数说明 |

### 输出
| 字段 | 类型 | 说明 |
|------|------|------|
| result | object | 结果说明 |

## 使用示例
```json
{
  "input": {...},
  "output": {...}
}
```

## 依赖
- 依赖1：说明
- 依赖2：说明

## 版本历史
- v1.0.0: 初始版本
```

### 9.4 Skill 注册与发现

```json
{
  "registry": {
    "type": "local|remote|marketplace",
    "endpoint": "https://skills.openclaw.io",
    "authentication": "api-key|oauth|none"
  },
  "discovery": {
    "search": {
      "by_keyword": true,
      "by_category": true,
      "by_tag": true,
      "by_capability": true
    },
    "filter": {
      "rating": ">=4.0",
      "downloads": ">=100",
      "verified": true
    }
  }
}
```

### 9.5 Skill 运行时接口

```python
# 标准接口定义
class BaseSkill:
    """所有 Skill 的基类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.metadata = self._load_metadata()
    
    async def initialize(self) -> None:
        """初始化 Skill"""
        pass
    
    async def execute(self, context: Context) -> Result:
        """执行 Skill 主逻辑"""
        raise NotImplementedError
    
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        return HealthStatus.HEALTHY
    
    async def shutdown(self) -> None:
        """优雅关闭"""
        pass

# 上下文对象
class Context:
    user_id: str
    session_id: str
    input_data: dict
    env_vars: dict
    dependencies: dict  # 依赖的 Skill 实例
```

### 9.6 Skill 组合与编排

```yaml
# 工作流定义示例
workflow:
  name: "daily-report-generation"
  version: "1.0.0"
  
  steps:
    - id: "collect"
      skill: "rss-collector"
      inputs:
        feeds: "${user.preferred_feeds}"
      
    - id: "filter"
      skill: "content-filter"
      inputs:
        contents: "${collect.outputs.articles}"
        keywords: "${user.interests}"
      depends_on: ["collect"]
      
    - id: "summarize"
      skill: "llm-summarizer"
      inputs:
        articles: "${filter.outputs.filtered}"
        style: "${user.summary_style}"
      depends_on: ["filter"]
      
    - id: "format"
      skill: "markdown-formatter"
      inputs:
        content: "${summarize.outputs.summaries}"
        template: "daily-report"
      depends_on: ["summarize"]
      
    - id: "notify"
      skill: "email-notifier"
      inputs:
        content: "${format.outputs.document}"
        to: "${user.email}"
      depends_on: ["format"]
  
  error_handling:
    on_failure: "retry|skip|notify"
    max_retries: 3
    retry_delay: "5s"
```

### 9.7 Skill 质量管理

| 质量维度 | 指标 | 要求 |
|----------|------|------|
| **功能完整性** | 接口实现度 | 100% 声明接口必须实现 |
| **代码质量** | 测试覆盖率 | >= 80% |
| **文档完整** | SKILL.md 完整性 | 必需字段全部填写 |
| **性能** | 响应时间 | P99 < 1s |
| **可靠性** | 成功率 | >= 99.5% |
| **安全性** | 漏洞扫描 | 无高危漏洞 |

---

## 🎯 能力评估矩阵

| 能力维度 | 基础版 | 进阶版 | 专业版 |
|----------|:------:|:------:|:------:|
| 信息源数量 | < 20 | 20-100 | > 100 |
| 更新频率 | 每日 1 次 | 每日多次 | 实时流式 |
| 个性化精度 | 规则匹配 | 机器学习 | 深度学习 |
| 摘要质量 | 抽取式 | 简单生成 | LLM 生成 |
| 响应延迟 | 分钟级 | 秒级 | 毫秒级 |
| 用户规模 | < 100 | 100-10k | > 10k |
| 多语言 | 单语言 | 多语言 | 全语言 |
| 交互方式 | 被动接收 | 简单交互 | 智能对话 |
| Skill 生态 | 单 Skill | 多 Skill | 完整 Skill 市场 |

---

## 📚 技术栈参考

### 简化版技术栈（一键部署推荐）

适用于个人服务器部署和 OpenClaw Skill 集成的最小化技术栈：

| 层级 | 推荐技术 | 说明 |
|------|----------|------|
| **采集** | Playwright、httpx、aiohttp | 轻量级异步爬虫，无需 Scrapy 重型框架 |
| **存储** | SQLite / PostgreSQL、Redis | SQLite 适合单机部署，PostgreSQL 适合多用户 |
| **处理** | Python、LangChain、Jinja2 | 简洁的文本处理与模板渲染 |
| **模型** | OpenAI API / OpenRouter / 本地 Ollama | 优先使用 API，可选本地模型 |
| **服务** | FastAPI、Docker | 单容器部署，无需 Kubernetes |
| **调度** | APScheduler / Celery Lite | 轻量级定时任务 |
| **配置** | Pydantic Settings、python-dotenv | 环境变量管理 |

### 部署方式对比

| 部署方式 | 复杂度 | 适用场景 | 资源需求 |
|----------|--------|----------|----------|
| **Docker 单机** | ⭐ 低 | 个人使用、小团队 | 2核4G 即可 |
| **OpenClaw Skill** | ⭐ 低 | 已有 OpenClaw 生态用户 | 依赖 OpenClaw 运行时 |
| **Docker Compose** | ⭐⭐ 中 | 需要独立 Redis/DB | 4核8G 推荐 |
| **K8s 集群** | ⭐⭐⭐⭐ 高 | 企业级大规模部署 | 需要运维能力 |

### 快速启动依赖

```dockerfile
# 最小化 Dockerfile 示例
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "-m", "daily_agent"]
```

```txt
# requirements.txt（精简版）
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.25.0
playwright==1.40.0
apscheduler==3.10.0
redis==5.0.0
sqlalchemy==2.0.0
langchain==0.1.0
openai==1.0.0
jinja2==3.1.0
```

### 架构选型建议

**个人用户 / 一键部署：**
- 数据库：SQLite（零配置）或 PostgreSQL（Docker 一键启动）
- 缓存：内存字典 或 Redis（可选）
- 任务队列：APScheduler（内置）或 Celery + Redis
- LLM：OpenAI API / Claude API（无需本地 GPU）

**OpenClaw Skill 集成：**
- 利用 OpenClaw 的配置管理和凭证注入
- 复用 OpenClaw 的调度器（如支持）
- 遵循 Skill 接口规范（详见第9章）

---

## 🚀 演进路线

```
Phase 1: 基础采集 → 简单过滤 → 定时推送
    ↓
Phase 2: 多源聚合 → 自动摘要 → 基础个性化
    ↓
Phase 3: 智能推荐 → 用户画像 → 多格式输出
    ↓
Phase 4: LLM 增强 → 智能问答 → 持续学习
    ↓
Phase 5: 多模态 → 预测性推荐 → 生态集成
```

---

*本文档作为构建个性化日报信息收集 Agent 的能力参考框架，可根据实际需求进行裁剪和扩展。*
