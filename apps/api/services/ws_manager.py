from __future__ import annotations
"""
WebSocket connection manager — pushes real-time events to connected browser clients.
Each client subscribes to a farm_id channel.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from typing import DefaultDict
from collections import defaultdict

log = logging.getLogger("ws-manager")


class ConnectionManager:
    def __init__(self):
        # farm_id -> list of connected WebSocket clients
        self.farm_connections: DefaultDict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, farm_id: str, websocket: WebSocket):
        await websocket.accept()
        self.farm_connections[farm_id].append(websocket)
        log.info(f"WS connected to farm {farm_id}. Total: {len(self.farm_connections[farm_id])}")

    def disconnect(self, farm_id: str, websocket: WebSocket):
        if websocket in self.farm_connections[farm_id]:
            self.farm_connections[farm_id].remove(websocket)
        log.info(f"WS disconnected from farm {farm_id}")

    async def broadcast(self, farm_id: str, event_type: str, data: dict):
        """Push an event to all clients subscribed to a farm."""
        if not self.farm_connections[farm_id]:
            return
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        dead = []
        for ws in self.farm_connections[farm_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.farm_connections[farm_id].remove(ws)

    async def broadcast_alert(self, farm_id: str, alert: dict):
        await self.broadcast(farm_id, "ALERT_CREATED", alert)

    async def broadcast_device_update(self, farm_id: str, device: dict):
        await self.broadcast(farm_id, "DEVICE_UPDATED", device)

    async def broadcast_telemetry(self, farm_id: str, device_id: str, readings: list):
        await self.broadcast(farm_id, "TELEMETRY", {"device_id": device_id, "readings": readings})


# Singleton
ws_manager = ConnectionManager()
