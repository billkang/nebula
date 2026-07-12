## ADDED Requirements

### Requirement: SSE 消息实时推送
系统 SHALL 提供 SSE 端点，在消息变更时实时推送消息列表，替代前端定时轮询。

#### Scenario: SSE 连接建立
- **WHEN** 前端发起 `GET /api/v1/projects/{project_id}/sessions/{session_id}/messages/stream`
- **THEN** 后端返回 `Content-Type: text/event-stream` 的 StreamingResponse
- **AND** 鉴权支持通过 `token` query param 传入 JWT

#### Scenario: 新消息到达时推送
- **WHEN** 任意角色（user/agent）在 session 中新增消息
- **THEN** SSE 连接收到 `data: [...]` 事件，内容为全量消息列表
- **AND** 消息列表格式与 `GET /messages` 一致

#### Scenario: 空闲心跳保活
- **WHEN** SSE 连接持续 30 秒无新消息
- **THEN** 服务端发送 `: heartbeat\n\n` 注释行保持连接
- **AND** 浏览器/代理不因超时关闭连接

#### Scenario: 客户端断开连接
- **WHEN** 客户端关闭 SSE 连接（页面关闭、导航离开）
- **THEN** 服务端结束 StreamingResponse
- **AND** 不产生错误日志

#### Scenario: EventSource 自动重连
- **WHEN** 网络中断导致 SSE 连接断开
- **THEN** EventSource 自动发起重连（浏览器默认行为）
- **AND** 重连后立即收到当前全量消息列表

## 验证方法

| # | 测试函数 | 场景 | 方法 |
|---|---------|------|------|
| 1 | `test_sse_connection_established` | SSE 连接建立 | `client.get("/stream", ...)` → assert 200 + content-type `text/event-stream` |
| 2 | `test_sse_initial_push` | 连接后初始推送 | assert SSE stream 的首个事件包含当前消息列表（JSON array） |
| 3 | `test_sse_push_on_new_message` | 新消息推送 | `POST /messages` 发消息 → assert SSE stream 中下一个事件是更新后的全量消息 |
| 4 | `test_sse_heartbeat` | 空闲 30s 心跳 | mock EventBus.wait() 始终超时 → assert stream 中每隔 30s 出现 `: heartbeat` |
| 5 | `test_sse_error_recovery` | DB 异常后恢复 | mock get_messages 首次抛异常 → assert `event: error` → 恢复后重新推送正常数据 |
| 6 | `test_sse_client_disconnect` | 客户端断开 | 关闭 stream client → assert generator 正确退出（无资源泄漏） |
| 7 | `test_sse_auth_token_query_param` | token query param 鉴权 | `GET /stream?token=xxx` → assert 200；无 token → assert 401 |
