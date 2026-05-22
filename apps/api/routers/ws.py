from __future__ import annotations
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.security import decode_token
from ..services.ws_manager import ws_manager
import logging

log = logging.getLogger("ws-router")
router = APIRouter(tags=["realtime"])

@router.websocket("/ws/{farm_id}")
async def farm_websocket(farm_id: str, websocket: WebSocket, token: str = ""):
    """
    WebSocket endpoint — clients connect with:
      ws://host/ws/{farm_id}?token=<access_token>
    Receives real-time events: ALERT_CREATED, DEVICE_UPDATED, TELEMETRY
    """
    # Validate token
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(farm_id, websocket)
    try:
        # Send initial heartbeat
        import json
        from datetime import datetime, timezone
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "data": {"farm_id": farm_id},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))
        # Keep alive — client sends ping, server echoes pong
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(farm_id, websocket)
        log.info(f"Client disconnected from farm {farm_id}")
