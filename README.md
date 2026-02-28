# Daily Agent - 你的个性化智能日报

> 自动从多源信息渠道采集、智能筛选、生成个性化日报，推送到你指定的渠道。

---

## 🚀 5 分钟快速开始

### 方式一：简化 CLI（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily

# 2. 创建环境
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 首次运行（自动进入初始化向导）
python daily.py

# 常用命令
python daily.py --preview     # 预览日报（不保存）
python daily.py --date 2024-01-15  # 指定日期
python daily.py send          # 推送最新日报
python daily.py check         # 系统检查
python daily.py sources       # 查看所有数据源
```

### 方式二：Docker

```bash
# 1. 克隆仓库
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily

# 2. 运行诊断，确保环境就绪
python daily.py check

# 3. 选择启动方式

# 方式 A: Fast 模式（零配置，推荐首次体验）
STARTUP_MODE=fast docker-compose up -d

# 方式 B: 使用预设模板
SETUP_TEMPLATE=tech_developer docker-compose up -d

# 方式 C: 先本地配置，再挂载到容器（推荐日常使用）
# 先在本地运行配置向导，然后启动容器
python daily.py --init        # 完成配置（支持智能模板推荐）
docker-compose up -d          # 启动容器（配置自动挂载）

# 4. 查看日志
docker-compose logs -f
```

### 方式三：本地运行（高级）

```bash
# 1. 克隆仓库
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily

# 2. 创建环境
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 启动 FastAPI 服务
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🚀 **简化 CLI** | 直观的 `python daily.py` 命令，零门槛使用 |
| 🇨🇳 **中文优化** | 支持 30+ 国内信息源（科技媒体、社区、生活方式） |
| 🤖 **智能摘要** | LLM 驱动的内容摘要和质量评估 |
| 🔐 **认证采集** | 支持即刻、知乎等平台的认证采集（浏览器自动登录） |
| 📰 **智能日报** | 多源采集 → 智能筛选 → 个性化排序 → 多格式输出 |
| 🎯 **个性化** | 用户画像 + 兴趣偏好 + 反馈学习 |
| ⏰ **定时推送** | 支持每日定时生成和推送到多种渠道 |

---

## ⚡ 三种配置模式

首次运行 `python daily.py` 时，系统会检测配置状态并引导你选择：

| 模式 | 启动时间 | 特点 | 适合场景 |
|------|----------|------|----------|
| **快速模式** | 30 秒 | 零配置开箱即用，使用默认模板 | 快速体验、临时使用 |
| **智能模式** | 2-3 分钟 | AI 辅助配置，了解兴趣后自动推荐 | 推荐日常使用 |
| **专家模式** | 5-10 分钟 | 完全手动控制所有配置选项 | 深度定制需求 |

### 初始化命令

```bash
# 进入初始化向导
python daily.py --init

# 或指定具体模式
python daily.py --init fast    # 快速模式
python daily.py --init smart   # 智能模式
python daily.py --init expert  # 专家模式
```

### Docker 环境变量启动

```bash
# Fast 模式
docker run -e STARTUP_MODE=fast daily-agent

# 使用预设模板
docker run -e SETUP_TEMPLATE=product_manager daily-agent
```

---

## 📝 配置流程（智能模式）

首次运行 `python daily.py` 时，系统会引导你完成配置：

### 交互式初始化

```bash
$ python daily.py

欢迎使用 Daily Agent !

你的个性化智能日报助手

主要功能:
• 自动从多源采集信息（RSS、API、社交媒体）
• 智能筛选和摘要（支持 LLM）
• 个性化排序（基于你的兴趣）
• 多格式输出（Markdown、Telegram、Slack、邮件）

首次使用，请选择配置方式:

请选择配置模式:

  1. 快速模式 (推荐首次体验)
     30 秒完成，使用默认模板

  2. 智能模式 (推荐日常使用)
     AI 辅助配置，了解你的兴趣后自动推荐

  3. 专家模式 (深度定制)
     完全手动控制所有配置选项

请选择 [1-3]: 2
```

### 智能模式流程

智能模式会询问你的职业和兴趣，然后 AI 自动为你推荐最佳配置：

