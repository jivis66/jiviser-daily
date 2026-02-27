# AGENTS.md

## 项目概述

本项目是一个**能力图谱（Capability Map）**文档仓库，定义了构建「完美个性化日报信息收集 Agent」所需的核心能力集合。该 Agent 旨在为用户提供智能、高效、个性化的日报信息收集服务。

**项目名称**: openclaw-skills-daily  
**项目语言**: 中文  
**许可证**: MIT License  
**仓库性质**: 文档/规范仓库（非代码实现仓库）

## 文档结构

```
.
├── README.md                   # 项目简介（极简）
├── perfect-daily-agent.md      # 核心文档：能力图谱详细定义
├── LICENSE                     # MIT 许可证
├── AGENTS.md                   # 本文件：项目指南
└── .gitignore                  # Python 项目标准的 gitignore
```

## 核心文档说明

### perfect-daily-agent.md

这是项目的主要文档，包含以下 8 大能力维度：

1. **信息收集能力** - 多源信息获取、实时与批量采集、数据解析与清洗
2. **个性化能力** - 用户画像构建、兴趣偏好学习、自适应调整
3. **内容理解与处理** - 自然语言理解、内容摘要生成、信息结构化
4. **信息筛选与排序** - 智能去重、重要性评估、智能排序
5. **输出与呈现** - 多格式输出、可视化展示、多终端适配、推送策略
6. **交互与反馈** - 用户反馈收集、交互式定制、智能问答、多模态交互
7. **系统与工程能力** - 架构设计、数据存储、性能与可靠性、安全与隐私
8. **智能化能力** - 机器学习应用、大语言模型集成、持续学习优化、智能工作流

### 技术栈参考

文档中推荐的技术栈包括：

| 层级 | 推荐技术 |
|------|----------|
| **采集** | Scrapy、Playwright、Celery、Apache Kafka |
| **存储** | PostgreSQL、MongoDB、Redis、Elasticsearch、Pinecone |
| **处理** | Python、spaCy、Hugging Face Transformers、LangChain |
| **模型** | OpenAI API、Claude、开源 LLM (Llama、Qwen) |
| **服务** | FastAPI、Docker、Kubernetes、Nginx |
| **前端** | React/Vue、React Native、Electron |

## 演进路线

文档定义了 5 个演进阶段：

1. **Phase 1**: 基础采集 → 简单过滤 → 定时推送
2. **Phase 2**: 多源聚合 → 自动摘要 → 基础个性化
3. **Phase 3**: 智能推荐 → 用户画像 → 多格式输出
4. **Phase 4**: LLM 增强 → 智能问答 → 持续学习
5. **Phase 5**: 多模态 → 预测性推荐 → 生态集成

## 开发规范

### 文档语言
- 所有核心文档使用**简体中文**编写
- 技术术语保留英文（如 LLM、API、NER 等）

### 文档格式
- 使用 Markdown 格式
- 使用表格展示对比信息
- 使用代码块展示 JSON 结构和架构图
- 使用 emoji 增强可读性（📋、🎯、🚀 等）

### 内容组织
- 每个能力维度包含：能力项说明、示例/应用场景、技术参考
- 提供能力评估矩阵（基础版/进阶版/专业版）

## 贡献指南

由于这是一个规范/文档仓库：

1. **修改能力定义**: 编辑 `perfect-daily-agent.md`
2. **更新项目信息**: 编辑 `README.md`
3. **添加实现代码**: 当前仓库为纯文档仓库，如需添加实现代码，建议：
   - 创建子目录（如 `implementations/`）存放不同语言/框架的实现
   - 或使用 git submodule 链接到具体实现仓库

## 相关链接

- 项目主页: https://github.com/uhajivis-cell/openclaw-skills-daily
- 核心文档: `perfect-daily-agent.md`

## 注意事项

1. 本仓库**不包含实际可运行的代码**，仅包含能力规范定义
2. 如需基于此规范进行实现，建议创建新的代码仓库
3. `.gitignore` 使用 Python 项目标准模板，为未来可能的 Python 实现预留

---

*本文档面向 AI 编程助手，用于快速理解本项目的目的和结构。*
