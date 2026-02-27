# AGENTS.md

## 项目概述

**Daily Agent** 是一个智能个性化日报信息收集系统，基于 [perfect-daily-agent.md](perfect-daily-agent.md) 能力图谱实现。该系统能够自动从多种数据源采集信息，通过 LLM 进行智能处理和摘要生成，根据用户画像进行个性化筛选和排序，最终输出多格式的日报内容。

**项目名称**: openclaw-skills-daily  
**项目语言**: 简体中文（代码注释和文档）  
**技术栈**: Python 3.11+ / FastAPI / SQLAlchemy  
**许可证**: MIT License

### 核心功能

- **多源采集**: RSS、API、社交媒体（B站、小红书、知乎等）、新闻媒体、播客
- **智能处理**: 内容清洗、关键词提取、主题分类、LLM 摘要生成
- **智能筛选**: 语义去重、多维度质量评分、个性化排序、多样性保证
- **多格式输出**: Markdown / HTML / JSON / Telegram / Slack / Discord / 邮件
- **个性化**: 用户画像构建、兴趣偏好学习、反馈驱动的持续优化
- **任务调度**: 支持定时生成和推送日报

## 技术栈

| 层级 | 技术 |
|------|------|
| **Web 框架** | FastAPI 0.104, Uvicorn 0.24 |
| **数据验证** | Pydantic 2.5, Pydantic-Settings 2.1 |
| **数据库** | SQLite + SQLAlchemy 2.0 (异步) + aiosqlite |
| **HTTP/采集** | httpx 0.25, aiohttp 3.9, feedparser 6.0, BeautifulSoup 4.12 |
| **任务调度** | APScheduler 3.10 |
| **NLP/文本** | jieba, scikit-learn 1.3, markdown, markdownify |
| **配置管理** | python-dotenv, PyYAML, ruamel.yaml |
| **CLI/UI** | Click 8.1, Rich 13.7 |
| **安全** | cryptography 41.0 |
| **测试** | pytest 7.4, pytest-asyncio |

## 项目结构

```
.
├── src/                          # 源代码目录
│   ├── collector/                # 采集模块
│   │   ├── base.py               # 采集器基类和管理器
│   │   ├── base_auth_collector.py # 带认证的采集器基类
│   │   ├── rss_collector.py      # RSS 采集器
│   │   ├── api_collector.py      # API 采集器（HN、GitHub 等）
│   │   ├── bilibili_collector.py # B站采集器
│   │   ├── xiaohongshu_collector.py # 小红书采集器
│   │   ├── zhihu_collector.py    # 知乎采集器
│   │   ├── jike_collector.py     # 即刻采集器
│   │   ├── podcast_collector.py  # 播客采集器（小宇宙、喜马拉雅等）
│   │   ├── caixin_collector.py   # 财新采集器
│   │   ├── intl_news_collector.py # 国际新闻（Bloomberg、Reuters等）
│   │   └── ...                   # 其他平台采集器
│   ├── processor/                # 内容处理模块
│   │   ├── cleaner.py            # 内容清洗（HTML 净化）
│   │   ├── extractor.py          # 信息提取（关键词、主题分类）
│   │   └── summarizer.py         # 摘要生成（抽取式/生成式）
│   ├── filter/                   # 筛选排序模块
│   │   ├── deduper.py            # 去重算法（语义/精确）
│   │   ├── ranker.py             # 排序算法
│   │   └── selector.py           # 内容选择器
│   ├── output/                   # 输出模块
│   │   ├── formatter.py          # 格式转换（Markdown/HTML）
│   │   └── publisher.py          # 推送发布（Telegram/Slack/Discord/邮件）
│   ├── personalization/          # 个性化模块
│   │   ├── profile.py            # 用户画像管理
│   │   └── learning.py           # 学习算法（反馈处理）
│   ├── main.py                   # FastAPI 应用入口
│   ├── service.py                # 核心业务服务（采集-处理-生成-推送流程）
│   ├── models.py                 # Pydantic 数据模型
│   ├── database.py               # SQLAlchemy 数据库模型和仓库
│   ├── config.py                 # 配置管理（环境变量 + YAML）
│   ├── scheduler.py              # 任务调度器（APScheduler 封装）
│   ├── cli.py                    # 命令行工具
│   ├── auth_manager.py           # 认证管理（Cookie/Token 加密存储）
│   ├── llm_config.py             # LLM 配置管理
│   └── setup_wizard.py           # 交互式设置向导
├── config/                       # 配置文件目录
│   ├── columns.yaml              # 日报分栏配置
│   ├── templates.yaml            # 用户画像模板
│   └── sources_example.yaml      # 数据源配置示例
├── tests/                        # 测试目录
│   ├── test_collector.py         # 采集器测试
│   └── test_processor.py         # 处理器测试
├── data/                         # 数据目录（SQLite 数据库、缓存）
├── docker-compose.yml            # Docker Compose 配置
├── Dockerfile                    # Docker 镜像构建
├── requirements.txt              # Python 依赖
├── start.sh                      # 启动脚本
├── .env.example                  # 环境变量示例
└── pytest.ini                   # pytest 配置
```