```
🤖 AI 配置助手
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 请描述你的职业和兴趣（如：AI 产品经理，关注大模型、产品设计）

> 我是一名后端开发，关注云原生、微服务架构和开源项目

🤖 分析中...
   推荐模板: 后端开发者 (backend_dev)
   匹配度: 95%

📝 推荐的数据源:
   • 稀土掘金 - 后端技术
   • 开源中国 - 开源资讯
   • InfoQ - 架构设计
   • V2EX - 开发者社区

✅ 配置已生成！
```

---

## 🎮 日常使用（简化 CLI）

### 生成日报

```bash
# 生成今日日报（默认命令）
python daily.py

# 预览模式（不保存到数据库）
python daily.py --preview

# 生成指定日期的日报
python daily.py --date 2024-01-15

# 指定用户生成
python daily.py --user alice
```

### 推送日报

```bash
# 推送最新日报到所有配置渠道
python daily.py send

# 推送到指定渠道
python daily.py send --channel telegram
```

### 系统管理

```bash
# 系统检查和诊断
python daily.py check

# 查看当前配置
python daily.py config

# 编辑配置文件
python daily.py config edit

# 查看所有数据源
python daily.py sources
```

### 高级 CLI（完整功能）

如需更多高级功能，使用完整 CLI：

```bash
# 诊断与测试
python -m src.cli doctor
python -m src.cli preview
python -m src.cli test source "Hacker News"
python -m src.cli test channel telegram

# 配置管理
python -m src.cli config export --output my-config.yaml
python -m src.cli config import my-config.yaml
python -m src.cli setup --module llm

# 报告管理
python -m src.cli reports list
python -m src.cli reports view <report_id>
```

---

## 🔧 配置模板

系统内置 12 种预设模板，覆盖主流用户场景，支持**智能推荐**：

| 模板 ID | 名称 | 适合人群 | 核心关注 |
|---------|------|----------|----------|
| `tech_developer` | 👨‍💻 技术开发者 | 程序员、架构师 | 开源、AI、工具 |
| `product_manager` | 💼 产品经理 | PM、产品设计师 | 设计、增长、行业 |
| `investor` | 💰 投资人 | VC、PE、分析师 | 市场、融资、财报 |
| `business_analyst` | 📊 商业分析师 | 咨询、战略 | 行业研究、数据 |
| `designer` | 🎨 设计师 | UI/UX、创意 | 趋势、工具、灵感 |
| `ai_researcher` | 🧠 AI 研究员 | ML工程师、学者 | 论文、大模型、前沿 |
| `frontend_dev` | 🌐 前端开发者 | 前端工程师 | React/Vue、UI组件 |
| `backend_dev` | ⚙️ 后端开发者 | 后端工程师 | 架构、数据库、分布式 |
| `data_engineer` | 📈 数据工程师 | 数据工程师 | ETL、数据仓库、BI |
| `security_engineer` | 🔒 安全工程师 | 安全工程师 | 攻防、合规、隐私 |
| `entrepreneur` | 🚀 创业者 | 创始人、CEO | 融资、管理、增长 |
| `general` | 📰 综合资讯 | 大众用户 | 平衡资讯 |

**🎯 智能推荐**：配置向导会根据你的兴趣自动推荐最合适的模板
```bash
python -m src.cli setup wizard
# 输入关键词如：AI 编程 创业
# 系统将自动推荐匹配度最高的模板
```

使用指定模板启动：
```bash
python -m src.cli setup --template tech_developer
```

---

## 📡 推送渠道配置

### Telegram

