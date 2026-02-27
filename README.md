# Daily Agent - 完美个性化日报信息收集 Agent

基于 [perfect-daily-agent.md](perfect-daily-agent.md) 能力图谱实现的智能日报系统。

## ✨ 功能特性

### 核心能力

- **🔥 多源采集**
  - RSS 订阅源（TechCrunch、36氪、arXiv 等）
  - API 数据源（Hacker News、GitHub Trending、Hugging Face）
  - 社交媒体（B站、小红书、知乎、即刻）
  - 新闻媒体（财新、FT中文网、第一财经）
  - 音频播客

- **🧠 智能处理**
  - 内容清洗与格式化
  - 关键词提取与主题分类
  - LLM 驱动的自动摘要（1句/3点/段落）
  - 多语言支持

- **🎯 智能筛选**
  - 语义去重与精确去重
  - 基于多维度质量评分
  - 个性化排序算法
  - 多样性保证（避免单一来源占比过高）

- **📤 多格式输出**
  - Markdown / HTML / JSON
  - Telegram / Slack / Discord 推送
  - 邮件推送
  - 自定义模板

- **👤 个性化**
  - 用户画像构建
  - 兴趣偏好学习
  - 冷启动模板支持
  - 反馈驱动的持续优化

### 技术亮点

- **⚡ 异步架构**: 基于 asyncio 的高性能并发采集
- **🔧 热更新配置**: 无需重启服务的配置更新
- **🤖 多 LLM 支持**: OpenAI、Claude、Ollama、Azure、国产模型
- **📊 质量评分**: 多维度内容质量评估体系
- **🔐 安全认证**: API 密钥保护和用户认证

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

最小配置（仅基础功能）：
```bash
# 可选：配置 LLM 以获得更好的摘要效果
OPENAI_API_KEY=sk-your-api-key

# 可选：配置推送渠道
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 3. 启动服务

#### 方式一：Docker（推荐）

```bash
docker-compose up -d
```

#### 方式二：本地运行

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn src.main:app --reload
```

### 4. 验证服务

```bash
curl http://localhost:8080/health
```

访问 API 文档：`http://localhost:8080/docs`

## 📡 API 使用

### 生成日报

```bash
curl -X POST http://localhost:8080/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "default",
    "date": "2024-01-15",
    "columns": ["headlines", "tech"],
    "force_refresh": false
  }'
```

### 获取日报列表

```bash
curl "http://localhost:8080/api/v1/reports?user_id=default&limit=10"
```

### 获取日报详情

```bash
# JSON 格式
curl http://localhost:8080/api/v1/reports/{report_id}

# Markdown 格式
curl "http://localhost:8080/api/v1/reports/{report_id}?format=markdown"
```

### 推送日报

```bash
curl -X POST http://localhost:8080/api/v1/reports/{report_id}/push \
  -H "Content-Type: application/json" \
  -d '{
    "channels": ["telegram", "slack"]
  }'
```

### 手动触发采集

```bash
curl -X POST http://localhost:8080/api/v1/collect
```

### 提交反馈

```bash
curl -X POST http://localhost:8080/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "default",
    "item_id": "content-id",
    "feedback_type": "positive",
    "comment": "很有帮助"
  }'
```

### 获取/更新用户画像

```bash
# 获取画像
curl http://localhost:8080/api/v1/profile/default

# 更新画像
curl -X PUT http://localhost:8080/api/v1/profile/default \
  -H "Content-Type: application/json" \
  -d '{
    "interests": ["AI", "区块链", "编程"],
    "push_time": "09:00"
  }'
```

### 重新加载配置

```bash
curl -X POST http://localhost:8080/api/v1/reload
```

## 🛠️ 配置说明

### 分栏配置 (`config/columns.yaml`)

定义日报的各个分栏：

```yaml
columns:
  - id: "headlines"
    name: "🔥 今日头条"
    description: "当日最重要的科技新闻"
    enabled: true
    max_items: 5
    order: 1
    sources:
      - type: "rss"
        name: "TechCrunch"
        url: "https://techcrunch.com/feed/"
        weight: 1.0
        filter:
          keywords: ["AI", "人工智能", "大模型"]
          exclude: ["广告", "sponsored"]
      
      - type: "api"
        name: "Hacker News"
        provider: "hackernews"
        endpoint: "https://hacker-news.firebaseio.com/v0/topstories.json"
        filter:
          min_score: 100
    
    organization:
      sort_by: "relevance"      # 排序方式：relevance/time/mixed
      dedup_strategy: "semantic" # 去重策略：semantic/exact/none
      summarize: "3_points"     # 摘要方式：1_sentence/3_points/paragraph/none
      highlight_key_info: true
```

### 环境变量

#### 服务配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_NAME` | 应用名称 | DailyAgent |
| `DEBUG` | 调试模式 | false |
| `LOG_LEVEL` | 日志级别 | info |
| `HOST` | 服务监听地址 | 0.0.0.0 |
| `PORT` | 服务端口 | 8080 |

#### LLM 配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | sk-xxx |
| `OPENAI_MODEL` | 模型名称 | gpt-4o-mini |
| `OPENAI_BASE_URL` | 自定义 API 地址 | https://api.openai.com/v1 |

支持多种 LLM 提供商：OpenAI、OpenRouter、Ollama、Azure OpenAI、通义千问、文心一言、智谱 AI

#### 数据库配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 URL | sqlite:///data/daily.db |

#### 采集配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MAX_CONCURRENT_COLLECTORS` | 并发采集数 | 5 |
| `REQUEST_DELAY` | 请求间隔（秒） | 1.0 |
| `CONTENT_RETENTION_DAYS` | 内容保留天数 | 30 |

