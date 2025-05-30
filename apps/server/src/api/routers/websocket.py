from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...streaming.stream_manager import stream_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time execution updates."""
    await stream_manager.connect_websocket(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "subscribe_execution":
                execution_id = data["execution_id"]
                await stream_manager.subscribe_to_execution(client_id, execution_id)
    except WebSocketDisconnect:
        await stream_manager.disconnect_websocket(client_id)