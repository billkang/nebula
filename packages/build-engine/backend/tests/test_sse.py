import json
import asyncio
import pytest
from fastapi.testclient import TestClient
from app.models.user import User
from app.api.chat import stream_messages
from app.services.event_bus import init_event_bus


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
async def test_sse_connection_established(client: TestClient, token: str, db):
    """SSE endpoint generates initial data push on connection.

    Calls stream_messages directly and iterates the async generator,
    because httpx.ASGITransport cannot handle infinite SSE streams
    (it buffers the entire response before returning).
    """
    # Create a project and session first
    resp = client.post("/api/v1/projects", json={
        "name": "SSE Test Project",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.post(f"/api/v1/projects/{pid}/sessions",
        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    sid = resp.json()["id"]

    # Initialize EventBus with a running event loop
    init_event_bus()

    # Get the authenticated user
    user = db.query(User).filter(User.username == "ssetest").first()

    # Call stream_messages directly, bypassing HTTP layer
    response = await stream_messages(session_id=sid, db=db, user=user)

    # Verify it's a StreamingResponse with correct media type
    assert response.media_type == "text/event-stream"

    # Iterate the async generator to get the initial data push
    gen = response.body_iterator
    chunk = await gen.__anext__()

    # Verify SSE format: "data: <json>\n\n"
    assert chunk.startswith("data: ")
    assert chunk.endswith("\n\n")
    data_str = chunk[6:].strip()
    data = json.loads(data_str)
    assert isinstance(data, list)
    # No messages sent yet, so list should be empty
    assert len(data) == 0

    # Clean up — aclose() triggers GeneratorExit in the generator,
    # which calls event_bus.remove(session_id)
    await gen.aclose()


@pytest.mark.asyncio
async def test_send_message_triggers_notify(client: TestClient, token: str, db):
    """send_message should call event_bus.notify() after saving messages."""
    from unittest.mock import patch, MagicMock
    from app.services.chat_service import ChatService
    from app.models.user import User

    # Create project and session
    resp = client.post("/api/v1/projects", json={"name": "Notify Test"},
        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.post(f"/api/v1/projects/{pid}/sessions",
        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    sid = resp.json()["id"]

    # Get user
    user = db.query(User).filter(User.username == "ssetest").first()
    assert user is not None

    # Mock event bus to verify notify is called
    mock_bus = MagicMock()
    with patch("app.services.chat_service.get_event_bus", return_value=mock_bus):
        messages = ChatService.send_message(
            session_id=sid, content="Test notify", user=user, db=db
        )

    # Verify notify was called with the correct session_id
    mock_bus.notify.assert_called_once()
    args, _ = mock_bus.notify.call_args
    assert args[0] == sid

    # Verify messages were returned
    assert len(messages) > 0
    assert any(m.content == "Test notify" for m in messages)


def test_sse_auth_no_token(client: TestClient):
    """Connecting without token should fail with 401.

    Uses client.get() (non-streaming) because the auth dependency
    raises 401 before the endpoint creates the SSE stream.
    """
    resp = client.get("/api/v1/projects/fake/sessions/fake/messages/stream")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_sse_generator_heartbeat(client: TestClient, token: str, db):
    """Generator yields heartbeat on wait timeout."""
    resp = client.post("/api/v1/projects", json={"name": "HB Test"},
        headers={"Authorization": f"Bearer {token}"})
    pid = resp.json()["id"]
    resp = client.post(f"/api/v1/projects/{pid}/sessions",
        headers={"Authorization": f"Bearer {token}"})
    sid = resp.json()["id"]

    init_event_bus()
    from app.services.event_bus import get_event_bus
    user = db.query(User).filter(User.username == "ssetest").first()

    response = await stream_messages(session_id=sid, db=db, user=user)
    gen = response.body_iterator

    # Consume initial push
    first = await gen.__anext__()
    assert first.startswith("data: ")

    # Mock event_bus.wait to simulate timeout
    import asyncio
    from unittest.mock import patch

    async def mock_wait(*args, **kwargs):
        await asyncio.sleep(0.1)
        return False

    event_bus = get_event_bus()
    with patch.object(event_bus, 'wait', mock_wait):
        second = await asyncio.wait_for(gen.__anext__(), timeout=2)
        assert second == ": heartbeat\n\n"

    await gen.aclose()


@pytest.mark.asyncio
async def test_sse_generator_error_recovery(client: TestClient, token: str, db):
    """Generator handles errors and continues."""
    resp = client.post("/api/v1/projects", json={"name": "Err Test"},
        headers={"Authorization": f"Bearer {token}"})
    pid = resp.json()["id"]
    resp = client.post(f"/api/v1/projects/{pid}/sessions",
        headers={"Authorization": f"Bearer {token}"})
    sid = resp.json()["id"]

    init_event_bus()
    from unittest.mock import patch
    from app.services.chat_service import ChatService
    from app.services.event_bus import get_event_bus
    user = db.query(User).filter(User.username == "ssetest").first()

    response = await stream_messages(session_id=sid, db=db, user=user)
    gen = response.body_iterator

    # Consume initial push
    first = await gen.__anext__()
    assert first.startswith("data: ")

    # Patch get_messages to raise on first call during wait loop
    original_get = ChatService.get_messages
    call_count = 0

    def failing_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("DB error simulated")
        return original_get(*args, **kwargs)

    event_bus = get_event_bus()

    with patch.object(ChatService, 'get_messages', failing_get):
        # Start the next generator iteration in background; it enters event_bus.wait()
        next_task = asyncio.create_task(gen.__anext__())

        # Give time for generator to enter event_bus.wait()
        await asyncio.sleep(0.2)

        # Notify while generator is waiting — this unblocks wait()
        event_bus.notify(sid)

        # Generator should try get_messages, fail, yield error
        second = await asyncio.wait_for(next_task, timeout=5)
        assert "event: error" in second
        assert "DB error simulated" in second

    await gen.aclose()


@pytest.mark.asyncio
async def test_sse_generator_client_disconnect(client: TestClient, token: str, db):
    """Generator cleanup on disconnect."""
    resp = client.post("/api/v1/projects", json={"name": "Disc Test"},
        headers={"Authorization": f"Bearer {token}"})
    pid = resp.json()["id"]
    resp = client.post(f"/api/v1/projects/{pid}/sessions",
        headers={"Authorization": f"Bearer {token}"})
    sid = resp.json()["id"]

    init_event_bus()
    from app.services.event_bus import get_event_bus
    event_bus = get_event_bus()
    user = db.query(User).filter(User.username == "ssetest").first()

    response = await stream_messages(session_id=sid, db=db, user=user)
    gen = response.body_iterator

    # Consume initial push
    first = await gen.__anext__()
    assert first.startswith("data: ")

    # Close the generator — triggers GeneratorExit
    await gen.aclose()

    # Verify event_bus cleaned up the session
    assert sid not in event_bus._events
