"""WebSocket endpoint for real-time bidirectional communication."""
import asyncio
import json
import logging
import uuid
from typing import Dict, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from ...utils.dependencies import get_app_context
from ...utils.app_context import AppContext

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
        self.execution_states: Dict[str, Dict] = {}
        
    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"Client {client_id} connected via WebSocket")
        
    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected from WebSocket")
        
    async def send_to_client(self, client_id: str, message: dict):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    await self.disconnect(client_id)
                    
    async def broadcast(self, message: dict, execution_id: str = None):
        """Broadcast a message to all connected clients or those subscribed to an execution."""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            # Check if client is subscribed to this execution or if it's a general broadcast
            if execution_id is None or execution_id in self.client_subscriptions.get(client_id, set()):
                if websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to client {client_id}: {e}")
                        disconnected_clients.append(client_id)
                else:
                    disconnected_clients.append(client_id)
                    
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
            
    async def handle_message(self, client_id: str, message: dict, app_context: AppContext):
        """Handle incoming messages from clients."""
        message_type = message.get('type')
        
        match message_type:
            case 'heartbeat':
                # Respond to heartbeat to keep connection alive
                await self.send_to_client(client_id, {'type': 'heartbeat_ack', 'timestamp': datetime.utcnow().isoformat()})
                
            case 'subscribe_monitor':
                # Subscribe to all execution monitoring events
                await self.send_to_client(client_id, {'type': 'subscribed', 'channel': 'monitor'})
                
            case 'execute_diagram':
                # Handle diagram execution request (will be implemented in Phase 3)
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': 'Diagram execution via WebSocket not yet implemented'
                })
                
            case 'pause_node' | 'resume_node' | 'skip_node' | 'abort_execution':
                # Handle execution control commands (will be implemented in Phase 3)
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': f'{message_type} not yet implemented'
                })
                
            case _:
                # Unknown message type
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                })


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    app_context: AppContext = Depends(get_app_context)
):
    """Main WebSocket endpoint for bidirectional communication."""
    client_id = str(uuid.uuid4())
    
    try:
        await manager.connect(client_id, websocket)
        
        # Send welcome message
        await manager.send_to_client(client_id, {
            'type': 'connected',
            'client_id': client_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle the message
                await manager.handle_message(client_id, message, app_context)
                
            except json.JSONDecodeError as e:
                await manager.send_to_client(client_id, {
                    'type': 'error',
                    'message': f'Invalid JSON: {str(e)}'
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await manager.disconnect(client_id)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager