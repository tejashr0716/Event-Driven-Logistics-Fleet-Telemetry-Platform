import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_manager import ws_manager

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/fleet/live")
async def websocket_fleet_live(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
