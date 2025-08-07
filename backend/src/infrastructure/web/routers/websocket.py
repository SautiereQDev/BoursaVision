"""WebSocket endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.get("/health")
async def websocket_health():
    """WebSocket service health check."""
    return {"status": "ok", "service": "websocket"}
