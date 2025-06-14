"""GraphQL subscription definitions for real-time updates."""
import strawberry
from typing import AsyncGenerator, Optional, List, Dict, Any
import asyncio
import logging
from datetime import datetime

from .types.domain import ExecutionState, ExecutionEvent, Node, Diagram, TokenUsage
from .types.scalars import ExecutionID, DiagramID, NodeID, JSONScalar
from .types.enums import NodeType, EventType, ExecutionStatus
from .context import GraphQLContext

logger = logging.getLogger(__name__)

# Helper types for subscriptions
@strawberry.type
class NodeExecution:
    """Real-time node execution update."""
    execution_id: ExecutionID
    node_id: NodeID
    node_type: NodeType
    status: str  # started, running, completed, failed, skipped
    progress: Optional[str] = None
    output: Optional[JSONScalar] = None
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


# Stream implementation functions
async def execution_stream(execution_id: ExecutionID, info) -> AsyncGenerator[ExecutionState, None]:
    """Stream execution state updates."""
    context: GraphQLContext = info.context
    event_store = context.event_store
    
    # Track last known state
    last_sequence = -1
    
    try:
        while True:
            # Get latest events
            events = event_store.get_events(execution_id)
            new_events = [e for e in events if e.sequence > last_sequence]
            
            if new_events:
                # Update last sequence
                last_sequence = max(e.sequence for e in new_events)
                
                # Replay full state (could be optimized to incremental updates)
                state = event_store.replay(execution_id)
                
                if state:
                    # Convert to GraphQL ExecutionState
                    yield ExecutionState(
                        id=state.execution_id,
                        status=_map_status(state.status),
                        diagram_id=state.diagram_id,
                        started_at=state.start_time,
                        ended_at=state.end_time,
                        running_nodes=[NodeID(n) for n in state.running_nodes],
                        completed_nodes=[NodeID(n) for n in state.completed_nodes],
                        skipped_nodes=[NodeID(n) for n in state.skipped_nodes],
                        paused_nodes=[NodeID(n) for n in state.paused_nodes],
                        failed_nodes=[NodeID(n) for n in state.failed_nodes],
                        node_outputs=state.node_outputs,
                        variables=state.variables,
                        token_usage=TokenUsage(
                            input=state.token_usage.input,
                            output=state.token_usage.output,
                            cached=state.token_usage.cached,
                            total=state.token_usage.total
                        ) if state.token_usage else None,
                        error=state.error
                    )
                    
                    # Check if execution is complete
                    if state.status in ['completed', 'failed', 'cancelled']:
                        break
            
            # Poll interval (100ms)
            await asyncio.sleep(0.1)
            
    except asyncio.CancelledError:
        logger.info(f"Subscription cancelled for execution {execution_id}")
        raise
    except Exception as e:
        logger.error(f"Error in execution stream for {execution_id}: {e}")
        raise

async def event_stream(
    execution_id: ExecutionID, 
    event_types: Optional[List[EventType]], 
    info
) -> AsyncGenerator[ExecutionEvent, None]:
    """Stream execution events."""
    context: GraphQLContext = info.context
    event_store = context.event_store
    
    # Track last event sequence
    last_sequence = -1
    
    try:
        while True:
            # Get latest events
            events = event_store.get_events(execution_id)
            new_events = [e for e in events if e.sequence > last_sequence]
            
            # Apply event type filtering if specified
            if event_types and new_events:
                new_events = [
                    e for e in new_events 
                    if e.event_type in [et.value for et in event_types]
                ]
            
            # Yield new events
            for event in new_events:
                last_sequence = event.sequence
                yield ExecutionEvent(
                    execution_id=event.execution_id,
                    sequence=event.sequence,
                    event_type=event.event_type,
                    node_id=NodeID(event.node_id) if event.node_id else None,
                    timestamp=event.timestamp,
                    data=event.data
                )
                
                # Check if execution is complete
                if event.event_type in ['execution_completed', 'execution_failed', 'execution_cancelled']:
                    return
            
            # Poll interval (100ms)
            await asyncio.sleep(0.1)
            
    except asyncio.CancelledError:
        logger.info(f"Event subscription cancelled for execution {execution_id}")
        raise
    except Exception as e:
        logger.error(f"Error in event stream for {execution_id}: {e}")
        raise

