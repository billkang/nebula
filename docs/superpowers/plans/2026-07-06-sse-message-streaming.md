# SSE 消息推送 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace frontend `refetchInterval: 2000` polling with server-sent events (SSE) for real-time message push.

**Architecture:** Backend async SSE generator using `asyncio.Event` + `StreamingResponse`, with `loop.call_soon_threadsafe` bridging from sync message-send handlers. EventBus initialized in FastAPI lifespan. Frontend `EventSource` replaces `useQuery` polling.

**Tech Stack:** Python FastAPI (backend), React + @tanstack/react-query (frontend), pytest + TestClient (testing)

## Global Constraints

- All existing routes remain sync (`def`, not `async def`) — only the new SSE endpoint is async
- DB queries inside the async generator use `run_in_executor` (sync SQLAlchemy)
- No new external dependencies
- EventSource token passed as `?token=` query param (no custom headers possible)
- Token checked once at connection time by `get_current_user_sse` dependency

---

### Task 1: EventBus — 事件总线

**Files:**
- Create: `packages/build-engine/backend/src/app/services/event_bus.py`

**Interfaces:**
- Produces: `init_event_bus()` (called from lifespan), `get_event_bus()` (returns singleton), `EventBus` class with `notify(session_id: str)` and `wait(session_id: str, timeout: float) -> bool`

- [ ] **Step 1: Write the failing test**

Create `packages/build-engine/backend/tests/test_event_bus.py`:

```python
import asyncio
import pytest
from app.services.event_bus import EventBus


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.mark.asyncio
async def test_wait_returns_true_on_notify(event_bus):
    # Arrange
    session_id = "test-session-1"
    notified = False

    async def waiter():
        nonlocal notified
        result = await event_bus.wait(session_id, timeout=5)
        notified = result

    # Act: start waiter, then notify
    task = asyncio.create_task(waiter())
    await asyncio.sleep(0.01)  # let waiter start
    event_bus.notify(session_id)
    await task

    # Assert
    assert notified


@pytest.mark.asyncio
async def test_wait_returns_false_on_timeout(event_bus):
    result = await event_bus.wait("no-notify", timeout=0.1)
    assert not result


@pytest.mark.asyncio
async def test_version_counter_prevents_race(event_bus):
    """Simulate: notify fires between clear and wait — version check catches it."""
    session_id = "race-test"
    # Prime the event
    event_bus.notify(session_id)
    # wait should return True immediately (version already incremented)
    result = await event_bus.wait(session_id, timeout=5)
    assert result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_event_bus.py -v`
Expected: ImportError / ModuleNotFoundError (EventBus not yet defined)

- [ ] **Step 3: Write minimal implementation**

```python
import asyncio
from typing import Optional


class EventBus:
    """Cross-thread event bus for SSE notification.

    Used from sync side (send_message in thread pool) via notify(),
    and from async side (SSE generator on event loop) via wait().
    Uses version counter to avoid clear/wait race conditions.
    """

    def __init__(self):
        self._loop = asyncio.get_running_loop()
        self._events: dict[str, asyncio.Event] = {}
        self._versions: dict[str, int] = {}

    def notify(self, session_id: str) -> None:
        """Called from sync thread. Schedules notify on the event loop."""
        self._loop.call_soon_threadsafe(self._notify_impl, session_id)

    def _notify_impl(self, session_id: str) -> None:
        self._versions[session_id] = self._versions.get(session_id, 0) + 1
        event = self._events.get(session_id)
        if event:
            event.set()

    async def wait(self, session_id: str, timeout: float = 30) -> bool:
        """Called from async context. Returns True if notified, False if timeout."""
        version = self._versions.get(session_id, 0)
        if session_id not in self._events:
            self._events[session_id] = asyncio.Event()
        event = self._events[session_id]
        event.clear()
        # Check if version changed during clear (pending notification)
        if self._versions.get(session_id, 0) != version:
            return True
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def remove(self, session_id: str) -> None:
        """Clean up when SSE connection closes."""
        self._events.pop(session_id, None)
        self._versions.pop(session_id, None)


# Module-level singleton
_event_bus: Optional[EventBus] = None


def init_event_bus() -> EventBus:
    """Initialize EventBus singleton. Call from FastAPI lifespan."""
    global _event_bus
    _event_bus = EventBus()
    return _event_bus


def get_event_bus() -> EventBus:
    """Get the singleton EventBus instance."""
    assert _event_bus is not None, "EventBus not initialized. Call init_event_bus() in lifespan."
    return _event_bus
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_event_bus.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/build-engine/backend/src/app/services/event_bus.py tests/test_event_bus.py
git commit -m "新增 EventBus 事件总线模块

基于 asyncio.Event + version counter 的跨线程事件通知机制。
支持 sync notify() / async wait() 的跨边界调用。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: get_current_user_sse — SSE 端点专用鉴权依赖

**Files:**
- Modify: `packages/build-engine/backend/src/app/middleware/auth.py`
- Test: `packages/build-engine/backend/tests/test_auth.py` (add tests)

**Interfaces:**
- Consumes: `token` query param or `Authorization` header
- Produces: `get_current_user_sse` dependency function

- [ ] **Step 1: Write the failing test**

Add to `tests/test_auth.py`:

```python
def test_sse_auth_token_query_param(client):
    """SSE auth via token query param should succeed."""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    resp = client.post("/api/v1/auth/register", json={
        "username": "ssetest", "email": "sse@test.com", "password": "test123456",
    })
    assert resp.status_code == 200
    login = client.post("/api/v1/auth/login", json={
        "username": "ssetest", "password": "test123456",
    })
    token = login.json()["access_token"]
    # Use SSE endpoint with token query param — will 404 on session not found
    # but auth should pass (404 means auth succeeded but session doesn't exist)
    resp = client.get(
        f"/api/v1/projects/fake/sessions/fake/messages/stream?token={token}",
    )
    assert resp.status_code != 401  # Not auth error


