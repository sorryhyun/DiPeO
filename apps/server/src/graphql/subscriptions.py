"""GraphQL subscription definitions for real-time updates."""
import strawberry
from typing import AsyncGenerator, Optional, List, Dict, Any
import asyncio
from datetime import datetime

from .types.domain import ExecutionState, ExecutionEvent, Node, Diagram
from .types.scalars import ExecutionID, DiagramID, NodeID
from .types.enums import NodeType, EventType

# Helper types for subscriptions
@strawberry.type
class NodeExecution:
    """Real-time node execution update."""
    execution_id: ExecutionID
    node_id: NodeID
    node_type: NodeType
    status: str  # started, running, completed, failed, skipped
    progress: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    timestamp: datetime

@strawberry.type
class InteractivePrompt:
    """Interactive prompt requiring user input."""
    execution_id: ExecutionID
    node_id: NodeID
    prompt: str
    timeout_seconds: Optional[int] = None
    timestamp: datetime

@strawberry.type
class Subscription:
    """Root subscription type for DiPeO GraphQL API."""
    
    @strawberry.subscription
    async def execution_updates(
        self, 
        info,
        execution_id: ExecutionID
    ) -> AsyncGenerator[ExecutionState, None]:
        """Subscribe to execution state updates."""
        # This will connect to the existing event system
        # and yield updates as they occur
        async for update in execution_stream(execution_id, info):
            yield update
    
    @strawberry.subscription
    async def execution_events(
        self,
        info,
        execution_id: ExecutionID,
        event_types: Optional[List[EventType]] = None
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Subscribe to specific execution events."""
        async for event in event_stream(execution_id, event_types, info):
            yield event
    
    @strawberry.subscription
    async def node_updates(
        self,
        info,
        execution_id: ExecutionID,
        node_types: Optional[List[NodeType]] = None
    ) -> AsyncGenerator[NodeExecution, None]:
        """Subscribe to node execution updates, optionally filtered by type."""
        async for update in node_update_stream(execution_id, node_types, info):
            yield update
    
    @strawberry.subscription
    async def diagram_changes(
        self,
        info,
        diagram_id: DiagramID
    ) -> AsyncGenerator[Diagram, None]:
        """Subscribe to diagram changes for collaborative editing."""
        async for change in diagram_change_stream(diagram_id, info):
            yield change
    
    @strawberry.subscription
    async def interactive_prompts(
        self,
        info,
        execution_id: ExecutionID
    ) -> AsyncGenerator[InteractivePrompt, None]:
        """Subscribe to interactive prompts that need user input."""
        async for prompt in interactive_prompt_stream(execution_id, info):
            yield prompt


# Placeholder stream functions - these will be implemented with actual services
async def execution_stream(execution_id: ExecutionID, info) -> AsyncGenerator[ExecutionState, None]:
    """Stream execution state updates."""
    # TODO: Connect to event store and yield updates
    yield
    return

async def event_stream(
    execution_id: ExecutionID, 
    event_types: Optional[List[EventType]], 
    info
) -> AsyncGenerator[ExecutionEvent, None]:
    """Stream execution events."""
    # TODO: Connect to event store with filtering
    pass

async def node_update_stream(
    execution_id: ExecutionID,
    node_types: Optional[List[NodeType]],
    info
) -> AsyncGenerator[NodeExecution, None]:
    """Stream node execution updates."""
    # TODO: Connect to execution engine
    pass

async def diagram_change_stream(diagram_id: DiagramID, info) -> AsyncGenerator[Diagram, None]:
    """Stream diagram changes."""
    # TODO: Implement collaborative editing support
    pass

async def interactive_prompt_stream(execution_id: ExecutionID, info) -> AsyncGenerator[InteractivePrompt, None]:
    """Stream interactive prompts."""
    # TODO: Connect to interactive handler
    pass