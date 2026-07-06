# 星云 · Nebula — CLAUDE.md

## 项目简介

**星云 (Nebula)** 是一个 AI Agent 中台平台。

核心定位：**不造轮子**。把业务需求翻译成 Agent 开发指令，调度成熟工具（Claude Code 等）完成交付。让产品经理像点将一样驱动 Agent 军团。

> "星云深处，万物始生。"
> *Where stars are born.*

---

## 命名由来

星云（Nebula）是天文学中恒星的摇篮——星际气体与尘埃在引力作用下凝聚、坍缩，最终诞生出新的恒星。

这与星云平台的使命完美对应：平台是"恒星孕育所"。项目需求就是星云中的原始物质，在平台的引力下凝聚成型，最终诞生出可独立运行的代码——一颗颗"恒星"。

---

## 命名规范

| 上下文 | 名称 | 示例 |
|--------|------|------|
| 中文文档/对内 | 星云 | 星云平台、星云构建引擎 |
| 英文代码/域名/包名 | Nebula | nebula-api, @nebula/engine |

- 代码中所有命名用英文（PascalCase / camelCase / kebab-case 按语言惯例）
- 文档、注释、Commit 用中文，技术关键词保留英文
- 不混用：Nebula 就是 Nebula，别缩写成 neb 或 nebula

---

## 架构概要

```
┌─────────────┐  ┌─────────────┐
│  构建引擎    │  │  运行时引擎  │
│ Build Engine │  │ Runtime     │
│              │  │              │
│ · PM 对话    │  │ · LangGraph │
│ · 文档生成   │  │ · MCP GW    │
│ · Skill 匹配 │  │ · A2A GW    │
│ · 编码调度   │  │ · 监控日志   │
└─────────────┘  └─────────────┘
```

核心协议：**MCP**（外部工具）、**A2A**（Agent 通信）

详见 [平台架构文档](../docs/agents/platform-architecture.md)

---

## 技术栈规划

| 层 | 技术 |
|---|---|
| 前端 | React |
| 后端 | Python |
| Agent 引擎 | LangGraph |
| 数据库 | PostgreSQL, Redis |
| 执行容器 | Docker (v1) → A2A (v2) |

---

## 代码风格

- Python：遵循 PEP 8，使用 type hints，用 `ruff` 格式化
- React：使用函数组件 + hooks
- 提交：中文 commit message，动词开头（"新增…" "修复…" "重构…"）
- 命名：英文 + 业务语义，不滥用缩写
- 文档：每个模块目录有 README，复杂逻辑写 docstring

---

## 常用命令

_待项目启动后补充_
