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
        """Called from sync thread. Schedules notify on the event loop.

        If the event loop is already closed (e.g. during shutdown or test
        cleanup), the notification is silently skipped — messages are still
        persisted to the database regardless.
        """
        if self._loop.is_closed():
            return
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
    if _event_bus is None:
        raise RuntimeError("EventBus not initialized. Call init_event_bus() in lifespan.")
    return _event_bus