def test_sse_auth_no_token_fails(client):
    """SSE auth without any token should fail."""
    resp = client.get(
        "/api/v1/projects/fake/sessions/fake/messages/stream",
    )
    assert resp.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_auth.py::test_sse_auth_token_query_param -v`
Expected: FAIL — get_current_user_sse not defined / 404 for wrong reason

- [ ] **Step 3: Write get_current_user_sse in auth.py**

Add to end of `packages/build-engine/backend/src/app/middleware/auth.py`:

```python
from fastapi import Query, Request


async def get_current_user_sse(
    request: Request,
    db: Session = Depends(get_db),
    token: str | None = Query(None),
) -> User:
    """SSE endpoint auth: try token query param first, fall back to Authorization header.

    EventSource cannot set custom headers, so token is passed via ?token=xxx.
    """
    if token is None:
        # Fall back to Authorization header (for testing or future clients)
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_auth.py::test_sse_auth_token_query_param tests/test_auth.py::test_sse_auth_no_token_fails -v`
Expected: Both PASS

- [ ] **Step 5: Commit**

```bash
git add packages/build-engine/backend/src/app/middleware/auth.py tests/test_auth.py
git commit -m "新增 get_current_user_sse 鉴权依赖函数

支持 token query param（EventSource 使用）和 Authorization header 回退。
SSE 端点专用，不影响其他 API 的鉴权行为。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: EventBus 集成到 FastAPI lifespan

**Files:**
- Modify: `packages/build-engine/backend/src/app/main.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_event_bus.py`:

```python
def test_event_bus_initialized_via_lifespan(client):
    """After app startup, EventBus should be accessible."""
    from app.services.event_bus import get_event_bus
    eb = get_event_bus()
    assert eb is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_event_bus.py::test_event_bus_initialized_via_lifespan -v`
Expected: FAIL — EventBus not initialized

- [ ] **Step 3: Modify lifespan in main.py**

In `packages/build-engine/backend/src/app/main.py`, add EventBus init:

