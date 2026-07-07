## Context

Chat 页面当前使用 `@tanstack/react-query` 的 `refetchInterval: 2000` 轮询 `GET /messages`。每次轮询都会执行完整的 HTTP 请求 + 数据库查询 + 响应序列化，对话空闲时也在持续消耗资源。

SSE 是单向实时推送的轻量方案：服务端长连接推送数据，EventSource 浏览器 API 原生支持自动重连，不需要额外依赖。

## Architecture

```
Frontend (EventSource)                  Backend (StreamingResponse)
         │                                     │
         │  GET /.../messages/stream?token=xxx  │
         │─────────────────────────────────────>│
         │                                     │
         │  SSE: data: [...]                    │
         │<════════════════════════════════════│  ← 有新消息时推送
         │                                     │
         │  SSE: : heartbeat                    │
         │<════════════════════════════════════│  ← 空闲时每 30s 心跳
         │                                     │
```

**数据传输流程：**

1. SSE 连接建立时，generator **先立即推送当前全量消息**（初始状态同步）
2. `send_message()` 保存新消息到 DB → 调用 `event_bus.notify(session_id)`
3. `EventBus.notify()` 通过 `loop.call_soon_threadsafe()` 递增 session 版本号 + set `asyncio.Event`
4. SSE async generator 中的 `event_bus.wait()` 返回 → 通过 `run_in_executor` 执行 `ChatService.get_messages()` 获取全量消息
5. 序列化为 JSON → StreamingResponse 推送 `data: [...]\n\n`
6. 前端 EventSource.onmessage 接收 JSON.parse → 更新 React state

**Generator 循环结构：**

```python
async def event_generator(session_id, event_bus, db_factory):
    # 初始推送（连接建立时的全量消息）
    messages = await run_in_executor(get_messages, session_id)
    yield f"data: {json.dumps(messages)}\n\n"

    while True:
        try:
            notified = await event_bus.wait(session_id, timeout=30)
            if not notified:
                yield ": heartbeat\n\n"
                continue
            messages = await run_in_executor(get_messages, session_id)
            yield f"data: {json.dumps(messages)}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
            await asyncio.sleep(5)  # 退避 5s：不长不短，恢复后 ~5s 内重新推送；DB down 时不会高频重试
```

**版本计数竞态处理：**

```python
def notify(self, session_id: str):
    self._loop.call_soon_threadsafe(self._notify_impl, session_id)

def _notify_impl(self, session_id: str):
    self._versions[session_id] = self._versions.get(session_id, 0) + 1
    event = self._events.get(session_id)
    if event:
        event.set()

async def wait(self, session_id: str, timeout: float = 30) -> bool:
    version = self._versions.get(session_id, 0)
    if session_id not in self._events:
        self._events[session_id] = asyncio.Event()
    event = self._events[session_id]
    event.clear()
    # 检查版本是否已在 clear 期间变更（有未消费通知）
    if self._versions.get(session_id, 0) != version:
        return True
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False
```

## Goals / Non-Goals

**Goals:**
- 消息变更后实时推送到前端
- 对话空闲时零 HTTP 流量
- 后端资源随连接关闭释放

**Non-Goals:**
- 多服务/分布式场景（v2 做，当前仅单进程）
- 增量同步（每次推送全量消息，数据量小无需优化）
- 浏览器不支持 EventSource 时的降级方案（如 polyfill，不会引入）
- 离线消息缓存 / 消息队列（服务端不缓存推送失败的消息，EventSource 自动重连后通过全量拉取自愈）
- 连接数限流 / 每用户连接上限（当前不限制同一用户的并发 SSE 连接数，多 tab 按需建立）
- 消息确认机制（不要求客户端 ACK，缺失的消息通过下次全量推送补全）

## Decisions

