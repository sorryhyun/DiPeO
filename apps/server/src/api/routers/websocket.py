"""WebSocket endpoint for real-time bidirectional communication."""
import asyncio
import json
import logging
import uuid
from typing import Dict, Set, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState


from ...utils.app_context import AppContext
from ...engine.engine import UnifiedExecutionEngine
from ...exceptions import ValidationError, DiagramExecutionError

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
        self.execution_states: Dict[str, Dict] = {}
        self.interactive_prompts: Dict[str, asyncio.Future] = {}  # node_id -> Future for user response
        
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
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                })
                
    async def execute_diagram(self, client_id: str, message: dict, app_context: AppContext):
        """Execute a diagram and stream results via WebSocket."""
        try:
            diagram = message.get('diagram')
            options = message.get('options', {})
            
            if not diagram:
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': 'No diagram provided'
                })
                return
                
            # Validate diagram structure
            if not isinstance(diagram, dict):
                await self.send_to_client(client_id, {
                    'type': 'error', 
                    'message': 'Diagram must be a dictionary'
                })
                return
                
            nodes = diagram.get("nodes", [])
            if not nodes:
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': 'Diagram must contain at least one node'
                })
                return
                
            # Check for start nodes
            start_nodes = [
                node for node in nodes 
                if node.get("type", "") == "start" or 
                   node.get("data", {}).get("type", "") == "start"
            ]
            if not start_nodes:
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': 'Diagram must contain at least one start node'
                })
                return
                
            # Set up execution options
            execution_options = {
                "continue_on_error": options.get("continueOnError", False),
                "allow_partial": options.get("allowPartial", False),
                "debug_mode": options.get("debugMode", False),
                **options
            }
            
            # Generate execution ID
            execution_id = f"exec_{int(datetime.now().timestamp() * 1000)}"
            execution_options["execution_id"] = execution_id
            
            # Store execution state
            self.execution_states[execution_id] = {
                'client_id': client_id,
                'status': 'running',
                'paused_nodes': set(),
                'aborted': False
            }
            
            # Subscribe client to this execution
            if client_id not in self.client_subscriptions:
                self.client_subscriptions[client_id] = set()
            self.client_subscriptions[client_id].add(execution_id)
            
            # Pre-initialize LLM models
            llm_service = app_context.llm_service
            api_key_service = app_context.api_key_service
            
            pre_initialized = set()
            persons = diagram.get("persons", [])
            
            for person in persons:
                model = person.get("model", "")
                service = person.get("service", "")
                api_key_id = person.get("apiKeyId", "")
                
                if model and service and api_key_id:
                    config_key = f"{service}:{model}:{api_key_id}"
                    if config_key not in pre_initialized:
                        try:
                            llm_service.pre_initialize_model(
                                service=service,
                                model=model,
                                api_key_id=api_key_id
                            )
                            pre_initialized.add(config_key)
                        except Exception as e:
                            logger.warning(f"Failed to pre-initialize {config_key}: {e}")
                            
            # Load API keys
            api_keys_list = api_key_service.list_api_keys()
            api_keys_dict = {}
            for key_info in api_keys_list:
                full_key_data = api_key_service.get_api_key(key_info["id"])
                api_keys_dict[key_info["id"]] = full_key_data["key"]
                
            # Create enhanced diagram with API keys
            enhanced_diagram = {
                **diagram,
                "api_keys": api_keys_dict
            }
            
            # Create execution engine
            execution_engine = UnifiedExecutionEngine(
                llm_service=app_context.llm_service,
                file_service=app_context.file_service,
                memory_service=app_context.memory_service
            )
            
            # Create interactive handler for this execution
            interactive_handler = await self.create_interactive_handler(execution_id)
            
            # Send execution started event
            await self.send_to_client(client_id, {
                'type': 'execution_started',
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat()
            })
            
            # Add interactive handler to execution options
            execution_options["interactive_handler"] = interactive_handler
            
            # Execute diagram and stream updates
            async for update in execution_engine.execute_diagram(
                enhanced_diagram, 
                execution_options
            ):
                # Add execution ID to all updates
                update["execution_id"] = execution_id
                
                # Check if execution was aborted
                if self.execution_states.get(execution_id, {}).get('aborted'):
                    await self.send_to_client(client_id, {
                        'type': 'execution_aborted',
                        'execution_id': execution_id,
                        'timestamp': datetime.now().isoformat()
                    })
                    break
                    
                # Send update to client
                await self.send_to_client(client_id, update)
                
            # Clean up execution state
            if execution_id in self.execution_states:
                del self.execution_states[execution_id]
                
        except Exception as e:
            logger.error(f"Diagram execution failed: {e}", exc_info=True)
            await self.send_to_client(client_id, {
                'type': 'execution_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
    async def pause_node(self, client_id: str, message: dict):
        """Pause a specific node execution."""
        node_id = message.get('nodeId')
        execution_id = message.get('executionId')
        
        if not node_id or not execution_id:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': 'nodeId and executionId are required'
            })
            return
            
        if execution_id in self.execution_states:
            self.execution_states[execution_id]['paused_nodes'].add(node_id)
            await self.send_to_client(client_id, {
                'type': 'node_paused',
                'nodeId': node_id,
                'executionId': execution_id,
                'timestamp': datetime.now().isoformat()
            })
            # Broadcast to all clients subscribed to this execution
            await self.broadcast({
                'type': 'node_paused',
                'nodeId': node_id,
                'executionId': execution_id,
                'timestamp': datetime.now().isoformat()
            }, execution_id)
        else:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': f'Execution {execution_id} not found'
            })
            
    async def resume_node(self, client_id: str, message: dict):
        """Resume a paused node execution."""
        node_id = message.get('nodeId')
        execution_id = message.get('executionId')
        
        if not node_id or not execution_id:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': 'nodeId and executionId are required'
            })
            return
            
        if execution_id in self.execution_states:
            paused_nodes = self.execution_states[execution_id].get('paused_nodes', set())
            if node_id in paused_nodes:
                paused_nodes.discard(node_id)
                await self.send_to_client(client_id, {
                    'type': 'node_resumed',
                    'nodeId': node_id,
                    'executionId': execution_id,
                    'timestamp': datetime.now().isoformat()
                })
                # Broadcast to all clients
                await self.broadcast({
                    'type': 'node_resumed',
                    'nodeId': node_id,
                    'executionId': execution_id,
                    'timestamp': datetime.now().isoformat()
                }, execution_id)
            else:
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': f'Node {node_id} is not paused'
                })
        else:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': f'Execution {execution_id} not found'
            })
            
    async def skip_node(self, client_id: str, message: dict):
        """Skip a node execution."""
        node_id = message.get('nodeId')
        execution_id = message.get('executionId')
        
        if not node_id or not execution_id:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': 'nodeId and executionId are required'
            })
            return
            
        if execution_id in self.execution_states:
            # Store skip request - actual skipping will be handled by execution engine
            if 'skipped_nodes' not in self.execution_states[execution_id]:
                self.execution_states[execution_id]['skipped_nodes'] = set()
            self.execution_states[execution_id]['skipped_nodes'].add(node_id)
            
            await self.send_to_client(client_id, {
                'type': 'node_skip_requested',
                'nodeId': node_id,
                'executionId': execution_id,
                'timestamp': datetime.now().isoformat()
            })
            # Broadcast to all clients
            await self.broadcast({
                'type': 'node_skip_requested',
                'nodeId': node_id,
                'executionId': execution_id,
                'timestamp': datetime.now().isoformat()
            }, execution_id)
        else:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': f'Execution {execution_id} not found'
            })
            
    async def abort_execution(self, client_id: str, message: dict):
        """Abort an entire execution."""
        execution_id = message.get('executionId')
        
        if not execution_id:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': 'executionId is required'
            })
            return
            
        if execution_id in self.execution_states:
            self.execution_states[execution_id]['aborted'] = True
            await self.send_to_client(client_id, {
                'type': 'execution_abort_requested',
                'executionId': execution_id,
                'timestamp': datetime.now().isoformat()
            })
            # Broadcast to all clients
            await self.broadcast({
                'type': 'execution_abort_requested',
                'executionId': execution_id,
                'timestamp': datetime.now().isoformat()
            }, execution_id)
        else:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': f'Execution {execution_id} not found'
            })
    
    async def handle_interactive_response(self, client_id: str, message: dict):
        """Handle user response to an interactive prompt."""
        node_id = message.get('nodeId')
        execution_id = message.get('executionId')
        response = message.get('response', '')
        
        if not node_id or not execution_id:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': 'nodeId and executionId are required'
            })
            return
            
        # Create a unique key for this prompt
        prompt_key = f"{execution_id}:{node_id}"
        
        # Check if there's a pending interactive prompt
        if prompt_key in self.interactive_prompts:
            future = self.interactive_prompts[prompt_key]
            if not future.done():
                # Set the result to unblock the waiting executor
                future.set_result(response)
                
                # Send acknowledgment
                await self.send_to_client(client_id, {
                    'type': 'interactive_response_received',
                    'nodeId': node_id,
                    'executionId': execution_id,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Broadcast to all clients
                await self.broadcast({
                    'type': 'interactive_response_received',
                    'nodeId': node_id,
                    'executionId': execution_id,
                    'timestamp': datetime.now().isoformat()
                }, execution_id)
                
                # Clean up
                del self.interactive_prompts[prompt_key]
            else:
                await self.send_to_client(client_id, {
                    'type': 'error',
                    'message': f'Interactive prompt for node {node_id} already completed'
                })
        else:
            await self.send_to_client(client_id, {
                'type': 'error',
                'message': f'No interactive prompt pending for node {node_id}'
            })
    
    async def create_interactive_handler(self, execution_id: str):
        """Create an interactive handler function for a specific execution."""
        async def interactive_handler(node_id: str, prompt: str, context: dict) -> str:
            # Create a unique key for this prompt
            prompt_key = f"{execution_id}:{node_id}"
            
            # Create a future to wait for the response
            future = asyncio.Future()
            self.interactive_prompts[prompt_key] = future
            
            # Send interactive prompt to all clients subscribed to this execution
            await self.broadcast({
                'type': 'interactive_prompt',
                'nodeId': node_id,
                'executionId': execution_id,
                'prompt': prompt,
                'context': context,
                'timestamp': datetime.now().isoformat()
            }, execution_id)
            
            try:
                # Wait for response with a timeout
                response = await asyncio.wait_for(future, timeout=300.0)  # 5 minute timeout
                return response
            except asyncio.TimeoutError:
                # Clean up on timeout
                if prompt_key in self.interactive_prompts:
                    del self.interactive_prompts[prompt_key]
                    
                await self.broadcast({
                    'type': 'interactive_prompt_timeout',
                    'nodeId': node_id,
                    'executionId': execution_id,
                    'timestamp': datetime.now().isoformat()
                }, execution_id)
                
                # Return empty string on timeout
                return ""
            except Exception as e:
                logger.error(f"Error in interactive handler: {e}")
                # Clean up on error
                if prompt_key in self.interactive_prompts:
                    del self.interactive_prompts[prompt_key]
                return ""
                
        return interactive_handler


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