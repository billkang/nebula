## 1. 后端 — 事件总线

- [ ] 1.1 新增 `event_bus.py`，实现 `EventBus` 类（`notify` / `wait` 方法，基于 `asyncio.Event`）

## 2. 后端 — SSE 端点

- [ ] 2.1 修改 `auth.py`，新增 `get_current_user_sse` 依赖函数（优先 `token` query param，回退到 `Authorization` header）
- [ ] 2.2 修改 `chat.py`，新增 SSE 端点 `GET /{session_id}/messages/stream`
- [ ] 2.3 修改 `chat_service.py`，`send_message` 中调用 `event_bus.notify()` 通知 SSE 推送

## 3. 前端 — EventSource

- [ ] 3.1 修改 `Chat.tsx`，用 `useEffect` + `EventSource` 替代 `useQuery` + `refetchInterval` 轮询

## 4. 测试

- [ ] 4.1 编写 EventBus 单元测试（notify/wait 的同步→异步桥接）
- [ ] 4.2 编写 SSE 端点集成测试（连接建立、token auth、初始推送、心跳）
- [ ] 4.3 编写推送集成测试（发消息后 SSE 收到推送、错误恢复）
