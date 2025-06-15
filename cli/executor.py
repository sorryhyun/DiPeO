# apps/cli/executor.py
from enum import Enum
from typing import Optional, Dict, Any
import asyncio
from dataclasses import dataclass
import json


class ExecutionState(Enum):
    """Deterministic state machine for CLI execution"""
    INIT = "init"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    execution_id: str
    diagram_path: str
    state: ExecutionState
    websocket: Optional[Any] = None
    start_time: float = 0
    events: list = None

    def __post_init__(self):
        if self.events is None:
            self.events = []


class DeterministicExecutor:
    """State machine based executor with no race conditions"""

    def __init__(self, monitor_mode: bool = False):
        self.monitor_mode = monitor_mode
        self.transitions = {
            ExecutionState.INIT: [ExecutionState.CONNECTING],
            ExecutionState.CONNECTING: [ExecutionState.CONNECTED, ExecutionState.FAILED],
            ExecutionState.CONNECTED: [ExecutionState.EXECUTING, ExecutionState.FAILED],
            ExecutionState.EXECUTING: [ExecutionState.MONITORING, ExecutionState.COMPLETED, ExecutionState.FAILED],
            ExecutionState.MONITORING: [ExecutionState.COMPLETED, ExecutionState.FAILED],
            ExecutionState.COMPLETED: [],
            ExecutionState.FAILED: []
        }

    async def execute(self, diagram_path: str) -> ExecutionContext:
        """Execute diagram with deterministic state transitions"""
        ctx = ExecutionContext(
            execution_id=self._generate_id(),
            diagram_path=diagram_path,
            state=ExecutionState.INIT
        )

        # State machine loop
        while ctx.state not in [ExecutionState.COMPLETED, ExecutionState.FAILED]:
            try:
                ctx = await self._transition(ctx)
            except Exception as e:
                ctx.state = ExecutionState.FAILED
                ctx.events.append({"type": "error", "error": str(e)})

        return ctx

    async def _transition(self, ctx: ExecutionContext) -> ExecutionContext:
        """Handle state transitions"""
        handlers = {
            ExecutionState.INIT: self._handle_init,
            ExecutionState.CONNECTING: self._handle_connecting,
            ExecutionState.CONNECTED: self._handle_connected,
            ExecutionState.EXECUTING: self._handle_executing,
            ExecutionState.MONITORING: self._handle_monitoring,
        }

        handler = handlers.get(ctx.state)
        if not handler:
            raise ValueError(f"No handler for state {ctx.state}")

        new_state = await handler(ctx)

        # Validate transition
        if new_state not in self.transitions[ctx.state]:
            raise ValueError(f"Invalid transition {ctx.state} -> {new_state}")

        ctx.state = new_state
        ctx.events.append({
            "type": "state_transition",
            "from": ctx.state.value,
            "to": new_state.value
        })

        return ctx

    async def _handle_init(self, ctx: ExecutionContext) -> ExecutionState:
        """Initialize execution"""
        # Load and validate diagram
        with open(ctx.diagram_path) as f:
            diagram = json.load(f)

        if not self._validate_diagram(diagram):
            raise ValueError("Invalid diagram format")

        ctx.events.append({
            "type": "diagram_loaded",
            "nodes": len(diagram.get("nodes", [])),
            "arrows": len(diagram.get("arrows", []))
        })

        return ExecutionState.CONNECTING

    async def _handle_connecting(self, ctx: ExecutionContext) -> ExecutionState:
        """Establish WebSocket connection with exponential backoff"""
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                # Connection logic here
                ctx.websocket = await self._create_websocket()

                # Verify connection with ping
                await ctx.websocket.send_json({"type": "ping"})
                pong = await asyncio.wait_for(
                    ctx.websocket.receive_json(),
                    timeout=5.0
                )

                if pong.get("type") == "pong":
                    return ExecutionState.CONNECTED

            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    ctx.events.append({
                        "type": "connection_failed",
                        "error": str(e)
                    })
                    return ExecutionState.FAILED

    async def _handle_connected(self, ctx: ExecutionContext) -> ExecutionState:
        """Send execution request"""
        with open(ctx.diagram_path) as f:
            diagram = json.load(f)

        await ctx.websocket.send_json({
            "type": "execute_diagram",
            "execution_id": ctx.execution_id,
            "diagram": diagram,
            "options": {"monitor": self.monitor_mode}
        })

        # Wait for acknowledgment
        ack = await asyncio.wait_for(
            ctx.websocket.receive_json(),
            timeout=10.0
        )

        if ack.get("type") == "execution_started":
            return ExecutionState.EXECUTING
        else:
            return ExecutionState.FAILED

    async def _handle_executing(self, ctx: ExecutionContext) -> ExecutionState:
        """Process execution events"""
        completion_events = {"execution_completed", "execution_failed"}

        while True:
            try:
                event = await asyncio.wait_for(
                    ctx.websocket.receive_json(),
                    timeout=300.0  # 5 min timeout for long operations
                )

                ctx.events.append(event)

                if event.get("type") in completion_events:
                    if event["type"] == "execution_completed":
                        return ExecutionState.COMPLETED
                    else:
                        return ExecutionState.FAILED

                # Handle specific events
                await self._process_event(ctx, event)

            except asyncio.TimeoutError:
                # Check if execution is still alive
                if not await self._check_execution_alive(ctx):
                    return ExecutionState.FAILED

    async def _process_event(self, ctx: ExecutionContext, event: dict):
        """Process individual execution events"""
        event_type = event.get("type")

        if event_type == "node_started":
            print(f"▶ {event['node_id']}: {event.get('label', 'Unknown')}")

        elif event_type == "node_completed":
            print(f"✓ {event['node_id']} completed")

        elif event_type == "llm_token":
            # Stream tokens for better UX
            print(event.get("token", ""), end="", flush=True)

        elif event_type == "error":
            print(f"✗ Error: {event.get('message', 'Unknown error')}")

    def _validate_diagram(self, diagram: dict) -> bool:
        """Validate diagram structure"""
        if not isinstance(diagram, dict):
            return False

        if "nodes" not in diagram or "arrows" not in diagram:
            return False

        # Check for start node
        start_nodes = [n for n in diagram["nodes"] if n.get("type") == "start"]
        if len(start_nodes) != 1:
            return False

        return True

    def _generate_id(self) -> str:
        """Generate unique execution ID"""
        import uuid
        return f"cli_{uuid.uuid4().hex[:8]}"

    async def _create_websocket(self):
        """Create WebSocket connection"""
        # Implementation depends on your WebSocket library
        pass

    async def _check_execution_alive(self, ctx: ExecutionContext) -> bool:
        """Check if execution is still running"""
        try:
            await ctx.websocket.send_json({"type": "execution_status"})
            status = await asyncio.wait_for(
                ctx.websocket.receive_json(),
                timeout=5.0
            )
            return status.get("alive", False)
        except:
            return False