#### 推送配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEFAULT_PUSH_TIME` | 默认推送时间 | 09:00 |
| `TIMEZONE` | 时区 | Asia/Shanghai |

#### Telegram 推送

| 变量 | 说明 |
|------|------|
| `TELEGRAM_BOT_TOKEN` | Bot Token |
| `TELEGRAM_CHAT_ID` | 聊天 ID |

#### Slack 推送

| 变量 | 说明 |
|------|------|
| `SLACK_BOT_TOKEN` | Bot Token |
| `SLACK_CHANNEL` | 频道名 |

#### Discord 推送

| 变量 | 说明 |
|------|------|
| `DISCORD_BOT_TOKEN` | Bot Token |
| `DISCORD_CHANNEL_ID` | 频道 ID |

#### 邮件推送

| 变量 | 说明 |
|------|------|
| `SMTP_HOST` | SMTP 服务器 |
| `SMTP_PORT` | SMTP 端口 |
| `SMTP_USER` | 用户名 |
| `SMTP_PASSWORD` | 密码 |
| `EMAIL_FROM` | 发件人 |
| `EMAIL_TO` | 收件人 |

## 📁 项目结构

```
.
├── src/                        # 源代码目录
│   ├── collector/              # 采集模块
│   │   ├── rss_collector.py    # RSS 采集器
│   │   ├── api_collector.py    # API 采集器
│   │   ├── bilibili_collector.py  # B站采集器
│   │   ├── xiaohongshu_collector.py  # 小红书采集器
│   │   └── ...                 # 其他采集器
│   ├── processor/              # 处理模块
│   │   ├── cleaner.py          # 内容清洗
│   │   ├── extractor.py        # 信息提取
│   │   └── summarizer.py       # 摘要生成
│   ├── filter/                 # 筛选排序模块
│   │   ├── deduper.py          # 去重算法
│   │   ├── ranker.py           # 排序算法
│   │   └── selector.py         # 内容选择
│   ├── output/                 # 输出模块
│   │   ├── formatter.py        # 格式转换
│   │   └── publisher.py        # 推送发布
│   ├── personalization/        # 个性化模块
│   │   ├── profile.py          # 用户画像
│   │   └── learning.py         # 学习算法
│   ├── auth_manager.py         # 认证管理
│   ├── cli.py                  # 命令行工具
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库模型
│   ├── llm_config.py           # LLM 配置
│   ├── main.py                 # FastAPI 入口
│   ├── models.py               # 数据模型
│   ├── scheduler.py            # 任务调度
│   ├── service.py              # 业务服务
│   └── setup_wizard.py         # 设置向导
├── config/                     # 配置文件目录
│   ├── columns.yaml            # 分栏配置
│   ├── sources_example.yaml    # 数据源配置示例
│   └── templates.yaml          # 模板配置
├── tests/                      # 测试目录
├── data/                       # 数据目录（SQLite 数据库）
├── docker-compose.yml          # Docker 部署配置
├── Dockerfile                  # Docker 镜像构建
├── requirements.txt            # Python 依赖
├── start.sh                    # 启动脚本
└── .env.example                # 环境变量示例
```

## 💬 推送渠道配置

### Telegram

1. 创建 Bot: [@BotFather](https://t.me/botfather)，获取 Bot Token
2. 获取 Chat ID: [@userinfobot](https://t.me/userinfobot)
3. 配置环境变量：
   ```bash
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

### Slack

1. 创建 App: [Slack API](https://api.slack.com/apps)
2. 添加 `chat:write` 权限
3. 安装到工作区并获取 Bot Token
4. 配置环境变量：
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_CHANNEL=#daily-news
   ```

### Discord

1. 创建 Bot: [Discord Developer](https://discord.com/developers/applications)
2. 获取 Bot Token
3. 获取频道 ID（右键频道 -> 复制 ID）
4. 配置环境变量：
   ```bash
   DISCORD_BOT_TOKEN=your-token
   DISCORD_CHANNEL_ID=your-channel-id
   ```

### 邮件

支持任意 SMTP 服务（Gmail、QQ、163 等）：

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=Daily Agent <your-email@gmail.com>
EMAIL_TO=recipient@example.com
```

> Gmail 需要使用应用专用密码，而非登录密码。

## 🖥️ CLI 工具

项目提供命令行工具用于管理：

```bash
# 生成日报
python -m src.cli generate --user default

# 指定日期生成
python -m src.cli generate --user default --date 2024-01-15

# 手动触发采集
python -m src.cli collect

# 推送日报
python -m src.cli push <report_id> --channel telegram --channel slack

# 查看帮助
python -m src.cli --help
```

## 📋 开发计划

- [x] 基础采集 (RSS/API)
- [x] 内容处理 (清洗/摘要/分类)
- [x] 筛选排序 (去重/质量评分/个性化排序)
- [x] 多格式输出 (Markdown/HTML/JSON)
- [x] 多推送渠道 (Telegram/Slack/Discord/邮件)
- [x] 用户画像与个性化
- [x] 反馈学习系统
- [x] CLI 工具
- [x] Docker 部署
- [x] 热更新配置
- [ ] Playwright 网页采集增强
- [ ] 智能问答交互
- [ ] 管理后台 Web UI
- [ ] 多租户支持
- [ ] 多语言界面

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范

- 使用 Python 类型注解
- 异步 IO 操作使用 `async/await`
- 新功能需包含测试
- 遵循 PEP 8 代码风格

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- 能力图谱文档: [perfect-daily-agent.md](perfect-daily-agent.md)
- 开发指南: [AGENTS.md](AGENTS.md)
- 项目主页: https://github.com/uhajivis-cell/openclaw-skills-daily