## 构建和运行

### 环境准备

```bash
# 1. 克隆仓库
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的 API 密钥
```

### 方式一：Docker（推荐生产环境）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：本地运行

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（开发模式，带热重载）
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# 或使用启动脚本
./start.sh dev
```

### 验证服务

```bash
# 健康检查
curl http://localhost:8080/health

# API 文档
open http://localhost:8080/docs  # Swagger UI
open http://localhost:8080/redoc # ReDoc
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_collector.py
pytest tests/test_processor.py

# 带覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试配置

测试配置位于 `pytest.ini`：
- 使用 `pytest-asyncio` 支持异步测试
- 测试文件命名规则: `test_*.py`
- 测试类命名规则: `Test*`
- 测试函数命名规则: `test_*`

## 配置说明

### 环境变量 (.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_NAME` | 应用名称 | DailyAgent |
| `DEBUG` | 调试模式 | false |
| `LOG_LEVEL` | 日志级别 (debug/info/warning/error) | info |
| `HOST` / `PORT` | 服务监听地址/端口 | 0.0.0.0 / 8080 |
| `DATABASE_URL` | SQLite 数据库路径 | sqlite:///data/daily.db |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `OPENAI_BASE_URL` | 自定义 API 地址（可选） | - |
| `OPENAI_MODEL` | 默认模型 | gpt-4o-mini |
| `MAX_CONCURRENT_COLLECTORS` | 并发采集数 | 5 |
| `REQUEST_DELAY` | 请求间隔（秒） | 1.0 |
| `DEFAULT_PUSH_TIME` | 默认推送时间 | 09:00 |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Telegram 配置 | - |
| `SLACK_BOT_TOKEN` / `SLACK_CHANNEL` | Slack 配置 | - |
| `API_SECRET_KEY` | API 安全密钥 | change-this-secret-key |

### 分栏配置 (config/columns.yaml)

定义日报的各个分栏和数据源：

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
          keywords: ["AI", "人工智能"]
    organization:
      sort_by: "relevance"
      dedup_strategy: "semantic"
      summarize: "3_points"
```

配置支持热更新：通过 API `POST /api/v1/reload` 重新加载配置，无需重启服务。

## CLI 工具

项目提供丰富的命令行工具：

```bash
# 生成日报
python -m src.cli generate --user default

# 指定日期生成
python -m src.cli generate --user default --date 2024-01-15

# 推送日报
python -m src.cli push <report_id> --channel telegram --channel slack

# 手动触发采集
python -m src.cli collect

# 验证配置
python -m src.cli verify

# 初始化数据库
python -m src.cli init

# 认证管理（配置需要登录的渠道）
python -m src.cli auth list          # 列出已配置的认证
python -m src.cli auth add jike      # 添加即刻认证
python -m src.cli auth test jike     # 测试认证

# LLM 配置
python -m src.cli llm setup          # 启动 LLM 配置向导
python -m src.cli llm test           # 测试 LLM 连接
python -m src.cli llm status         # 查看 LLM 配置状态

