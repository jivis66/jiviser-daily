# AGENTS.md

## 项目概述

**Daily Agent**（完美个性化日报信息收集 Agent）是一个基于 Python 的智能日报生成系统，能够自动从多源采集信息、智能处理内容、个性化筛选排序，并通过多渠道推送定制化日报。

**项目名称**: openclaw-skills-daily  
**项目语言**: 简体中文  
**技术栈**: Python 3.11+, FastAPI, SQLAlchemy, APScheduler  
**许可证**: MIT License

### 核心功能

- **多源采集**: RSS、API（Hacker News、GitHub 等）、网页爬虫、社交媒体（B站、小红书）、新闻媒体
- **智能处理**: 内容清洗、关键词提取、主题分类、自动摘要（支持 LLM 增强）
- **智能筛选**: 语义去重、质量评分、个性化排序、多样性保证
- **多格式输出**: Markdown、HTML、邮件、Telegram、Slack、Discord
- **个性化**: 用户画像构建、兴趣学习、冷启动模板
- **定时任务**: 支持定时生成和推送日报

---

## 技术架构

### 技术栈详情

| 层级 | 技术选型 |
|------|----------|
| **Web 框架** | FastAPI 0.104.1 + Uvicorn 0.24.0 |
| **数据验证** | Pydantic 2.5.0 + pydantic-settings 2.1.0 |
| **数据库** | SQLite + SQLAlchemy 2.0.23 + aiosqlite 0.19.0 |
| **HTTP/爬虫** | httpx 0.25.2 + aiohttp 3.9.1 + BeautifulSoup4 4.12.2 + feedparser 6.0.10 |
| **任务调度** | APScheduler 3.10.4 |
| **NLP/文本** | scikit-learn 1.3.2 + markdown 3.5.1 + Jinja2 3.1.2 |
| **LLM 集成** | OpenAI API / OpenRouter（可选） |
| **CLI/工具** | Click 8.1.7 + Rich 13.7.0 + tenacity 8.2.3 |
| **测试** | pytest 7.4.3 + pytest-asyncio 0.21.1 |
| **部署** | Docker + Docker Compose |

### 项目结构

```
.
├── src/                          # 主源代码目录
│   ├── collector/               # 采集模块（~40 个采集器）
│   │   ├── base.py              # 采集器基类和管理器
│   │   ├── rss_collector.py     # RSS 采集器
│   │   ├── api_collector.py     # API 采集器（HN、GitHub）
│   │   ├── bilibili_collector.py    # B站采集器
│   │   ├── xiaohongshu_collector.py # 小红书采集器
│   │   ├── caixin_collector.py      # 财新采集器
│   │   ├── yicai_collector.py       # 第一财经采集器
│   │   ├── jiemian_collector.py     # 界面采集器
│   │   ├── ftchinese_collector.py   # FT中文网采集器
│   │   ├── zhihu_collector.py       # 知乎采集器
│   │   ├── jike_collector.py        # 即刻采集器
│   │   ├── podcast_collector.py     # 播客采集器
│   │   └── ...
│   ├── processor/               # 处理模块
│   │   ├── cleaner.py           # 内容清洗（HTML 清理）
│   │   ├── extractor.py         # 关键词/实体提取
│   │   └── summarizer.py        # 文本摘要（规则/LLM）
│   ├── filter/                  # 筛选排序模块
│   │   ├── deduper.py           # 内容去重（语义/精确）
│   │   ├── ranker.py            # 内容排序算法
│   │   └── selector.py          # 内容选择器
│   ├── output/                  # 输出模块
│   │   ├── formatter.py         # 格式转换（MD/HTML/Chat）
│   │   └── publisher.py         # 多渠道推送
│   ├── personalization/         # 个性化模块
│   │   ├── profile.py           # 用户画像管理
│   │   └── learning.py          # 兴趣学习算法
│   ├── config.py                # 配置管理（Pydantic Settings）
│   ├── database.py              # 数据库模型和仓库（SQLAlchemy 2.0）
│   ├── models.py                # Pydantic 数据模型
│   ├── scheduler.py             # 任务调度器（APScheduler）
│   ├── service.py               # 核心业务服务
│   ├── main.py                  # FastAPI 入口
│   ├── cli.py                   # 命令行工具
│   └── __init__.py
├── config/                      # 配置文件目录
│   ├── columns.yaml             # 分栏配置（数据源定义）
│   └── sources_example.yaml     # 数据源配置示例
├── data/                        # 数据目录（gitignored）
│   ├── cache/                   # 缓存文件
│   ├── daily.db                 # SQLite 数据库
│   ├── exports/                 # 导出文件
│   └── logs/                    # 日志文件
├── tests/                       # 测试目录
│   ├── test_collector.py        # 采集器测试
│   └── test_processor.py        # 处理器测试
├── docker-compose.yml           # Docker Compose 配置
├── Dockerfile                   # Docker 镜像定义
├── start.sh                     # 启动脚本
├── pytest.ini                  # pytest 配置
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量示例
├── .env                        # 环境变量（gitignored）
├── .gitignore                  # Git 忽略规则
├── README.md                   # 项目说明
└── AGENTS.md                   # 本文件
```

