import asyncio
import pytest
from app.services.event_bus import EventBus


@pytest.fixture
async def event_bus():
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


def test_event_bus_initialized_via_lifespan(client):
    """After app startup, EventBus should be accessible."""
    with client:
        from app.services.event_bus import get_event_bus
        eb = get_event_bus()
        assert eb is not None


@pytest.mark.asyncio
async def test_version_counter_prevents_race(event_bus):
    """Simulate: notify fires between clear and wait — version check catches it."""
    session_id = "race-test"
    # Prime the event
    event_bus.notify(session_id)
    # wait should return True immediately (version already incremented)
    result = await event_bus.wait(session_id, timeout=5)
    assert result