async def node_update_stream(
    execution_id: ExecutionID,
    node_types: Optional[List[NodeType]],
    info
) -> AsyncGenerator[NodeExecution, None]:
    """Stream node execution updates."""
    context: GraphQLContext = info.context
    event_store = context.event_store
    
    # Track processed events
    processed_events = set()
    
    try:
        while True:
            # Get latest events
            events = event_store.get_events(execution_id)
            
            # Filter for node-related events
            node_events = [
                e for e in events 
                if e.event_type in ['node_started', 'node_completed', 'node_failed', 'node_skipped']
                and e.sequence not in processed_events
            ]
            
            for event in node_events:
                processed_events.add(event.sequence)
                
                # Extract node info from event data
                node_id = event.node_id
                node_type = event.data.get('node_type', 'unknown')
                
                # Filter by node types if specified
                if node_types and node_type not in [nt.value for nt in node_types]:
                    continue
                
                # Map event type to status
                status_map = {
                    'node_started': 'started',
                    'node_completed': 'completed',
                    'node_failed': 'failed',
                    'node_skipped': 'skipped'
                }
                status = status_map.get(event.event_type, 'running')
                
                # Create NodeExecution update
                yield NodeExecution(
                    execution_id=execution_id,
                    node_id=NodeID(node_id),
                    node_type=NodeType(node_type) if node_type != 'unknown' else NodeType.JOB,
                    status=status,
                    progress=event.data.get('progress'),
                    output=event.data.get('output'),
                    error=event.data.get('error'),
                    tokens_used=event.data.get('token_usage', {}).get('total'),
                    timestamp=event.timestamp
                )
                
            # Check if execution is complete
            state = event_store.replay(execution_id)
            if state and state.status in ['completed', 'failed', 'cancelled']:
                break
            
            # Poll interval (100ms)
            await asyncio.sleep(0.1)
            
    except asyncio.CancelledError:
        logger.info(f"Node update subscription cancelled for execution {execution_id}")
        raise
    except Exception as e:
        logger.error(f"Error in node update stream for {execution_id}: {e}")
        raise

async def diagram_change_stream(diagram_id: DiagramID, info) -> AsyncGenerator[Diagram, None]:
    """Stream diagram changes."""
    # TODO: Implement collaborative editing support
    # This would require:
    # 1. File watching on diagram files
    # 2. Or a separate change tracking system
    # 3. Or integration with version control
    # For now, this is a placeholder
    logger.warning(f"Diagram change stream not yet implemented for {diagram_id}")
    while False:  # Never yields
        yield

async def interactive_prompt_stream(execution_id: ExecutionID, info) -> AsyncGenerator[InteractivePrompt, None]:
    """Stream interactive prompts."""
    context: GraphQLContext = info.context
    event_store = context.event_store
    
    # Track processed prompts
    processed_prompts = set()
    
    try:
        while True:
            # Get latest events
            events = event_store.get_events(execution_id)
            
            # Filter for interactive prompt events
            prompt_events = [
                e for e in events 
                if e.event_type == 'interactive_prompt_required'
                and e.sequence not in processed_prompts
            ]
            
            for event in prompt_events:
                processed_prompts.add(event.sequence)
                
                yield InteractivePrompt(
                    execution_id=execution_id,
                    node_id=NodeID(event.node_id),
                    prompt=event.data.get('prompt', 'User input required'),
                    timeout_seconds=event.data.get('timeout'),
                    timestamp=event.timestamp
                )
            
            # Check if execution is complete
            state = event_store.replay(execution_id)
            if state and state.status in ['completed', 'failed', 'cancelled']:
                break
            
            # Poll interval (100ms)
            await asyncio.sleep(0.1)
            
    except asyncio.CancelledError:
        logger.info(f"Interactive prompt subscription cancelled for execution {execution_id}")
        raise
    except Exception as e:
        logger.error(f"Error in interactive prompt stream for {execution_id}: {e}")
        raise


def _map_status(status: str) -> ExecutionStatus:
    """Map internal status string to GraphQL ExecutionStatus enum."""
    status_map = {
        'started': ExecutionStatus.STARTED,
        'running': ExecutionStatus.RUNNING,
        'paused': ExecutionStatus.PAUSED,
        'completed': ExecutionStatus.COMPLETED,
        'failed': ExecutionStatus.FAILED,
        'cancelled': ExecutionStatus.CANCELLED
    }
    return status_map.get(status.lower(), ExecutionStatus.STARTED)