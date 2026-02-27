# Daily Agent - 你的个性化智能日报

> 自动从多源信息渠道采集、智能筛选、生成个性化日报，推送到你指定的渠道。

---

## 🚀 5 分钟快速开始

### 方式一：Docker（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily

# 2. 运行诊断，确保环境就绪
python -m src.cli doctor

# 3. 选择启动方式

# 方式 A: Fast 模式（零配置，推荐首次体验）
STARTUP_MODE=fast docker-compose up -d

# 方式 B: 使用预设模板
SETUP_TEMPLATE=tech_developer docker-compose up -d

# 方式 C: 先本地配置，再挂载到容器（推荐日常使用）
# 先在本地运行配置向导，然后启动容器
python -m src.cli setup wizard  # 完成配置（支持智能模板推荐）
docker-compose up -d            # 启动容器（配置自动挂载）

# 4. 查看日志
docker-compose logs -f
```

### 方式二：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/uhajivis-cell/openclaw-skills-daily.git
cd openclaw-skills-daily

# 2. 创建环境
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 启动（首次启动会进入交互式配置）
python -m src.cli start

# 或直接使用 uvicorn（跳过交互配置）
uvicorn src.main:app --reload
```

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 **交互式登录** | 支持小红书等平台的浏览器自动登录，自动检测登录成功 |
| 🛡️ **反检测** | 注入反检测脚本，绕过平台的自动化检测 |
| 🔐 **安全存储** | Cookie/Token 使用 Fernet 加密，密钥派生自配置 |
| 📰 **智能日报** | 多源采集 → 智能筛选 → 个性化排序 → 多格式输出 |
| 🎯 **个性化** | 用户画像 + 兴趣偏好 + 反馈学习 |
| ⏰ **定时推送** | 支持每日定时生成和推送到多种渠道 |

---

## ⚡ 双模式启动

首次启动时，系统会检测配置状态并引导你选择：

| 模式 | 启动时间 | 特点 | 适合场景 |
|------|----------|------|----------|
| **Fast 模式** | 30 秒 | 零配置开箱即用，使用默认模板 | 快速体验、临时使用 |
| **Configure 模式** | 3-5 分钟 | 完整交互式配置，个性化设置 | 日常使用、深度定制 |

### 跳过交互，直接启动

```bash
# Fast 模式（零配置）
python -m src.cli start --mode fast

# Configure 模式（完整配置向导）
python -m src.cli start --mode configure

# 使用预设模板启动
python -m src.cli start --template tech_developer
```

### Docker 环境变量启动

```bash
# Fast 模式
docker run -e STARTUP_MODE=fast daily-agent

# 使用预设模板
docker run -e SETUP_TEMPLATE=product_manager daily-agent
```

---

## 📝 配置流程（Configure 模式）

首次启动进入 Configure 模式后，按提示完成 5 步配置：

### Step 1: 用户画像
```
👤 用户画像
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 您当前从事的行业是？
   [1] 互联网/科技  [2] 金融/投资  [3] 咨询/商业分析
   [4] 媒体/内容创作 [5] 学术研究 [6] 其他

请选择 [1-6]: 1

📝 您的职位或角色是？
   [1] 技术开发者  [2] 产品经理  [3] 创业者/高管
   [4] 投资人/分析师 [5] 其他

请选择 [1-5]: 2
```

### Step 2: 兴趣偏好
```
🎯 兴趣偏好
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 选择配置方式：
   [1] 🚀 快速配置 - 选择预设模板（推荐）
   [2] 🎨 自定义配置 - 详细设置每一项

请选择 [1-2]: 1

📝 选择预设模板：
   [1] 👨‍💻 技术开发者  [2] 💼 产品经理
   [3] 💰 投资人     [4] 📊 商业分析师
   [5] 🎨 设计师     [6] 📰 综合资讯

请选择 [1-6]: 2
```

### Step 3: 日报设置
```
📰 日报设置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 日报风格选择：
   [1] 📰 新闻简报型  [2] 📖 深度阅读型
   [3] 💬 对话简报型  [4] 📊 数据驱动型

请选择 [1-4]: 2

📝 日报分栏设置（按需启用/调整条数）：
   [x] 🔥 今日头条 - 3条
   [x] 🤖 AI/技术 - 5条
   [x] 💰 商业/投资 - 3条
   [ ] 🛠️ 产品/工具 - 2条
   [ ] 📚 深度阅读 - 1条
```

### Step 4: LLM 配置（可选）
```
🤖 LLM 配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 选择 LLM 提供商：
   [1] 🌐 OpenAI (推荐)
   [2] 🔗 OpenRouter
   [3] 🏠 Ollama (本地)
   [4] 🌙 Kimi (Moonshot)
   [5] 🔷 通义千问
   [6] 🔶 智谱 GLM
   [7] ⏭️  跳过

请选择 [1-7]: 1

请输入 OpenAI API Key: sk-xxxxxxxxxxxxxxxx

✅ API Key 验证通过！
```

### Step 5: 推送渠道（可选）
```
📤 推送渠道
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 选择推送渠道：
   [ ] Telegram
   [ ] Slack
   [ ] Discord
   [ ] Email
   [x] 暂不配置（可后续设置）

配置完成后，系统会自动生成第一份日报！
```

---

## 🎮 日常使用

### 生成日报

```bash
# 生成今日日报
python -m src.cli generate

# 指定日期生成
python -m src.cli generate --date 2024-01-15

# 推送到指定渠道
python -m src.cli push <report_id> --channel telegram
```

### 查看与管理

