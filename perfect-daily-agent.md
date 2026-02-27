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
9. [OpenClaw Skill 规范](#9-openclaw-skill-规范)

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

### 1.2 实时与批量采集

- **实时流式采集**：WebSocket、SSE、Webhook 接收实时推送
- **定时批量采集**：Cron 任务、调度器管理采集任务
- **增量更新机制**：基于时间戳、ETag、哈希的去重采集
- **反爬对抗**：代理池、请求频率控制、User-Agent 轮换、验证码处理

### 1.3 数据解析与清洗

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

## 9. OpenClaw Skill 规范

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
