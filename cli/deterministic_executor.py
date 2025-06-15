"""Deterministic CLI Executor with State Machine and Event Store Integration"""
import asyncio
import json
import time
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass, field
import uuid
from pathlib import Path
import logging
import websockets
from websockets.client import WebSocketClientProtocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionState(Enum):
    """Deterministic state machine for CLI execution"""
    INIT = "init"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    INTERACTIVE = "interactive"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class StateTransition:
    """Records a state transition"""
    from_state: ExecutionState
    to_state: ExecutionState
    timestamp: float
    reason: Optional[str] = None


@dataclass
class ExecutionContext:
    """Execution context with full state tracking"""
    execution_id: str
    diagram: Dict[str, Any]
    state: ExecutionState = ExecutionState.INIT
    websocket: Optional[WebSocketClientProtocol] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    transitions: List[StateTransition] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    heartbeat_task: Optional[asyncio.Task] = None
    
    def transition_to(self, new_state: ExecutionState, reason: Optional[str] = None):
        """Record a state transition"""
        transition = StateTransition(
            from_state=self.state,
            to_state=new_state,
            timestamp=time.time(),
            reason=reason
        )
        self.transitions.append(transition)
        self.state = new_state
        logger.info(f"State transition: {transition.from_state.value} -> {transition.to_state.value}")
        if reason:
            logger.info(f"  Reason: {reason}")


