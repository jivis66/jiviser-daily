# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Daily Agent** is a personalized daily news aggregation system that automatically collects information from multiple sources, processes and summarizes content using LLM, filters and ranks based on user profiles, and outputs to multiple channels (Telegram, Slack, Discord, Email).

- **Language**: Python 3.11+
- **Framework**: FastAPI with SQLAlchemy 2.0 (async)
- **Database**: SQLite (async via aiosqlite)
- **Key Dependencies**: httpx, feedparser, pydantic, click, rich, openai, playwright

### China Information Sources (中国信息源)

This project includes extensive support for Chinese information sources:

**Tech Media (科技媒体):**
- 稀土掘金 (Juejin) - Developer community
- 开源中国 (OSChina) - Open source news
- InfoQ中文 - Enterprise technology
- 思否 (SegmentFault) - Developer Q&A

**Business Media (商业媒体):**
- 虎嗅 (Huxiu) - Business and tech news
- 雷锋网 (Leiphone) - AI and technology
- 品玩 (PingWest) - Tech news
- 极客公园 (GeekPark) - Product and innovation
- 新浪科技 / 网易科技 - Portal tech news

**Communities (社区):**
- V2EX - Developer community
- 雪球 (Xueqiu) - Investment community
- 华尔街见闻 - Financial news
- ITPUB / ChinaUnix - IT communities

**Quality Lifestyle/Tools (优质生活方式/工具):**
- 少数派 (Sspai) - Efficiency tools & digital lifestyle
- 爱范儿 (Ifanr) - Innovation & consumer tech
- AppSo - App recommendations
- 小众软件 (Appinn) - Niche software discovery
- 利器 (Liqi) - Tools used by creators
- 数字尾巴 (Dgtle) - Digital lifestyle
- 优设 (Uisdc) - Design resources
- 理想生活实验室 (Toodaylab) - Creative lifestyle

**Video Platforms:**
- Bilibili - Tech and education videos

**Social Media:**
- 知乎 (Zhihu) - Q&A platform
- 即刻 (Jike) - Interest-based social
- 微信公众号 (WeChat Channels)

Configuration in `config/columns.yaml` is optimized for Chinese users by default.

## Quick Start (Simplified CLI)

### New Simplified Commands

```bash
# Run daily report (default command)
python daily.py
python daily.py --preview     # Preview without saving
python daily.py --date 2024-01-15  # Specific date

# Initialization (3 modes)
python daily.py --init        # Interactive mode selection

# Management commands
python daily.py send          # Push latest report
python daily.py check         # System diagnostics
python daily.py config        # View/edit config
python daily.py sources       # List all sources
```

### Legacy CLI (Advanced)

```bash
# Full-featured CLI with all commands
python -m src.cli doctor
python -m src.cli setup expert
# ... see src/cli.py for all commands
```

### Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# Preview daily report (no save)
python -m src.cli preview

# Generate daily report
python -m src.cli generate

# Generate for specific date
python -m src.cli generate --date 2024-01-15

# Push report to channels
python -m src.cli push <report_id> --channel telegram

# Test specific components
python -m src.cli test source "Hacker News"
python -m src.cli test channel telegram
python -m src.cli test llm

# Authentication management (for protected sources like 小红书/即刻/知乎)
python -m src.cli auth add xiaohongshu -b    # Browser auto-login
python -m src.cli auth add jike -m           # Manual cURL paste
python -m src.cli auth list
python -m src.cli auth test xiaohongshu

# Configuration
python -m src.cli config sources
python -m src.cli config edit
python -m src.cli config validate
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_collector.py
pytest tests/test_processor.py

# With coverage
pytest --cov=src --cov-report=html
```

### Docker

```bash
# Fast mode (zero-config)
STARTUP_MODE=fast docker-compose up -d

# With template
SETUP_TEMPLATE=tech_developer docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Architecture

### Data Flow

```
Data Sources → Collectors → Content Processor → Filter/Selector → Formatter → Publisher
                  ↓               ↓
            SQLite DB        LLM Summarization
```

### Core Components

1. **DailyAgentService** (`src/service.py`)
   - Main orchestrator class
   - `initialize()` - Register collectors
   - `collect_all()` - Fetch from all sources
   - `generate_daily_report()` - Full pipeline execution
   - `push_report()` - Send to channels

2. **Collectors** (`src/collector/`)
   - `BaseCollector` - Abstract base class with HTTP client
   - `CollectorManager` - Manages all collectors, runs concurrent collection
   - Implementations: RSSCollector, HackerNewsCollector, BilibiliCollector, etc.
   - `base_auth_collector.py` - For sources requiring authentication (小红书, 即刻, 知乎)
   - `browser_auth.py` - Playwright-based authentication with anti-detection

3. **Content Processing** (`src/processor/`)
   - `ContentProcessor` - Main orchestrator
   - `cleaner.py` - HTML cleaning
   - `extractor.py` - Keyword/entity/topic extraction
   - `summarizer.py` - LLM-based and extractive summarization
   - `batch_llm.py` - Concurrent LLM processing

4. **Filtering & Ranking** (`src/filter/`)
   - `deduper.py` - Semantic and exact deduplication
   - `ranker.py` - Quality and relevance scoring
   - `selector.py` - Content selection per column