# 设置向导
python -m src.cli quickstart         # 快速开始（完整设置向导）
python -m src.cli setup templates    # 查看可用配置模板
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/reports/generate` | POST | 生成日报 |
| `/api/v1/reports/{id}` | GET | 获取日报（支持 format=markdown） |
| `/api/v1/reports` | GET | 获取日报列表 |
| `/api/v1/reports/{id}/push` | POST | 推送日报 |
| `/api/v1/contents` | GET | 获取内容列表 |
| `/api/v1/collect` | POST | 手动触发采集 |
| `/api/v1/feedback` | POST | 提交反馈 |
| `/api/v1/profile/{user_id}` | GET/PUT | 获取/更新用户画像 |
| `/api/v1/reload` | POST | 重新加载配置（热更新） |

## 代码风格指南

### Python 代码规范

1. **类型注解**: 所有函数参数和返回值必须使用类型注解
   ```python
   async def collect(self) -> CollectorResult:
       pass
   ```

2. **异步编程**: IO 操作必须使用 `async/await`，使用 `httpx.AsyncClient` 进行 HTTP 请求
   ```python
   async def fetch(self, url: str) -> Response:
       async with httpx.AsyncClient() as client:
           return await client.get(url)
   ```

3. **文档字符串**: 使用中文编写 docstring，说明函数功能、参数和返回值
   ```python
   async def collect(self) -> CollectorResult:
       """
       执行采集
       
       Returns:
           CollectorResult: 采集结果
       """
   ```

4. **命名规范**:
   - 类名: `PascalCase` (如 `BaseCollector`, `ContentItem`)
   - 函数/变量: `snake_case` (如 `collect_all`, `content_items`)
   - 常量: `UPPER_SNAKE_CASE`
   - 私有成员: 前缀 `_` (如 `_client`, `_initialize`)

5. **导入排序**:
   - 标准库导入
   - 第三方库导入
   - 本地模块导入（使用 `src.` 前缀）

6. **错误处理**: 使用 try-except 捕获特定异常，避免裸 except
   ```python
   try:
       result = await collector.collect()
   except httpx.HTTPError as e:
       logger.error(f"HTTP 错误: {e}")
   ```

### 模块组织

- 每个模块在 `__init__.py` 中导出公共接口
- 使用 `__all__` 明确指定公开 API
- 按功能分层：collector / processor / filter / output / personalization

## 架构设计

### 数据流

```
数据源 → 采集器(Collector) → 内容清洗(Cleaner) → 信息提取(Extractor)
                                                         ↓
用户 ← 推送(Publisher) ← 格式化(Formatter) ← 筛选排序(Selector/Ranker)
                                                         ↓
                                              摘要生成(Summarizer) ← LLM
```

### 核心类

1. **DailyAgentService** (`service.py`): 核心业务服务，编排整个流程
2. **BaseCollector** (`collector/base.py`): 采集器基类，所有采集器继承此类
3. **ContentProcessor** (`processor/summarizer.py`): 内容处理主类
4. **ContentSelector** (`filter/selector.py`): 内容筛选选择器
5. **Publisher** (`output/publisher.py`): 推送发布器

### 数据库模型

- **ContentItemDB**: 内容条目表，存储采集的原始内容
- **DailyReportDB**: 日报表，存储生成的日报
- **DailyReportItemDB**: 日报-内容关联表
- **UserProfileDB**: 用户画像表
- **UserFeedbackDB**: 用户反馈表
- **AuthCredentialDB**: 认证凭证表（加密存储）

## 安全注意事项

1. **API 密钥管理**:
   - 所有密钥存储在 `.env` 文件，禁止提交到版本控制
   - 使用 `mask_sensitive_data()` 函数对日志中的敏感信息进行脱敏
   - `.env` 文件权限设置为 `0o600`（仅所有者可读写）

2. **认证凭证加密**:
   - 使用 Fernet 对称加密存储 Cookie/Token
   - 加密密钥从 `API_SECRET_KEY` 派生
   - 支持凭证过期自动检测和提醒

3. **数据库安全**:
   - 默认使用 SQLite，数据存储在本地 `data/` 目录
   - 数据库文件应在备份时加密

4. **部署安全**:
   - Docker 容器以非 root 用户运行（推荐）
   - 生产环境必须修改默认的 `API_SECRET_KEY`
   - 使用 HTTPS 反向代理（Nginx/Caddy）

## 开发计划

已完成功能：
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

待开发功能：
- [ ] Playwright 网页采集增强
- [ ] 智能问答交互
- [ ] 管理后台 Web UI
- [ ] 多租户支持
- [ ] 多语言界面

## 相关链接

- 项目主页: https://github.com/uhajivis-cell/openclaw-skills-daily
- 能力图谱文档: [perfect-daily-agent.md](perfect-daily-agent.md)
- API 文档: http://localhost:8080/docs (服务启动后)