```bash
# 查看系统状态
python -m src.cli status

# 查看当前配置
python -m src.cli config show

# 导出配置（备份/迁移）
python -m src.cli config export --output my-config.yaml

# 导入配置
python -m src.cli config import my-config.yaml
```

### 诊断与测试

```bash
# 一键诊断系统状态
python -m src.cli doctor

# 自动修复发现的问题
python -m src.cli fix

# 预览今日日报（不保存）
python -m src.cli preview

# 测试单个数据源
python -m src.cli test source "Hacker News"

# 测试推送渠道
python -m src.cli test channel telegram

# 测试 LLM 连接
python -m src.cli test llm
```

### 配置管理

```bash
# 查看所有数据源
python -m src.cli config sources

# 编辑配置文件
python -m src.cli config edit

# 验证配置
python -m src.cli config validate
```

### 重新配置

```bash
# 完整重新配置
python -m src.cli setup --all

# 仅修改特定模块
python -m src.cli setup --module profile      # 用户画像
python -m src.cli setup --module interests    # 兴趣偏好
python -m src.cli setup --module daily        # 日报设置
python -m src.cli setup --module llm          # LLM 配置
python -m src.cli setup --module channels     # 推送渠道
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
- **社交媒体**: 
  - B站（热门/搜索）
  - 知乎（热榜/搜索）
  - 即刻（需认证）
  - 小红书（公开内容/关注流需认证）

配置修改后热更新（无需重启）：
```bash
curl -X POST http://localhost:8080/api/v1/reload
```

---

## 🔐 私有渠道认证

对于需要登录的渠道（即刻、小红书、知乎等），提供两种配置方式：

### 方式一：浏览器自动登录（推荐小红书）

小红书等平台的交互式浏览器登录，自动获取并加密存储 Cookie：

```bash
# 小红书 - 浏览器自动登录（自动检测登录成功）
python -m src.cli auth add xiaohongshu -b

# 其他平台（即刻、知乎等）
python -m src.cli auth add jike -b
python -m src.cli auth add zhihu -b
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
python -m src.cli auth add xiaohongshu -m
python -m src.cli auth add zhihu -m
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
python -m src.cli auth test xiaohongshu

# 删除认证
python -m src.cli auth remove xiaohongshu

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
│   │   ├── base.py               # 采集器基类
│   │   ├── xiaohongshu_collector.py  # 小红书采集器
│   │   ├── xiaohongshu_auth.py   # 小红书交互式鉴权（Playwright）
│   │   └── ...                   # 其他采集器
│   ├── processor/                # 处理模块（清洗/摘要/分类）
│   ├── filter/                   # 筛选排序模块
│   ├── output/                   # 输出模块（格式化/推送）
│   ├── personalization/          # 个性化模块（画像/学习）
│   ├── auth_manager.py           # 认证管理（Cookie/Token 加密）
│   ├── browser_auth.py           # 浏览器自动化认证
│   ├── cli.py                    # 命令行工具
│   └── main.py                   # FastAPI 入口
├── config/                       # 配置文件
│   ├── columns.yaml              # 日报分栏配置
│   └── templates.yaml            # 用户画像模板
├── docs/                         # 文档
│   └── XIAOHONGSHU_AUTH.md       # 小红书鉴权详细文档
├── data/                         # 数据目录（SQLite）
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
python -m src.cli generate --user alice
python -m src.cli generate --user bob

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

### 小红书认证采集

配置小红书认证后，采集关注流内容：

```bash
# 1. 配置小红书认证（浏览器自动登录）
python -m src.cli auth add xiaohongshu -b

# 2. 在 config/columns.yaml 中添加关注流数据源
#    collector: xiaohongshu_feed
#    auth_source: xiaohongshu

# 3. 手动触发采集测试
python -m src.cli collect
```

更多详情参见 [docs/XIAOHONGSHU_AUTH.md](docs/XIAOHONGSHU_AUTH.md)

---

## ❓ 常见问题

**Q: Fast 模式和 Configure 模式有什么区别？**

A: Fast 模式 30 秒零配置启动，使用默认模板，适合快速体验；Configure 模式提供完整个性化配置，3-5 分钟完成，适合日常使用。

**Q: 如何切换到 Configure 模式？**

A: 运行 `python -m src.cli setup --mode configure` 随时进入完整配置向导。

**Q: 可以不配置 LLM 吗？**

A: 可以。系统会使用规则摘要，但智能摘要、质量评估等功能不可用。

**Q: 如何添加自定义 RSS 源？**

A: 编辑 `config/columns.yaml`，在对应分栏下添加 `type: rss` 的数据源即可。

**Q: 推送失败怎么排查？**

A: 使用 `python -m src.cli auth test <channel>` 测试渠道连接，或查看日志 `docker-compose logs -f`。

**Q: 小红书认证失败怎么办？**

A: 1) 确保已安装 Playwright: `pip install playwright && python -m playwright install chromium`
2) 使用浏览器自动登录: `python -m src.cli auth add xiaohongshu -b`
3) 如果浏览器登录失败，可尝试手动方式: `python -m src.cli auth add xiaohongshu -m`

**Q: 为什么小红书需要特殊处理？**

A: 小红书有严格的反爬机制，普通 HTTP 请求容易被拦截。交互式浏览器登录可以：
- 模拟真实用户行为
- 自动处理反检测
- 获取完整的登录态 Cookie

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**快速开始 → [5 分钟快速开始](#-5-分钟快速开始)** | **配置详情 → [配置流程](#-配置流程configure-模式)** | **API 文档 → `http://localhost:8080/docs`**
