from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from application.realtime.connection_manager import get_connection_manager

router = APIRouter(tags=["realtime"])


@router.websocket("/api/ws")
async def realtime_feed(websocket: WebSocket) -> None:
    """Stream domain events as ``{"type": ..., "payload": ...}`` messages.

    The route only registers the client. Alert rules and persistence stay in
    their Phase 11 subscribers; this transport never writes to the database.
    """
    manager = get_connection_manager()
    await manager.connect(websocket)
    try:
        # The stream is server-to-client; reading also detects disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
