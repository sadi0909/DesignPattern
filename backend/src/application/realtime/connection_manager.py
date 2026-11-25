"""WebSocket client registry and broadcast queue.

The event bus is synchronous and can publish from a request worker thread,
while WebSockets belong to the server's event loop. Broadcasts therefore cross
the thread boundary through a bounded queue instead of touching sockets from
the publisher.
"""

import asyncio
import contextlib
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

MAX_QUEUED_MESSAGES = 100


class ConnectionManager:
    """Tracks open sockets and delivers JSON envelopes to all of them."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[dict[str, Any]] | None = None
        self._drain_task: asyncio.Task[None] | None = None

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def start(self) -> None:
        """Bind to the running loop and start draining queued broadcasts."""
        if self._drain_task is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue(maxsize=MAX_QUEUED_MESSAGES)
        self._drain_task = asyncio.create_task(self._drain(), name="ws-broadcast")

    async def stop(self) -> None:
        """Cancel the drain task and close every connected client."""
        task = self._drain_task
        self._drain_task = None
        self._queue = None
        self._loop = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        for websocket in list(self._clients):
            with contextlib.suppress(Exception):
                await websocket.close(code=1001)
        self._clients.clear()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    def broadcast(self, message: dict[str, Any]) -> None:
        """Queue ``message`` for every client; safe to call from any thread."""
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        loop.call_soon_threadsafe(self._enqueue, message)

    def _enqueue(self, message: dict[str, Any]) -> None:
        queue = self._queue
        if queue is None:
            return
        if queue.full():
            # A stalled client must not grow memory without bound: keep the
            # newest events and drop the oldest queued one.
            with contextlib.suppress(asyncio.QueueEmpty):
                queue.get_nowait()
        queue.put_nowait(message)

    async def _drain(self) -> None:
        queue = self._queue
        if queue is None:
            return
        while True:
            message = await queue.get()
            await self._send_all(message)

    async def _send_all(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for websocket in list(self._clients):
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError, OSError):
                dead.append(websocket)
        for websocket in dead:
            self._clients.discard(websocket)
            logger.info("Dropped a WebSocket client that could not receive a broadcast")


_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Return the process-wide manager used by the route and the subscriber."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
