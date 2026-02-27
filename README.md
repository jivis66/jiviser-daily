# Daily Agent - 完美个性化日报信息收集 Agent

基于 [perfect-daily-agent.md](perfect-daily-agent.md) 能力图谱实现的智能日报系统。

## 功能特性

### 核心能力
- **多源采集**：RSS、API（Hacker News、GitHub 等）、网页爬虫
- **智能处理**：内容清洗、关键词提取、主题分类、自动摘要
- **智能筛选**：语义去重、质量评分、个性化排序、多样性保证
- **多格式输出**：Markdown、HTML、邮件、Telegram、Slack、Discord
- **个性化**：用户画像、兴趣学习、冷启动模板

### 技术栈
- **Web 框架**: FastAPI + Uvicorn
- **数据库**: SQLite (默认) / PostgreSQL
- **任务调度**: APScheduler
- **LLM 集成**: OpenAI API / OpenRouter (可选)
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的参数
```

最小配置：
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

## API 使用

### 生成日报

```bash
curl -X POST http://localhost:8080/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "default"}'
```

### 获取日报列表

```bash
curl http://localhost:8080/api/v1/reports
```

### 推送日报

```bash
curl -X POST http://localhost:8080/api/v1/reports/{report_id}/push
```

### 手动触发采集

```bash
curl -X POST http://localhost:8080/api/v1/collect
```

更多 API 详见 `http://localhost:8080/docs`

## 配置说明

### 分栏配置 (`config/columns.yaml`)

```yaml
columns:
  - id: "headlines"
    name: "🔥 今日头条"
    enabled: true
    max_items: 5
    sources:
      - type: "rss"
        name: "TechCrunch"
        url: "https://techcrunch.com/feed/"
        filter:
          keywords: ["AI", "人工智能"]
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | None |
| `DATABASE_URL` | 数据库连接 URL | sqlite:///data/daily.db |
| `DEFAULT_PUSH_TIME` | 每日推送时间 | 09:00 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | None |
| `SLACK_BOT_TOKEN` | Slack Bot Token | None |

## 项目结构

```
.
├── src/
│   ├── collector/      # 采集模块
│   ├── processor/      # 处理模块
│   ├── filter/         # 筛选排序模块
│   ├── output/         # 输出模块
│   ├── personalization/# 个性化模块
│   ├── config.py       # 配置管理
│   ├── database.py     # 数据库模型
│   ├── models.py       # 数据模型
│   ├── scheduler.py    # 任务调度
│   ├── service.py      # 业务服务
│   └── main.py         # FastAPI 入口
├── config/
│   └── columns.yaml    # 分栏配置
├── data/               # 数据目录
├── tests/              # 测试
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 推送渠道配置

### Telegram

1. 创建 Bot: [@BotFather](https://t.me/botfather)
2. 获取 Chat ID: [@userinfobot](https://t.me/userinfobot)
3. 配置环境变量

### Slack

1. 创建 App: [Slack API](https://api.slack.com/apps)
2. 添加 `chat:write` 权限
3. 安装到工作区并获取 Bot Token

### Discord

1. 创建 Bot: [Discord Developer](https://discord.com/developers/applications)
2. 获取 Bot Token
3. 获取频道 ID（右键频道 -> 复制 ID）

## 开发计划

- [x] 基础采集 (RSS/API)
- [x] 内容处理 (清洗/摘要)
- [x] 筛选排序 (去重/排序)
- [x] 多格式输出
- [x] Chat 渠道适配
- [x] 用户画像
- [ ] 网页采集增强 (Playwright)
- [ ] 智能推荐算法
- [ ] 多语言支持
- [ ] 管理后台 UI

## 许可证

MIT License