```python
from app.services.event_bus import init_event_bus

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "..", "projects"), exist_ok=True)
    init_event_bus()  # Initialize EventBus singleton in async context
    yield
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_event_bus.py::test_event_bus_initialized_via_lifespan -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/build-engine/backend/src/app/main.py
git commit -m "在 FastAPI lifespan 中集成 EventBus 初始化

EventBus 需在事件循环已运行后初始化，lifespan 是最佳位置。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: SSE 端点

**Files:**
- Modify: `packages/build-engine/backend/src/app/api/chat.py`
- Test: Create `packages/build-engine/backend/tests/test_sse.py`

- [ ] **Step 1: Write the failing test**

Create `packages/build-engine/backend/tests/test_sse.py`:

```python
import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def token(client):
    """Register and login a test user, return JWT."""
    client.post("/api/v1/auth/register", json={
        "username": "ssetest", "email": "sse@test.com", "password": "test123456",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "ssetest", "password": "test123456",
    })
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_sse_connection_established(client: TestClient, token: str):
    """SSE endpoint returns text/event-stream and pushes initial data."""
    # Create a project and session first
    resp = client.post("/api/v1/auth/register", json={
        "username": "sseproj", "email": "sseproj@test.com", "password": "test123456",
    })
    resp = client.post("/api/v1/projects", json={
        "name": "SSE Test Project",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.post(f"/api/v1/projects/{pid}/sessions",
        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    sid = resp.json()["id"]

    # Connect SSE
    with client.stream("GET",
        f"/api/v1/projects/{pid}/sessions/{sid}/messages/stream?token={token}",
    ) as stream:
        assert stream.status_code == 200
        assert stream.headers.get("content-type") == "text/event-stream"
        # Read initial data event
        raw = stream.read(4096)
        assert raw is not None


@pytest.mark.asyncio
async def test_sse_auth_no_token(client: TestClient):
    """Connecting without token should fail."""
    with client.stream("GET",
        "/api/v1/projects/fake/sessions/fake/messages/stream",
    ) as stream:
        assert stream.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_sse.py -v`
Expected: FAIL — SSE endpoint not defined

- [ ] **Step 3: Implement SSE endpoint in chat.py**

Add to `packages/build-engine/backend/src/app/api/chat.py`:

```python
import json
import asyncio
from fastapi.responses import StreamingResponse
from app.services.event_bus import get_event_bus
from app.middleware.auth import get_current_user_sse


@chat_router.get("/{session_id}/messages/stream")
async def stream_messages(
    session_id: str,
    db: DBSession = Depends(get_db),
    user: User = Depends(get_current_user_sse),
):
    event_bus = get_event_bus()

    async def event_generator():
        loop = asyncio.get_running_loop()
        try:
            # 1. Initial push: current full message list
            messages = await loop.run_in_executor(
                None, lambda: ChatService.get_messages(session_id, db)
            )
            yield f"data: {json.dumps([m.model_dump() for m in messages], default=str)}\n\n"

            # 2. Wait loop: notify → push, timeout → heartbeat
            while True:
                try:
                    notified = await event_bus.wait(session_id, timeout=30)
                    if not notified:
                        yield ": heartbeat\n\n"
                        continue
                    messages = await loop.run_in_executor(
                        None, lambda: ChatService.get_messages(session_id, db)
                    )
                    yield f"data: {json.dumps([m.model_dump() for m in messages], default=str)}\n\n"
                except Exception as e:
                    yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
                    await asyncio.sleep(5)
        except GeneratorExit:
            event_bus.remove(session_id)
        except Exception:
            event_bus.remove(session_id)
            raise

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_sse.py -v`
Expected: Both tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/build-engine/backend/src/app/api/chat.py tests/test_sse.py
git commit -m "新增 SSE 消息流端点 /messages/stream

async generator + StreamingResponse，连接建立时先推送全量消息。
EventBus wait 循环支持心跳（30s）和错误恢复（5s 退避）。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: chat_service send_message 集成 notify

**Files:**
- Modify: `packages/build-engine/backend/src/app/services/chat_service.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_sse.py`:

```python
@pytest.mark.asyncio
async def test_sse_push_on_new_message(client: TestClient, token: str):
    """Sending a message should trigger SSE push."""
    # Setup: create project + session
    resp = client.post("/api/v1/projects", json={
        "name": "SSE Push Test",
    }, headers={"Authorization": f"Bearer {token}"})
    pid = resp.json()["id"]

    resp = client.post(f"/api/v1/projects/{pid}/sessions",
        headers={"Authorization": f"Bearer {token}"})
    sid = resp.json()["id"]

    # Connect SSE
    with client.stream("GET",
        f"/api/v1/projects/{pid}/sessions/{sid}/messages/stream?token={token}",
    ) as stream:
        # Read initial push
        initial_data = stream.read(4096)
        assert b"data:" in initial_data

        # Send a message
        send_resp = client.post(
            f"/api/v1/projects/{pid}/sessions/{sid}/messages",
            json={"content": "Hello SSE"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert send_resp.status_code == 200

        # Read next SSE event (should be data: with the new message)
        push_data = stream.read(4096)
        assert b"data:" in push_data
        # Parse the SSE data
        for line in push_data.decode().split("\n"):
            if line.startswith("data: "):
                messages = json.loads(line[6:])
                assert len(messages) >= 1
                # The user message should be in the list
                assert any(m["content"] == "Hello SSE" for m in messages)
                break
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_sse.py::test_sse_push_on_new_message -v`
Expected: FAIL — SSE push not triggered (no notify call)

- [ ] **Step 3: Modify send_message in chat_service.py**

At the top of `packages/build-engine/backend/src/app/services/chat_service.py`, add:

```python
from app.services.event_bus import get_event_bus
```

At the end of `send_message` (after `agent_states[session_id] = result`, right before `return ChatService.get_messages(session_id, db)`), add:

```python
        # Notify SSE connections that new messages are available
        get_event_bus().notify(session_id)
```

The full relevant section becomes:

```python
        # 更新内存状态
        result["phase"] = new_phase
        result["req_summary"] = new_summary
        agent_states[session_id] = result

        # Notify SSE connections that new messages are available
        get_event_bus().notify(session_id)

        return ChatService.get_messages(session_id, db)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/build-engine/backend && python -m pytest tests/test_sse.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/build-engine/backend/src/app/services/chat_service.py
git commit -m "send_message 中集成 EventBus notify

消息写入 DB 后调用 event_bus.notify() 唤醒 SSE 连接推送更新。
仅在消息实际写入后触发，避免空通知。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: 前端 EventSource 替代轮询

**Files:**
- Modify: `packages/build-engine/frontend/src/pages/Chat.tsx`

- [ ] **Step 1: Replace useQuery message polling with EventSource**

In `packages/build-engine/frontend/src/pages/Chat.tsx`, make the following changes:

1. Remove `useQuery` import for messages, keep `useMutation` and `useQueryClient`
2. Add `useEffect` + `EventSource` logic
3. Show connection status indicator

Replace:

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
```

with:

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';
```

Replace the polling `useQuery` block:

```tsx
  const { data: messages } = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => {
      if (!id || !sessionId) return Promise.resolve([]);
      return api.sessions.messages(id, sessionId);
    },
    enabled: !!sessionId,
    refetchInterval: 2000,
  });
```

with an EventSource `useEffect`:

```tsx
  const [messages, setMessages] = useState<Array<{ id: string; role: string; content: string; phase?: string; created_at: string }>>([]);
  const [sseConnected, setSseConnected] = useState(false);

  useEffect(() => {
    if (!id || !sessionId) return;
    const token = localStorage.getItem('nebula_token');
    if (!token) return;

    const es = new EventSource(`/api/v1/projects/${id}/sessions/${sessionId}/messages/stream?token=${token}`);

    es.onopen = () => setSseConnected(true);

    es.onmessage = (e) => {
      try {
        const msgs = JSON.parse(e.data);
        setMessages(msgs);
      } catch { /* ignore parse errors on heartbeat/comment lines */ }
    };

    es.addEventListener('error', (e) => {
      // Check if error is auth-related
      if (es.readyState === EventSource.CLOSED) {
        setSseConnected(false);
      }
    });

    return () => {
      es.close();
      setSseConnected(false);
    };
  }, [id, sessionId]);
```

Add a connection status indicator in the JSX, after the header bar's close button:

```tsx
          <span className={`inline-block w-2 h-2 rounded-full ${sseConnected ? 'bg-green-500' : 'bg-red-400'}`}
                title={sseConnected ? '已连接' : '连接断开'} />
```

- [ ] **Step 2: Verify it builds**

Run: `cd packages/build-engine/frontend && npx tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: Verify old polling is removed**

Check that `refetchInterval` no longer appears anywhere in Chat.tsx.

```bash
grep -n "refetchInterval" packages/build-engine/frontend/src/pages/Chat.tsx
```
Expected: No output (not found)

- [ ] **Step 4: Commit**

```bash
git add packages/build-engine/frontend/src/pages/Chat.tsx
git commit -m "前端 Chat 页面改用 EventSource 替代轮询

移除 @tanstack/react-query 的 refetchInterval: 2000 轮询，
改用 EventSource 连接 SSE 端点实现消息实时推送。
添加连接状态指示器（绿/红圆点）。

Co-Authored-By: Claude <noreply@anthropic.com>"
```