---

## 构建和运行

### 环境要求

- Python 3.11+
- Docker 和 Docker Compose（可选）

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件配置必要参数
```

最小配置（仅运行基础功能）：
```bash
# 可选：配置 LLM 以获得更好的摘要效果
OPENAI_API_KEY=sk-your-api-key

# 可选：配置推送渠道
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 启动方式

#### 方式一：Docker（推荐生产环境）

```bash
# 使用启动脚本
./start.sh docker

# 或直接使用 docker-compose
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 方式二：开发模式

```bash
# 使用启动脚本
./start.sh dev

# 或直接运行
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

#### 方式三：生产模式

```bash
# 使用启动脚本
./start.sh

# 或直接运行
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### 验证服务

```bash
curl http://localhost:8080/health
```

### 命令行工具

```bash
# 验证配置
python -m src.cli verify

# 初始化数据库
python -m src.cli init

# 手动触发采集
python -m src.cli collect

# 生成日报
python -m src.cli generate --user default

# 推送日报
python -m src.cli push <report_id> --channel telegram
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_collector.py
pytest tests/test_processor.py

# 详细输出
pytest -v

# 带覆盖率
pytest --cov=src --cov-report=html
```

### 测试配置

测试配置位于 `pytest.ini`：
- 异步模式：auto
- 测试路径：tests/
- 文件模式：test_*.py
- 详细输出 + 简短 traceback

---

## 代码规范

### 代码风格

- **语言**: 所有代码注释和文档使用简体中文
- **命名规范**: 
  - 类名：PascalCase（如 `ContentItem`）
  - 函数/变量：snake_case（如 `fetch_url`）
  - 常量：UPPER_CASE
- **类型注解**: 全项目使用 Python 类型注解
- **异步**: 大量使用 async/await 模式
- **文档字符串**: 所有公共类和函数都包含中文文档字符串

### 模块组织规范

1. **采集器**: 继承 `BaseCollector`，实现 `collect()` 方法
2. **数据库模型**: 使用 SQLAlchemy 2.0 声明式语法（`Mapped`, `mapped_column`）
3. **Pydantic 模型**: 用于 API 请求/响应验证
4. **错误处理**: 使用 try/except 配合日志输出，关键操作使用 tenacity 重试

### 导入规范

```python
# 标准库
import asyncio
from datetime import datetime
from typing import List, Optional

# 第三方库
from fastapi import FastAPI
from sqlalchemy import select

# 项目内部
from src.config import get_settings
from src.models import ContentItem
```

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_NAME` | 应用名称 | DailyAgent |
| `DEBUG` | 调试模式 | false |
| `LOG_LEVEL` | 日志级别 | info |
| `HOST` | 服务绑定地址 | 0.0.0.0 |
| `PORT` | 服务端口 | 8080 |
| `DATABASE_URL` | 数据库 URL | sqlite:///data/daily.db |
| `OPENAI_API_KEY` | OpenAI API 密钥 | None |
| `OPENAI_MODEL` | LLM 模型 | gpt-4o-mini |
| `MAX_CONCURRENT_COLLECTORS` | 最大并发采集数 | 5 |
| `REQUEST_DELAY` | 请求间隔（秒） | 1.0 |
| `DEFAULT_PUSH_TIME` | 默认推送时间 | 09:00 |
| `TIMEZONE` | 时区 | Asia/Shanghai |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | None |
| `SLACK_BOT_TOKEN` | Slack Bot Token | None |
| `DISCORD_BOT_TOKEN` | Discord Bot Token | None |
| `SMTP_HOST` | SMTP 服务器 | None |
| `API_SECRET_KEY` | API 访问密钥 | change-this-secret-key |