1. 找 [@BotFather](https://t.me/botfather) 创建 Bot，获取 Token
2. 找 [@userinfobot](https://t.me/userinfobot) 获取 Chat ID
3. 配置环境变量或交互式输入

### Slack

1. 访问 [Slack API](https://api.slack.com/apps) 创建 App
2. 添加 `chat:write` 权限，安装到工作区
3. 复制 Bot Token（以 `xoxb-` 开头）

### Discord

1. 访问 [Discord Developer](https://discord.com/developers/applications) 创建 Bot
2. 获取 Bot Token，开启 `Send Messages` 权限
3. 右键频道 → 复制频道 ID

### 邮件

支持任意 SMTP 服务：
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Gmail 需使用应用专用密码
```

---

## 🇨🇳 中国信息源（Top 30+）

系统内置支持 30+ 中国主流信息渠道，覆盖科技、商业、社区、生活方式：

### 科技媒体
| 名称 | 类型 | 采集器 |
|------|------|--------|
| 稀土掘金 | 开发者社区 | `juejin` |
| 开源中国 | 开源资讯 | `oschina` |
| InfoQ中文 | 企业技术 | `infoq_cn` |
| 思否 | 开发者问答 | `segmentfault` |
| 雷锋网 | AI/科技 | `leiphone` |

### 商业媒体
| 名称 | 类型 | 采集器 |
|------|------|--------|
| 虎嗅 | 商业科技 | `huxiu` |
| 极客公园 | 产品创新 | `geekpark` |
| 品玩 | 科技新闻 | `pingwest` |
| 新浪科技 | 门户科技 | `sina_tech` |
| 网易科技 | 门户科技 | `netease_tech` |

### 社区
| 名称 | 类型 | 采集器 |
|------|------|--------|
| V2EX | 开发者社区 | `v2ex` |
| 雪球 | 投资社区 | `xueqiu` |
| 华尔街见闻 | 财经新闻 | `wallstreetcn` |
| ITPUB | IT社区 | `itpub` |
| 知乎 | 问答平台 | `zhihu` |
| 即刻 | 兴趣社交 | `jike` |

### 生活方式/工具
| 名称 | 类型 | 采集器 |
|------|------|--------|
| 少数派 | 效率工具 | `sspai` |
| 爱范儿 | 创新消费 | `ifanr` |
| 数字尾巴 | 数字生活 | `dgtle` |
| 小众软件 | 软件推荐 | `appinn` |
| 优设 | 设计资源 | `uisdc` |

---

## 🤖 LLM 配置建议

| 使用场景 | 推荐模型 | 获取方式 |
|----------|----------|----------|
| 日常摘要 | OpenAI gpt-4o-mini | [platform.openai.com](https://platform.openai.com) |
| 高质量摘要 | OpenAI gpt-4o / Claude 3.5 | [openrouter.ai](https://openrouter.ai) |
| 中文内容 | Kimi / 通义千问 | [platform.moonshot.cn](https://platform.moonshot.cn) |
| 隐私敏感 | Ollama 本地模型 | [ollama.com](https://ollama.com) |

快速配置：
```bash
# 查看 LLM 状态
python -m src.cli llm status

# 测试连接
python -m src.cli llm test

# 切换模型
python -m src.cli llm switch
```

---

## 📚 数据源配置

编辑 `config/columns.yaml` 自定义数据源：

```yaml
columns:
  - id: "headlines"
    name: "🔥 今日头条"
    max_items: 5
    sources:
      - type: "rss"
        name: "TechCrunch"
        url: "https://techcrunch.com/feed/"
        filter:
          keywords: ["AI", "人工智能"]

      - type: "api"
        name: "Hacker News"
        provider: "hackernews"
        filter:
          min_score: 100
```

支持的数据源类型：
- **RSS**: 任意 RSS/Atom 订阅源
- **API**: Hacker News、GitHub Trending、NewsAPI 等
- **中国科技媒体**: 稀土掘金、开源中国、InfoQ中文、思否、雷锋网
- **中国商业媒体**: 虎嗅、极客公园、品玩、新浪科技、网易科技
- **中国社区**: V2EX、雪球、华尔街见闻、ITPUB、ChinaUnix
- **生活方式/工具**: 少数派、爱范儿、数字尾巴、小众软件
- **社交媒体**: B站、知乎、即刻（部分需认证）

配置修改后热更新（无需重启）：
```bash
curl -X POST http://localhost:8080/api/v1/reload
```

---

## 🔐 私有渠道认证

对于需要登录的渠道（即刻、知乎、B站等），提供两种配置方式：

### 方式一：浏览器自动登录（推荐）

交互式浏览器登录，自动获取并加密存储 Cookie：

```bash
# 即刻 - 浏览器自动登录
python -m src.cli auth add jike -b

# 知乎
python -m src.cli auth add zhihu -b

# B站
python -m src.cli auth add bilibili -b
```

流程：启动浏览器 → 用户完成登录 → 自动提取 Cookie → 加密保存到数据库

特点：
- ✅ 自动检测登录成功（无需手动按 Enter）
- ✅ 反检测脚本（隐藏自动化特征）
- ✅ Cookie 加密存储
- ✅ 支持扫码/手机号/验证码登录

**依赖要求**（首次使用）：
```bash
pip install playwright
python -m playwright install chromium
```

### 方式二：手动粘贴 cURL

适用于所有平台：

```bash
# 添加认证（手动模式）
python -m src.cli auth add jike -m
python -m src.cli auth add zhihu -m
python -m src.cli auth add bilibili -m
```

Cookie 获取方式：
1. 浏览器登录目标网站（如 [web.okjike.com](https://web.okjike.com)）
2. F12 打开开发者工具 → Network 标签
3. 刷新页面，找到任意 API 请求
4. 右键 → Copy → Copy as cURL
5. 粘贴到 CLI 提示中

### 认证管理命令

```bash
# 列出已配置的认证
python -m src.cli auth list

# 测试认证状态
python -m src.cli auth test jike

# 删除认证
python -m src.cli auth remove jike

# 查看认证配置指南
python -m src.cli auth guide
```

---

## 🖥️ Web 界面

Daily Agent 提供友好的 Web 界面，无需命令行即可完成配置和管理。

### 配置向导

访问 `http://localhost:8080/setup`

**功能**:
- 🎯 智能模板推荐（输入关键词自动推荐）
- 👤 可视化用户画像配置
- 🤖 LLM 配置
- 📤 推送渠道设置

### 监控面板

访问 `http://localhost:8080/dashboard`

**功能**:
- 📊 实时统计（今日采集/本周日报/数据源状态）
- 📡 数据源健康监控
- 📰 最近日报列表
- 🔄 30秒自动刷新

### 日报管理

```bash
# 列出历史日报
python -m src.cli reports list

# 查看日报详情
python -m src.cli reports view <report_id>

# 对比两份日报
python -m src.cli reports diff <id1> <id2>

# 导出日报
python -m src.cli reports export <report_id> --output report.md

# 性能统计
python -m src.cli reports stats
```

### 规则测试

```bash
# 测试分栏过滤规则
python -m src.cli test rules --column headlines

# 测试数据源过滤规则
python -m src.cli test rules --source "TechCrunch"
```

---

## 🌐 API 接口

服务启动后访问 API 文档：`http://localhost:8080/docs`

常用接口：

```bash
# 生成日报
curl -X POST http://localhost:8080/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "default", "columns": ["headlines", "tech"]}'

# 获取日报（Markdown 格式）
curl "http://localhost:8080/api/v1/reports/{id}?format=markdown"

# 推送日报
curl -X POST http://localhost:8080/api/v1/reports/{id}/push \
  -H "Content-Type: application/json" \
  -d '{"channels": ["telegram"]}'

# 提交反馈
curl -X POST http://localhost:8080/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"item_id": "xxx", "feedback_type": "positive"}'
```

---

## 📁 项目结构

```
.
├── src/                          # 源代码
│   ├── collector/                # 采集模块
│   │   ├── base.py               # 采集器基类（v1）
│   │   ├── base_v2.py            # 采集器基类（v2，推荐新采集器使用）
│   │   ├── base_auth_collector.py # 认证采集器基类
│   │   ├── rss_collector.py      # RSS 采集器
│   │   ├── api_collector.py      # API 采集器
│   │   ├── china_tech_collector.py      # 中国科技媒体（掘金/开源中国/InfoQ等）
│   │   ├── china_media_collector.py     # 中国商业媒体（虎嗅/极客公园/品玩等）
│   │   ├── china_community_collector.py # 中国社区（V2EX/雪球等）
│   │   ├── quality_life_collector.py    # 生活方式/工具媒体（少数派/爱范儿等）
│   │   ├── zhihu_collector.py    # 知乎采集器
│   │   ├── jike_collector.py     # 即刻采集器
│   │   ├── bilibili_collector.py # B站采集器
│   │   └── ...                   # 其他采集器
│   ├── processor/                # 处理模块（清洗/摘要/分类）
│   │   ├── batch_llm.py          # 批量 LLM 处理
│   │   └── cache.py              # 处理结果缓存
│   ├── filter/                   # 筛选排序模块
│   ├── output/                   # 输出模块（格式化/推送）
│   ├── personalization/          # 个性化模块（画像/学习）
│   ├── auth_manager.py           # 认证管理（Cookie/Token 加密）
│   ├── browser_auth.py           # 浏览器自动化认证
│   ├── daily.py                  # 简化版 CLI（主要入口）
│   ├── cli.py                    # 完整功能 CLI
│   ├── main.py                   # FastAPI 入口
│   ├── service.py                # 核心服务逻辑
│   ├── config.py                 # 配置管理
│   ├── database.py               # 数据库模型和仓库
│   └── progress.py               # 进度显示和错误处理
├── config/                       # 配置文件
│   ├── columns.yaml              # 日报分栏配置（中国用户优化版）
│   └── templates.yaml            # 用户画像模板
├── data/                         # 数据目录（SQLite）
├── daily.py                      # 简化 CLI 入口（调用 src/daily.py）
├── docker-compose.yml            # Docker 部署
└── requirements.txt              # Python 依赖
```

---

## ⚙️ 环境变量

完整环境变量参考 `.env.example`，常用配置：

```bash
# 基础配置
DEBUG=false
LOG_LEVEL=info
PORT=8080

# LLM 配置
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# 推送配置
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_CHANNEL=#daily

# 采集配置
MAX_CONCURRENT_COLLECTORS=5
CONTENT_RETENTION_DAYS=30
```

---

## 🛠️ 高级使用

### 定时任务

系统内置 APScheduler，默认每日 9:00 自动生成并推送日报。

修改推送时间：
```bash
# 配置文件中修改
python -m src.cli setup --module daily
# 或设置环境变量
DEFAULT_PUSH_TIME=08:00
```

### 多用户支持

```bash
# 为不同用户生成日报
python daily.py --user alice
python daily.py --user bob

# 查看指定用户配置
python -m src.cli config show --user alice
```

### 配置迁移

```bash
# 导出用户 A 的配置
python -m src.cli config export --user alice --output alice-config.yaml

# 导入到用户 B
python -m src.cli config import alice-config.yaml --user bob
```

### 即刻认证采集

配置即刻认证后，采集关注流内容：

```bash
# 1. 配置即刻认证（浏览器自动登录）
python -m src.cli auth add jike -b

# 2. 在 config/columns.yaml 中添加关注流数据源
#    collector: jike_feed
#    auth_source: jike

# 3. 手动触发采集测试
python -m src.cli collect
```

---

## ❓ 常见问题

**Q: 快速模式、智能模式、专家模式有什么区别？**

A: 快速模式 30 秒零配置启动，使用默认模板；智能模式使用 AI 了解你的兴趣后自动推荐配置；专家模式提供完全手动控制，适合深度定制。

**Q: 如何重新配置？**

A: 运行 `python daily.py --init` 随时进入配置向导。

**Q: 可以不配置 LLM 吗？**

A: 可以。系统会使用规则摘要，但智能摘要、质量评估等功能不可用。

**Q: 如何添加自定义 RSS 源？**

A: 编辑 `config/columns.yaml`，在对应分栏下添加 `type: rss` 的数据源即可。

**Q: 推送失败怎么排查？**

A: 使用 `python daily.py check` 运行系统检查，或查看日志 `docker-compose logs -f`。

**Q: 即刻/知乎认证失败怎么办？**

A: 1) 确保已安装 Playwright: `pip install playwright && python -m playwright install chromium`
2) 使用浏览器自动登录: `python -m src.cli auth add jike -b`
3) 如果浏览器登录失败，可尝试手动方式: `python -m src.cli auth add jike -m`

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**快速开始 → [5 分钟快速开始](#-5-分钟快速开始)** | **配置详情 → [配置流程](#-配置流程智能模式)** | **API 文档 → `http://localhost:8080/docs`**
