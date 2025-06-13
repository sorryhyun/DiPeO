"""WebSocket endpoint for real-time bidirectional communication.

IMPORTANT: This WebSocket endpoint is required for legacy support, specifically:
1. CLI tool (tool.py) - Uses WebSocket for diagram execution and monitoring
2. Monitor mode - Broadcasts execution events to browser monitors
3. Interactive prompts - Handles user responses during execution

DO NOT REMOVE until the CLI tool has been fully migrated to GraphQL.

Most frontend functionality has been migrated to GraphQL subscriptions,
but the CLI tool still depends entirely on WebSocket communication.
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from ...utils.app_context import AppContext, get_app_context
from ...exceptions import ValidationError
from ..messages import MessageFactory
from ..websocket_state import (
    ExecutionStateManager, 
    ClientSubscriptionManager, 
    InteractiveHandlerFactory
)
from ..websocket_utils import (
    WebSocketValidator, 
    MessageBroadcaster, 
    generate_execution_id
)
from ...services.message_router import message_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.state_manager = ExecutionStateManager()
        self.subscription_manager = ClientSubscriptionManager()
        self.validator = WebSocketValidator()
        self.broadcaster: Optional[MessageBroadcaster] = None
        self._router_initialized = False
        
    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Initialize message router if not already done
        if not self._router_initialized:
            await message_router.initialize()
            self._router_initialized = True
        
        # Register connection with the router
        async def websocket_sender(message: dict):
            """Handler for messages routed from other workers"""
            if client_id in self.active_connections:
                ws = self.active_connections[client_id]
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
        
        await message_router.register_connection(client_id, websocket_sender)
        
        # Initialize broadcaster if not already done
        if not self.broadcaster:
            self.broadcaster = MessageBroadcaster(
                send_func=self.send_to_client,
                broadcast_func=self.broadcast
            )
        logger.info(f"Client {client_id} connected via WebSocket")
        
    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Unregister from router
        await message_router.unregister_connection(client_id)
        
        self.subscription_manager.remove_client(client_id)
        logger.info(f"Client {client_id} disconnected from WebSocket")
        
    async def send_to_client(self, client_id: str, message: dict):
        """Send a message to a specific client."""
        # First try local delivery
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json(message)
                    return
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    await self.disconnect(client_id)
                    return
        
        # If not local, route through message router
        if self._router_initialized:
            success = await message_router.route_to_connection(client_id, message)
            if not success:
                logger.warning(f"Failed to route message to client {client_id}")
                    
    async def broadcast(self, message: dict, execution_id: str = None):
        """Broadcast a message to all connected clients or those subscribed to an execution."""
        if execution_id and self._router_initialized:
            # Use router for execution-specific broadcasts
            await message_router.broadcast_to_execution(execution_id, message)
        else:
            # General broadcast - send to all local connections
            disconnected_clients = []
            
            for client_id, websocket in self.active_connections.items():
                # Check if client is subscribed to this execution or if it's a general broadcast
                if execution_id is None or self.subscription_manager.is_client_subscribed(client_id, execution_id):
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
                await self.send_to_client(client_id, MessageFactory.heartbeat_ack())
                
            case 'subscribe_monitor':
                # Subscribe to all execution monitoring events
                await self.send_to_client(client_id, MessageFactory.subscribed('monitor'))
                
            case 'execute_diagram':
                # Handle diagram execution request
                await self.execute_diagram(client_id, message, app_context)
                
            case 'pause_node':
                await self.pause_node(client_id, message)
            case 'resume_node':
                await self.resume_node(client_id, message)
            case 'skip_node':
                await self.skip_node(client_id, message)
            case 'abort_execution':
                await self.abort_execution(client_id, message)
                
            case 'interactive_response':
                await self.handle_interactive_response(client_id, message)
                
            case _:
                # Unknown message type
                await self.broadcaster.send_error(client_id, f'Unknown message type: {message_type}')
                
    async def execute_diagram(self, client_id: str, message: dict, app_context: AppContext):
        """Execute a diagram and stream results via WebSocket."""
        execution_id = None
        try:
            # Validate request
            diagram, options, error = self.validator.validate_diagram_request(message)
            if error:
                await self.send_to_client(client_id, error.to_dict())
                return
                
            # Generate execution ID
            execution_id = generate_execution_id()
            
            # Create execution state
            self.state_manager.create_execution(execution_id, client_id)
            
            # Subscribe client to this execution
            self.subscription_manager.subscribe_client(client_id, execution_id)
            
            # Register subscription with router for cross-worker broadcasts
            if self._router_initialized:
                await message_router.subscribe_connection_to_execution(client_id, execution_id)
            
            # Create interactive handler
            handler_factory = InteractiveHandlerFactory(self.state_manager, self.broadcast)
            interactive_handler = handler_factory.create_handler(execution_id)
            
            # Send execution started event
            await self.send_to_client(client_id, MessageFactory.execution_started(execution_id))
            
            # Use ExecutionService
            execution_service = app_context.execution_service
            
            # Execute diagram and stream updates
            async for update in execution_service.execute_diagram(
                diagram, options, execution_id, interactive_handler, self.state_manager
            ):
                # Check if execution was aborted
                if self.state_manager.is_execution_aborted(execution_id):
                    await self.send_to_client(client_id, MessageFactory.execution_aborted(execution_id))
                    break
                    
                # Send update to client
                await self.send_to_client(client_id, update)
                
            # Clean up execution state
            self.state_manager.remove_execution(execution_id)
            
            # Unsubscribe from router
            if self._router_initialized:
                await message_router.unsubscribe_connection_from_execution(client_id, execution_id)
                
        except ValidationError as e:
            await self.broadcaster.send_error(client_id, str(e), execution_id)
        except Exception as e:
            logger.error(f"Diagram execution failed: {e}", exc_info=True)
            await self.broadcaster.send_error(client_id, f"Execution failed: {str(e)}", execution_id)
            
    async def pause_node(self, client_id: str, message: dict):
        """Pause a specific node execution."""
        # Validate message
        node_id, execution_id, error = self.validator.validate_node_control(message)
        if error:
            await self.send_to_client(client_id, error.to_dict())
            return
            
        # Check execution exists
        if not self.state_manager.execution_exists(execution_id):
            await self.broadcaster.send_error(client_id, f'Execution {execution_id} not found')
            return
            
        # Pause node
        if self.state_manager.pause_node(execution_id, node_id):
            msg = MessageFactory.node_paused(node_id, execution_id)
            await self.broadcaster.send_and_broadcast(client_id, msg, execution_id)
            
    async def resume_node(self, client_id: str, message: dict):
        """Resume a paused node execution."""
        # Validate message
        node_id, execution_id, error = self.validator.validate_node_control(message)
        if error:
            await self.send_to_client(client_id, error.to_dict())
            return
            
        # Check execution exists
        if not self.state_manager.execution_exists(execution_id):
            await self.broadcaster.send_error(client_id, f'Execution {execution_id} not found')
            return
            
        # Check if node is paused
        if not self.state_manager.is_node_paused(execution_id, node_id):
            await self.broadcaster.send_error(client_id, f'Node {node_id} is not paused')
            return
            
        # Resume node
        if self.state_manager.resume_node(execution_id, node_id):
            msg = MessageFactory.node_resumed(node_id, execution_id)
            await self.broadcaster.send_and_broadcast(client_id, msg, execution_id)
            
    async def skip_node(self, client_id: str, message: dict):
        """Skip a node execution."""
        # Validate message
        node_id, execution_id, error = self.validator.validate_node_control(message)
        if error:
            await self.send_to_client(client_id, error.to_dict())
            return
            
        # Check execution exists
        if not self.state_manager.execution_exists(execution_id):
            await self.broadcaster.send_error(client_id, f'Execution {execution_id} not found')
            return
            
        # Mark node for skipping
        if self.state_manager.skip_node(execution_id, node_id):
            msg = MessageFactory.node_skip_requested(node_id, execution_id)
            await self.broadcaster.send_and_broadcast(client_id, msg, execution_id)
            
    async def abort_execution(self, client_id: str, message: dict):
        """Abort an entire execution."""
        # Validate message
        execution_id, error = self.validator.validate_execution_control(message)
        if error:
            await self.send_to_client(client_id, error.to_dict())
            return
            
        # Check execution exists
        if not self.state_manager.execution_exists(execution_id):
            await self.broadcaster.send_error(client_id, f'Execution {execution_id} not found')
            return
            
        # Abort execution
        if self.state_manager.abort_execution(execution_id):
            msg = MessageFactory.execution_abort_requested(execution_id)
            await self.broadcaster.send_and_broadcast(client_id, msg, execution_id)
    
    async def handle_interactive_response(self, client_id: str, message: dict):
        """Handle user response to an interactive prompt."""
        # Validate message
        node_id, execution_id, response, error = self.validator.validate_interactive_response(message)
        if error:
            await self.send_to_client(client_id, error.to_dict())
            return
            
        # Try to resolve the interactive prompt
        if self.state_manager.resolve_interactive_prompt(execution_id, node_id, response):
            # Send acknowledgment
            msg = MessageFactory.interactive_response_received(node_id, execution_id)
            await self.broadcaster.send_and_broadcast(client_id, msg, execution_id)
        else:
            await self.broadcaster.send_error(
                client_id, 
                f'No interactive prompt pending for node {node_id}'
            )
    


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
        await manager.send_to_client(client_id, MessageFactory.connected(client_id))
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle the message
                await manager.handle_message(client_id, message, app_context)
                
            except json.JSONDecodeError as e:
                await manager.send_to_client(
                    client_id, 
                    MessageFactory.error(f'Invalid JSON: {str(e)}')
                )
                
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await manager.disconnect(client_id)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager