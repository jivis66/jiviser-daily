# Daily Agent 快速开始指南

> 5 分钟完成配置，开始你的个性化日报之旅

---

## 🚀 首次使用流程

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: 环境检查                                                │
│  ─────────────────────────────────────────────────────────────   │
│  $ python -m src.cli doctor                                      │
│                                                                  │
│  检查 Python 版本、依赖、配置等是否完整                           │
│  如有问题，运行: python -m src.cli fix                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: 运行配置向导                                            │
│  ─────────────────────────────────────────────────────────────   │
│  $ python -m src.cli setup wizard                                │
│                                                                  │
│  1. 选择配置方式: 智能推荐 / 手动选择 / 自定义                    │
│  2. 输入你的兴趣关键词（如：AI 编程 创业）                        │
│  3. 系统将推荐最适合的模板                                        │
│  4. 配置推送渠道（可选）                                          │
│  5. 配置 LLM（可选，用于智能摘要）                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: 预览日报                                                │
│  ─────────────────────────────────────────────────────────────   │
│  $ python -m src.cli preview                                     │
│                                                                  │
│  查看今日采集的内容，不保存到数据库                               │
│  用于验证配置是否正确                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: 生成正式日报                                            │
│  ─────────────────────────────────────────────────────────────   │
│  $ python -m src.cli generate                                    │
│                                                                  │
│  采集内容、智能筛选、生成日报、保存到数据库                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: 推送日报（可选）                                        │
│  ─────────────────────────────────────────────────────────────   │
│  $ python -m src.cli push <report_id> --channel telegram         │
│                                                                  │
│  将生成的日报推送到 Telegram/Slack/Discord/Email                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 常用命令速查表

| 场景 | 命令 |
|------|------|
| **系统诊断** | `python -m src.cli doctor` |
| **自动修复** | `python -m src.cli fix` |
| **配置向导** | `python -m src.cli setup wizard` |
| **查看配置** | `python -m src.cli config sources` |
| **编辑配置** | `python -m src.cli config edit` |
| **预览日报** | `python -m src.cli preview` |
| **生成日报** | `python -m src.cli generate` |
| **推送日报** | `python -m src.cli push <id> --channel telegram` |
| **测试数据源** | `python -m src.cli test source "Hacker News"` |
| **测试推送** | `python -m src.cli test channel telegram` |
| **查看状态** | `python -m src.cli status` |

---

## 🎯 智能推荐示例

```bash
$ python -m src.cli setup wizard

🎯 智能模板推荐
告诉我们你关注哪些话题，我们会为你推荐最合适的配置

📝 输入你关注的关键词（空格分隔）: AI 编程 创业

✨ 根据你的兴趣，推荐以下模板：

┌─────────────────────────────────────────┐
│ [1] 🧠 AI 研究员 (匹配度: 95%)           │
│ 专注 AI 研究、学术论文、前沿技术          │
│ 匹配: AI, 编程                          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ [2] 👨‍💻 技术开发者 (匹配度: 80%)         │
│ 专注技术趋势、开源项目、编程实践          │
│ 匹配: 编程, AI                          │
└─────────────────────────────────────────┘

请选择: 1

✅ 已选择: 🧠 AI 研究员
```

---

## 🔧 故障排查流程

遇到问题？按以下步骤排查：

### 1. 运行诊断
```bash
python -m src.cli doctor
```

### 2. 根据诊断结果修复
```bash
# 如果是依赖问题
python -m src.cli fix

# 如果是配置问题
python -m src.cli config validate
python -m src.cli config edit
```

### 3. 测试具体组件
```bash
# 测试数据源
python -m src.cli test source "数据源名称"

# 测试推送渠道
python -m src.cli test channel telegram

# 测试 LLM
python -m src.cli test llm
```

### 4. 常见问题

**Q: 采集失败怎么办？**
```bash
# 测试具体数据源
python -m src.cli test source "TechCrunch"

# 检查数据源配置
python -m src.cli config sources
```

**Q: 推送失败怎么办？**
```bash
# 测试推送渠道
python -m src.cli test channel telegram

# 验证配置
python -m src.cli doctor
```

**Q: 如何重新配置？**
```bash
# 重置配置
python -m src.cli config reset

# 重新运行向导
python -m src.cli setup wizard
```

---

## 📚 进阶功能

### 定时日报

系统默认每日 9:00 自动生成并推送日报。

修改推送时间：
```bash
# 编辑 .env 文件
python -m src.cli config edit --file env

# 修改 DEFAULT_PUSH_TIME=09:00
```

### 多用户支持

```bash
# 为用户 alice 生成日报
python -m src.cli generate --user alice

# 查看用户配置
python -m src.cli config show --user alice
```

### 导出/导入配置

```bash
# 导出配置（备份）
python -m src.cli config export --output my-config.yaml

# 导入配置（迁移）
python -m src.cli config import my-config.yaml
```

---

## 💡 最佳实践

1. **首次使用前运行诊断**：`python -m src.cli doctor`
2. **使用智能推荐**：输入兴趣关键词，让系统推荐模板
3. **先预览再生成**：使用 `preview` 验证配置
4. **定期运行诊断**：每周运行一次 `doctor` 检查系统健康
5. **测试新数据源**：添加新源后先用 `test source` 测试

---

**开始你的 Daily Agent 之旅吧！** 🚀
