import json
import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger("FleetSync.WebSocket")

class FleetWebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("Client connected to FleetSync live radar stream.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_ping(self, data: dict):
        if not self.active_connections:
            return
        payload = json.dumps(data, default=str)
        dead_connections = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_connections.add(ws)
        for ws in dead_connections:
            self.active_connections.discard(ws)

ws_manager = FleetWebSocketManager()