class DeterministicExecutor:
    """State machine based executor with event store integration"""
    
    # Valid state transitions
    TRANSITIONS = {
        ExecutionState.INIT: [ExecutionState.CONNECTING, ExecutionState.FAILED],
        ExecutionState.CONNECTING: [ExecutionState.CONNECTED, ExecutionState.FAILED],
        ExecutionState.CONNECTED: [ExecutionState.EXECUTING, ExecutionState.FAILED],
        ExecutionState.EXECUTING: [ExecutionState.MONITORING, ExecutionState.INTERACTIVE, 
                                   ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.ABORTED],
        ExecutionState.MONITORING: [ExecutionState.COMPLETED, ExecutionState.FAILED],
        ExecutionState.INTERACTIVE: [ExecutionState.EXECUTING, ExecutionState.FAILED],
        ExecutionState.COMPLETED: [],
        ExecutionState.FAILED: [],
        ExecutionState.ABORTED: []
    }
    
    def __init__(self, ws_url: str = "ws://localhost:8000/api/ws", 
                 monitor_mode: bool = False,
                 debug: bool = False,
                 timeout: int = 300):
        self.ws_url = ws_url
        self.monitor_mode = monitor_mode
        self.debug = debug
        self.timeout = timeout
        self.retry_config = {
            'max_attempts': 3,
            'initial_delay': 1.0,
            'max_delay': 10.0,
            'exponential_base': 2
        }
    
    async def execute(self, diagram_path: str, options: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        """Execute diagram with deterministic state transitions"""
        # Load diagram
        diagram = self._load_diagram(diagram_path)
        
        # Create execution context
        ctx = ExecutionContext(
            execution_id=self._generate_execution_id(),
            diagram=diagram,
            options=options or {}
        )
        
        # State machine loop
        while ctx.state not in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.ABORTED]:
            try:
                await self._handle_state(ctx)
            except Exception as e:
                logger.error(f"State handler error: {e}")
                ctx.error = str(e)
                ctx.transition_to(ExecutionState.FAILED, f"Exception: {e}")
        
        # Cleanup
        await self._cleanup(ctx)
        
        return ctx
    
    async def _handle_state(self, ctx: ExecutionContext):
        """Handle current state and transition to next state"""
        handlers = {
            ExecutionState.INIT: self._handle_init,
            ExecutionState.CONNECTING: self._handle_connecting,
            ExecutionState.CONNECTED: self._handle_connected,
            ExecutionState.EXECUTING: self._handle_executing,
            ExecutionState.MONITORING: self._handle_monitoring,
            ExecutionState.INTERACTIVE: self._handle_interactive,
        }
        
        handler = handlers.get(ctx.state)
        if not handler:
            raise ValueError(f"No handler for state {ctx.state}")
        
        await handler(ctx)
    
    async def _handle_init(self, ctx: ExecutionContext):
        """Initialize execution context"""
        # Validate diagram
        if not self._validate_diagram(ctx.diagram):
            ctx.transition_to(ExecutionState.FAILED, "Invalid diagram format")
            return
        
        # Log initialization
        node_count = len(ctx.diagram.get('nodes', {}))
        arrow_count = len(ctx.diagram.get('arrows', {}))
        logger.info(f"Loaded diagram with {node_count} nodes and {arrow_count} arrows")
        
        ctx.transition_to(ExecutionState.CONNECTING)
    
    async def _handle_connecting(self, ctx: ExecutionContext):
        """Establish WebSocket connection with retry logic"""
        attempt = 0
        delay = self.retry_config['initial_delay']
        
        while attempt < self.retry_config['max_attempts']:
            try:
                logger.info(f"Connecting to {self.ws_url} (attempt {attempt + 1})")
                
                ctx.websocket = await asyncio.wait_for(
                    websockets.connect(self.ws_url),
                    timeout=10.0
                )
                
                # Wait for connected message
                msg = await asyncio.wait_for(ctx.websocket.recv(), timeout=5.0)
                data = json.loads(msg)
                
                if data.get('type') == 'connected':
                    logger.info(f"Connected with client ID: {data.get('client_id')}")
                    # Start heartbeat
                    ctx.heartbeat_task = asyncio.create_task(self._heartbeat_loop(ctx))
                    ctx.transition_to(ExecutionState.CONNECTED)
                    return
                    
            except asyncio.TimeoutError:
                logger.warning(f"Connection timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"Connection failed on attempt {attempt + 1}: {e}")
            
            attempt += 1
            if attempt < self.retry_config['max_attempts']:
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay = min(delay * self.retry_config['exponential_base'], 
                           self.retry_config['max_delay'])
        
        ctx.transition_to(ExecutionState.FAILED, f"Failed to connect after {attempt} attempts")
    
    async def _handle_connected(self, ctx: ExecutionContext):
        """Send execution request"""
        try:
            # Prepare execution request
            request = {
                'type': 'execute_diagram',
                'diagram': ctx.diagram,
                'options': {
                    'monitor': self.monitor_mode,
                    'debugMode': self.debug,
                    **ctx.options
                }
            }
            
            # Send request
            await ctx.websocket.send(json.dumps(request))
            logger.info(f"Sent execution request for ID: {ctx.execution_id}")
            
            # Wait for execution_started
            msg = await asyncio.wait_for(ctx.websocket.recv(), timeout=10.0)
            data = json.loads(msg)
            
            if data.get('type') == 'execution_started':
                ctx.execution_id = data.get('execution_id', ctx.execution_id)
                logger.info(f"Execution started: {ctx.execution_id}")
                ctx.transition_to(ExecutionState.EXECUTING)
            else:
                ctx.transition_to(ExecutionState.FAILED, 
                                f"Unexpected response: {data.get('type')}")
                
        except asyncio.TimeoutError:
            ctx.transition_to(ExecutionState.FAILED, "Timeout waiting for execution start")
        except Exception as e:
            ctx.transition_to(ExecutionState.FAILED, f"Error sending request: {e}")
    
    async def _handle_executing(self, ctx: ExecutionContext):
        """Process execution events"""
        try:
            while True:
                # Wait for message with timeout
                msg = await asyncio.wait_for(
                    ctx.websocket.recv(), 
                    timeout=self.timeout
                )
                data = json.loads(msg)
                
                # Record event
                ctx.events.append(data)
                
                # Handle different event types
                event_type = data.get('type')
                
                if event_type == 'node_start':
                    self._handle_node_start(data)
                    
                elif event_type == 'node_complete':
                    node_id = data.get('node_id')
                    if node_id and 'output' in data:
                        ctx.node_outputs[node_id] = data['output']
                    self._handle_node_complete(data)
                    
                elif event_type == 'node_error':
                    self._handle_node_error(data)
                    
                elif event_type == 'interactive_prompt':
                    # Need user input
                    ctx.transition_to(ExecutionState.INTERACTIVE, "User input required")
                    return
                    
                elif event_type == 'execution_complete':
                    ctx.end_time = time.time()
                    logger.info("Execution completed successfully")
                    ctx.transition_to(ExecutionState.COMPLETED)
                    return
                    
                elif event_type == 'execution_error':
                    ctx.error = data.get('error', 'Unknown error')
                    ctx.transition_to(ExecutionState.FAILED, ctx.error)
                    return
                    
                elif event_type == 'execution_aborted':
                    ctx.transition_to(ExecutionState.ABORTED, "Execution aborted by user")
                    return
                    
        except asyncio.TimeoutError:
            ctx.transition_to(ExecutionState.FAILED, 
                            f"Execution timeout after {self.timeout} seconds")
        except websockets.exceptions.ConnectionClosed:
            ctx.transition_to(ExecutionState.FAILED, "WebSocket connection closed")
        except Exception as e:
            ctx.transition_to(ExecutionState.FAILED, f"Execution error: {e}")
    
    async def _handle_monitoring(self, ctx: ExecutionContext):
        """Handle monitoring mode - stream events without timeout"""
        # In monitor mode, we just stream events indefinitely
        # This would be used for real-time monitoring dashboards
        pass
    
    async def _handle_interactive(self, ctx: ExecutionContext):
        """Handle interactive prompts"""
        # This would handle user input prompts
        # For now, transition back to executing
        ctx.transition_to(ExecutionState.EXECUTING, "Interactive prompt handled")
    
    def _handle_node_start(self, data: Dict[str, Any]):
        """Handle node start event"""
        node_id = data.get('node_id', 'unknown')
        node_type = data.get('node_type', 'unknown')
        if self.debug:
            logger.info(f"Node started: {node_id} ({node_type})")
        else:
            print(f"▶ {node_id}")
    
    def _handle_node_complete(self, data: Dict[str, Any]):
        """Handle node completion event"""
        node_id = data.get('node_id', 'unknown')
        if self.debug:
            tokens = data.get('token_count', 0)
            logger.info(f"Node completed: {node_id} (tokens: {tokens})")
        else:
            print(f"✓ {node_id}")
    
    def _handle_node_error(self, data: Dict[str, Any]):
        """Handle node error event"""
        node_id = data.get('node_id', 'unknown')
        error = data.get('error', 'Unknown error')
        logger.error(f"Node error in {node_id}: {error}")
    
    async def _heartbeat_loop(self, ctx: ExecutionContext):
        """Send periodic heartbeats to keep connection alive"""
        try:
            while ctx.state not in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.ABORTED]:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                if ctx.websocket and not ctx.websocket.closed:
                    await ctx.websocket.send(json.dumps({'type': 'heartbeat'}))
                    if self.debug:
                        logger.debug("Sent heartbeat")
        except Exception as e:
            logger.warning(f"Heartbeat error: {e}")
    
    async def _cleanup(self, ctx: ExecutionContext):
        """Clean up resources"""
        # Cancel heartbeat
        if ctx.heartbeat_task:
            ctx.heartbeat_task.cancel()
            try:
                await ctx.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if ctx.websocket and not ctx.websocket.closed:
            await ctx.websocket.close()
        
        ctx.end_time = time.time()
        duration = ctx.end_time - ctx.start_time
        logger.info(f"Execution duration: {duration:.2f} seconds")
    
    def _load_diagram(self, diagram_path: str) -> Dict[str, Any]:
        """Load diagram from file"""
        import yaml
        
        path = Path(diagram_path)
        if not path.exists():
            raise FileNotFoundError(f"Diagram not found: {diagram_path}")
        
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def _validate_diagram(self, diagram: Dict[str, Any]) -> bool:
        """Validate diagram structure"""
        if not isinstance(diagram, dict):
            return False
        
        # Check required fields
        if 'nodes' not in diagram:
            logger.error("Diagram missing 'nodes' field")
            return False
        
        # Check for at least one start node
        nodes = diagram.get('nodes', {})
        start_nodes = [
            node_id for node_id, node in nodes.items()
            if node.get('type') == 'start' or node.get('data', {}).get('type') == 'start'
        ]
        
        if not start_nodes:
            logger.error("Diagram must have at least one start node")
            return False
        
        return True
    
    def _generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        return f"cli_{uuid.uuid4().hex[:8]}"


async def run_diagram(diagram_path: str, **options) -> ExecutionContext:
    """Convenience function to run a diagram"""
    executor = DeterministicExecutor(**options)
    return await executor.execute(diagram_path)


if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        result = asyncio.run(run_diagram(sys.argv[1], debug=True))
        print(f"\nExecution result: {result.state.value}")
        if result.error:
            print(f"Error: {result.error}")