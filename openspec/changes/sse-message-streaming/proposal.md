## Why

Chat 页面当前使用 `refetchInterval: 2000`（每 2 秒轮询）获取消息，即使对话空闲也在持续请求。随着用户量增长，这种频繁轮询会产生大量无意义请求，增加服务器负载和网络开销。切换到 SSE（Server-Sent Events）后，服务端在新消息产生时才推送数据，空闲时零流量。

## What Changes

- 后端新增 SSE 端点 `/projects/{project_id}/sessions/{session_id}/messages/stream`，通过 `StreamingResponse` 保持长连接，有新消息时推送全量消息列表
- 后端新增事件总线（EventBus），消息写入时通知对应 SSE 连接
- 鉴权中间件增加 `token` query param 支持，用于 SSE 连接认证
- 前端 Chat.tsx 用 `EventSource` 替换 `useQuery` + `refetchInterval` 轮询

## Capabilities

### New Capabilities
- `sse-message-stream`: 基于 SSE 的消息实时推送，替代定时轮询

### Modified Capabilities
- （无现有 spec 被修改）

## Impact

| 领域 | 影响 |
|------|------|
| 后端 API | 新增 SSE 端点，新增 event_bus.py，修改 auth middleware |
| 前端 | Chat.tsx 改用 EventSource，移除 refetchInterval |
| 依赖 | 无新增依赖（StreamingResponse 来自 starlette 已有依赖） |

## Known Limitations

- **没有 polling 兜底** — 如果 SSE 因网络环境（企业代理过滤 text/event-stream）静默失败，用户不会收到新消息且无提示。v2 可加周期性 polling 做健康检查。
- **EventBus 纯内存** — 扩展到多进程时，进程 A 的 notify 无法通知进程 B 的 SSE 连接。v2 可用 Redis Pub/Sub 取代 in-process EventBus。
- **全量推送不扩展** — 长对话 session 积累大量消息时，每次推送全量 JSON 的开销线性增长。v2 可改为增量同步。
- **token query param 日志泄漏** — `?token=xxx` 可能出现在 access log、Referer header 中。仅影响 SSE 端点，但部署在公网环境时需关注。
- **notify 失败不重试** — DB commit 成功但 notify() 抛出异常时，消息已持久化但前端未收到推送。用户刷新页面即可恢复。