5. **Output** (`src/output/`)
   - `formatter.py` - Markdown/HTML/Chat formatters
   - `publisher.py` - Multi-channel publishing (Telegram/Slack/Discord/Email)

6. **Database** (`src/database.py`)
   - SQLAlchemy 2.0 async models
   - Key tables: ContentItemDB, DailyReportDB, UserProfileDB, AuthCredentialDB
   - Repository pattern for data access

7. **Scheduling** (`src/scheduler.py`, `src/scheduler_manager.py`)
   - APScheduler for daily report generation
   - DailyTaskManager - Core scheduling logic
   - SchedulerManager - Web UI management

### Configuration System

- **Environment Variables** (`.env`): Loaded via Pydantic Settings in `src/config.py`
- **Column Config** (`config/columns.yaml`): Defines report sections and data sources
- **Hot Reload**: `POST /api/v1/reload` reloads column config without restart

### Expert Mode (LLM Assisted)

Expert mode configures LLM first, then uses AI to help complete all other configurations through conversation:

```bash
python -m src.cli expert
# or
python -m src.cli setup expert
```

**Flow**:
1. Configure LLM (provider, API key, model)
2. AI asks about your profession and interests
3. AI analyzes and recommends configuration
4. AI generates `columns.yaml` automatically

**Benefits**:
- No need to understand YAML structure
- AI explains each configuration option
- Natural language configuration
- Smart recommendations based on your profile

### Authentication Flow

For platforms requiring login (小红书, 即刻, 知乎):

1. Browser mode (`-b` flag): Playwright launches Chromium with anti-detection scripts
2. User completes login manually (QR code, phone, etc.)
3. Auto-detection monitors cookies for successful login
4. Cookies encrypted with Fernet and stored in SQLite (`AuthCredentialDB`)
5. Subsequent requests use stored credentials

### Key Code Patterns

**Async SQLAlchemy Pattern**:
```python
from src.database import get_session

async with get_session() as session:
    repo = ContentRepository(session)
    items = await repo.get_by_status("pending")
```

**Collector Implementation**:
```python
class MyCollector(BaseCollector):
    def __init__(self, name: str, config: dict):
        super().__init__(name, SourceType.RSS, config)

    async def collect(self) -> CollectorResult:
        # Use self.client (httpx.AsyncClient)
        response = await self.fetch_url(url)
        # Create items with self.create_content_item()
        items = [self.create_content_item(title, url, content)]
        return CollectorResult(items=items)
```

**Type Annotations**: All functions must have type annotations.
**Docstrings**: Use Chinese for docstrings.
**Naming**: PascalCase for classes, snake_case for functions/variables.

## Project Structure

```
src/
├── main.py              # FastAPI entry, lifespan management
├── service.py           # DailyAgentService - core business logic
├── cli.py               # Click CLI commands
├── config.py            # Pydantic Settings, ColumnConfig
├── database.py          # SQLAlchemy models & repositories
├── models.py            # Pydantic data models
├── scheduler.py         # APScheduler daily tasks
├── auth_manager.py      # Credential encryption/decryption
├── browser_auth.py      # Playwright authentication
├── llm_config.py        # LLM provider configuration
├── collector/           # Data collection modules
├── processor/           # Content processing
├── filter/              # Deduplication & ranking
├── output/              # Formatting & publishing
└── personalization/     # User profiles & learning

config/
├── columns.yaml         # Report sections & sources
└── templates.yaml       # User profile templates

tests/
├── test_collector.py
└── test_processor.py
```

## Important Notes

- **Async First**: All I/O operations use async/await. Use `httpx.AsyncClient`, not requests.
- **Session Management**: Each database operation should use `async with get_session()` to avoid long-lived sessions.
- **ContentItem ID**: Generated from URL hash: `f"{source_type}_{md5(url)[:12]}"`
- **JSON Fields**: Database stores JSON as strings; use `parse_json_list()` when reading.
- **Sensitive Data**: API keys and credentials are masked in logs via `mask_sensitive_data()`.
- **Batch Processing**: LLM operations use `batch_llm.py` for concurrent processing to improve performance.

### Progress Display and Error Handling

The codebase includes enhanced progress display and error handling:

```python
from src.progress import ProgressManager, ErrorHandler

# Show progress bar
with ProgressManager("Processing...") as pm:
    for i, item in enumerate(items):
        process(item)
        pm.update(i + 1, len(items))

# Handle errors with suggestions
ErrorHandler.handle(e, "Context message")
ErrorHandler.success("Operation completed")
ErrorHandler.warning("Something might be wrong")
```

### Collector Base Classes (V2)

New simplified collector base classes in `src/collector/base_v2.py`:

```python
from src.collector import BaseCollectorV2, CollectContext

class MyCollector(BaseCollectorV2):
    async def _do_collect(self, context: CollectContext) -> List[ContentItem]:
        # Simpler error handling and progress reporting
        items = []
        for data in await self.fetch_data():
            item = self._parse(data)
            if item:
                items.append(item)
            context.report_progress("Processing", len(items), total)
        return items
```
