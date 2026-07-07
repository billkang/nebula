---
name: sse-message-streaming-brainstorming
description: 将前端消息轮询替换为 SSE 实时推送
---

# Brainstorming Session — SSE 消息实时推送

**日期：** 2026-07-06
**Change：** sse-message-streaming

## 讨论主题

将 Nebula Chat 页面的消息获取方式从短轮询（`refetchInterval: 2000`）替换为 SSE（Server-Sent Events）实时推送。

## 关键决策

- 采用 SSE 而非 WebSocket — 单向消息推送场景 SSE 已够用，实现更简单
- 仅在 Chat 页替换，不影响其他页面
- 利用 EventSource 内置自动重连机制，不做额外容错
- 后端使用 StreamingResponse + 心跳保活（30s 间隔）

## 需求要点

- 后端新增 SSE 端点 `GET /.../sessions/{session_id}/messages/stream`
- 后端新增事件总线，消息写入后通知 SSE 连接
- 后端鉴权增加 `token` query param 支持（EventSource 无法设置 Authorization header）
- 前端 Chat.tsx 用 EventSource 替代 useQuery + refetchInterval

## 边界范围（不做）

- 不做 WebSocket 方案
- 不改造其他页面（Docs、Sandbox 等无消息轮询）
- 不做消息历史增量同步（SSE 每次推送全量消息列表）
- 不做 SSE 自定义重连策略（使用 EventSource 默认行为）

## 后续步骤

1. 生成 SDD 文档（proposal → specs → design → tasks）
2. spec-hardener 过筛
3. 生成实现计划
4. TDD 实现