| 决策 | 方案 | 原因 |
|------|------|------|
| 推送协议 | SSE via `StreamingResponse` | 单向推送场景 SSE 足够，比 WebSocket 简单。`sse-starlette` 需加依赖，用原生 `StreamingResponse` 即可。 |
| 事件机制 | `asyncio.Event`（异步）+ `loop.call_soon_threadsafe` 桥接 | SSE handler 是 async generator，`asyncio.Event` 与之自然配合。由于消息发送端（sync `def send_message`）运行在 FastAPI 线程池，`EventBus.notify()` 通过 `loop.call_soon_threadsafe(event.set)` 从 sync 侧向事件循环发信号。DB 查询通过 `run_in_executor` 包装避免阻塞事件循环。 |
| 心跳策略 | 30s 超时 - 注释行 | Nginx/Cloudflare 等代理默认 60-90s 超时，30s 心跳足够。`:` 开头的 SSE 注释行浏览器不收发事件。 |
| 鉴权 | SSE 端点独立依赖 `get_current_user_sse`，优先 `token` query param，回退到 `Authorization` header | EventSource 不支持设置自定义 header，只能通过 query param 传递。仅 SSE 端点暴露此能力，不影响其他 API。 |
| 消息格式 | 全量列表 | 每 session 消息量小（几十条量级），全量推送简单可靠。EventSource 重连后自动补全。 |
| 竞态处理 | 版本号计数（version counter） | 避免 `asyncio.Event.clear()` / `.wait()` 间丢失通知。`wait()` 先快照版本、clear event、检查版本是否已变（有未消费通知），跳过一次等待。notify 同时递增版本 + set event。 |
| 连接清理 | generator except GeneratorExit → 从 EventBus 移除 | 客户端断开 → generator 被 close → 释放对应 session 的 event。 |
| 多 Tab | 同一 session 多个 generator 监听同一 Event | `asyncio.Event.set()` 自然唤醒所有 waiter，一次 notify 推送到所有页面。 |
| 生命周期 | FastAPI `lifespan` 中初始化 `EventBus()` | 需在事件循环已运行后初始化。[main.py 已有 lifespan](../packages/build-engine/backend/src/app/main.py) |
| Token 过期 | MVP 暂不处理。短期对话不会过期，长期连接断开后 token 失效 → 前端页面不更新（无 polling fallback），用户刷新页面解决。 | EventSource 不暴露 HTTP 状态码，服务端友好拒绝需改鉴权中间件行为，MVP 阶段不引入。 |

## API Contract

### SSE 端点

```
GET /api/v1/projects/{project_id}/sessions/{session_id}/messages/stream
Authorization: Bearer <token>
# 或 ?token=<token>（用于 EventSource）
```

**Response:** `text/event-stream`
```
data: [{"id":"...","role":"user","content":"...","phase":null,"created_at":"..."},...]

: heartbeat
```

### Code Changes

| 文件 | 操作 | Spec 覆盖 |
|------|------|-----------|
| `backend/src/app/services/event_bus.py` | **新增** — `EventBus` 类，`notify`/`wait` 方法 | ✅ spec 场景 2,3,4 |
| `backend/src/app/middleware/auth.py` | **新增** `get_current_user_sse` 依赖（支持 `token` query param） | ✅ spec 场景 1 |
| `backend/src/app/api/chat.py` | 修改 — 新增 SSE endpoint | ✅ spec 场景 1,2,3,4,5 |
| `backend/src/app/services/chat_service.py` | 修改 — `send_message` 中调用 `event_bus.notify()` | ✅ spec 场景 2 |
| `frontend/src/pages/Chat.tsx` | 修改 — `useQuery` 替换为 `EventSource` | ⚠️ spec 覆盖了 reconnect，但缺少前端的 error state / loading state / 重连反馈 UI |

## Risks / Trade-offs

- **事件循环阻塞** — DB 查询在 async handler 中需用 `run_in_executor` 避免阻塞事件循环。单线程处理所有 SSE 连接，连接数不受线程池限制。
- **存根数据重建** — 如果服务重启，EventBus 中的 events 丢失。前端 EventSource 自动重连后会从新连接获取当前全量消息，不影响功能。