### 分栏配置 (`config/columns.yaml`)

分栏配置定义了日报的结构和数据源：

```yaml
columns:
  - id: "headlines"
    name: "🔥 今日头条"
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

---

## API 接口

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/v1/reports/generate` | 生成日报 |
| GET | `/api/v1/reports` | 获取日报列表 |
| GET | `/api/v1/reports/{id}` | 获取日报详情 |
| POST | `/api/v1/reports/{id}/push` | 推送日报 |
| GET | `/api/v1/contents` | 获取内容列表 |
| POST | `/api/v1/collect` | 手动触发采集 |
| POST | `/api/v1/feedback` | 提交反馈 |
| GET | `/api/v1/profile/{user_id}` | 获取用户画像 |
| PUT | `/api/v1/profile/{user_id}` | 更新用户画像 |
| POST | `/api/v1/reload` | 重新加载配置 |

### API 文档

启动服务后访问：`http://localhost:8080/docs`（Swagger UI）

---

## 数据库模型

### 核心表

1. **content_items** - 内容条目表
   - 存储采集的原始内容
   - 包含标题、URL、内容、摘要、评分等

2. **daily_reports** - 日报表
   - 存储生成的日报
   - 包含日期、用户ID、统计信息等

3. **daily_report_items** - 日报-内容关联表
   - 多对多关系
   - 记录内容在日报中的顺序和分栏

4. **user_profiles** - 用户画像表
   - 存储用户兴趣和偏好
   - JSON 字段存储列表数据

5. **user_feedback** - 用户反馈表
   - 存储点赞、收藏、屏蔽等反馈

---

## 部署指南

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 停止服务
docker-compose down
```

### 数据持久化

Docker 部署时挂载以下卷：
- `./data:/app/data` - 数据库和缓存
- `./config:/app/config` - 配置文件

### 健康检查

服务包含健康检查端点：
- HTTP: `GET /health`
- Docker: 每 30 秒自动检查

---

## 安全注意事项

1. **API 密钥保护**
   - `.env` 文件包含敏感信息，已添加到 `.gitignore`
   - 生产环境务必修改 `API_SECRET_KEY`

2. **数据脱敏**
   - `config.py` 中包含 `mask_sensitive_data()` 函数
   - 日志会自动脱敏敏感字段（token, secret, password, key 等）

3. **请求限流**
   - 采集器使用 `asyncio.Semaphore` 限制并发
   - 配置 `REQUEST_DELAY` 控制请求间隔
   - 使用 tenacity 实现指数退避重试

4. **数据库**
   - 当前仅支持 SQLite（文件级）
   - 生产环境建议定期备份 `data/daily.db`

---

## 扩展开发

### 添加新采集器

1. 在 `src/collector/` 创建新文件
2. 继承 `BaseCollector`
3. 实现 `collect()` 方法
4. 在 `src/collector/__init__.py` 导出
5. 在 `service.py` 中注册

示例：
```python
from src.collector.base import BaseCollector, CollectorResult
from src.models import SourceType

class MyCollector(BaseCollector):
    def __init__(self, name: str, config: dict):
        super().__init__(name, SourceType.CUSTOM, config)
    
    async def collect(self) -> CollectorResult:
        # 实现采集逻辑
        pass
```

### 添加新推送渠道

1. 在 `src/output/publisher.py` 添加新的 Publisher 类
2. 实现 `publish()` 方法
3. 在 `Publisher` 类中注册

---

## 故障排查

### 常见问题

1. **数据库初始化失败**
   - 检查 `data/` 目录权限
   - 运行 `python -m src.cli init`

2. **采集失败**
   - 检查网络连接
   - 查看 `data/logs/` 日志
   - 验证数据源配置

3. **推送失败**
   - 验证推送渠道配置（Token、Chat ID 等）
   - 检查目标渠道权限

4. **LLM 摘要失败**
   - 验证 `OPENAI_API_KEY` 是否有效
   - 检查 API 配额

---

## 相关文档

- `README.md` - 快速开始指南
- `perfect-daily-agent.md` - 能力图谱详细定义（演进路线图）
- `.env.example` - 环境变量完整示例

---

*本文档面向 AI 编程助手，用于快速理解和开发本项目。*
