"""GraphQL subscription definitions for real-time updates."""
import strawberry
from typing import AsyncGenerator, Optional, List
import asyncio
import logging
from datetime import datetime

from .types.domain import ExecutionState, ExecutionEvent, DomainDiagram
from .types.scalars import ExecutionID, DiagramID, NodeID, JSONScalar
from .types.enums import EventType  # EventType is GraphQL-specific
from src.shared.domain import NodeType, ExecutionStatus  # Import domain enums
from .context import GraphQLContext
from .redis_subscriptions import RedisSubscriptionManager

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


# noinspection PyArgumentList
@strawberry.type
class Subscription:
    """Root subscription type for DiPeO GraphQL API."""
    
    @strawberry.subscription
    async def execution_updates(
        self, 
        info: strawberry.Info[GraphQLContext],
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
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        event_types: Optional[List[EventType]] = None
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Subscribe to specific execution events."""
        async for event in event_stream(execution_id, event_types, info):
            yield event
    
    @strawberry.subscription
    async def node_updates(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        node_types: Optional[List[NodeType]] = None
    ) -> AsyncGenerator[NodeExecution, None]:
        """Subscribe to node execution updates, optionally filtered by type."""
        async for update in node_update_stream(execution_id, node_types, info):
            yield update
    
    @strawberry.subscription
    async def diagram_changes(
        self,
        info: strawberry.Info[GraphQLContext],
        diagram_id: DiagramID
    ) -> AsyncGenerator[DomainDiagram, None]:
        """Subscribe to diagram changes for collaborative editing."""
        async for change in diagram_change_stream(diagram_id, info):
            yield change
    
    @strawberry.subscription
    async def interactive_prompts(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID
    ) -> AsyncGenerator[InteractivePrompt, None]:
        """Subscribe to interactive prompts that need user input."""
        async for prompt in interactive_prompt_stream(execution_id, info):
            yield prompt


# Stream implementation functions
async def execution_stream(execution_id: ExecutionID, info: strawberry.Info[GraphQLContext]) -> AsyncGenerator[ExecutionState, None]:
    """Stream execution state updates."""
    context: GraphQLContext = info.context
    state_store = context.state_store
    
    # Redis is no longer used for subscriptions
    redis_client = None
    
    if redis_client:
        # Use Redis pub/sub for real-time updates
        logger.info(f"Using Redis pub/sub for execution {execution_id}")
        subscription_manager = RedisSubscriptionManager(redis_client)
        
        try:
            async for event_data in subscription_manager.subscribe_to_execution(execution_id):
                # Replay state after each event
                state = await state_store.get_state(execution_id)
                
                if state:
                    # Convert to GraphQL ExecutionState
                    yield ExecutionState(
                        id=state.execution_id,
                        status=_map_status(state.status),
                        diagram_id=state.diagram_id if hasattr(state, 'diagram_id') else None,
                        started_at=datetime.fromtimestamp(state.start_time),
                        ended_at=datetime.fromtimestamp(state.end_time) if state.end_time else None,
                        current_node=state.node_statuses.get('current'),
                        node_outputs=state.node_outputs,
                        variables=state.variables,
                        total_tokens=state.total_tokens.get('total', 0) if state.total_tokens else 0,
                        error=state.error,
                        # Additional fields for compatibility
                        progress=len([s for s in state.node_statuses.values() if s == 'completed']) / max(len(state.node_statuses), 1) * 100 if state.node_statuses else 0
                    )
                    
        except Exception as e:
            logger.error(f"Error in Redis subscription for {execution_id}: {e}")
            # Fall back to polling
    
    # Fallback to polling if Redis is not available
    logger.info(f"Using polling for execution {execution_id}")
    
    # Track last update time
    last_update = 0
    
    try:
        while True:
            # Get latest state
            state = await state_store.get_state(execution_id)
            
            if state and state.last_updated > last_update:
                # State has changed
                last_update = state.last_updated
                
                # Convert to GraphQL ExecutionState
                yield ExecutionState(
                    id=state.execution_id,
                    status=_map_status(state.status),
                    diagram_id=state.diagram.get('id') if state.diagram else None,
                    started_at=datetime.fromtimestamp(state.start_time),
                    ended_at=datetime.fromtimestamp(state.end_time) if state.end_time else None,
                    current_node=state.current_node_id,
                    node_outputs=state.node_outputs,
                    variables=state.variables,
                    total_tokens=state.total_tokens.get('total', 0) if state.total_tokens else 0,
                    error=state.error,
                    progress=len([s for s in state.node_statuses.values() if s == 'completed']) / max(len(state.node_statuses), 1) * 100 if state.node_statuses else 0
                )
                
                # Check if execution is complete
                if state.status in ['completed', 'failed', 'aborted']:
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
    info: strawberry.Info[GraphQLContext]
) -> AsyncGenerator[ExecutionEvent, None]:
    """Stream execution events."""
    context: GraphQLContext = info.context
    state_store = context.state_store
    
    # Redis is no longer used for subscriptions
    redis_client = None
    
    if redis_client:
        # Use Redis pub/sub for real-time updates
        logger.info(f"Using Redis pub/sub for event stream {execution_id}")
        subscription_manager = RedisSubscriptionManager(redis_client)
        
        try:
            async for event_data in subscription_manager.subscribe_to_execution(execution_id):
                # Filter by event types if specified
                if event_types:
                    event_type_str = event_data.get("event_type")
                    if event_type_str not in [et.value for et in event_types]:
                        continue
                
                # Convert to GraphQL ExecutionEvent
                yield ExecutionEvent(
                    execution_id=event_data["execution_id"],
                    sequence=event_data["sequence"],
                    event_type=EventType(event_data["event_type"]),
                    node_id=NodeID(event_data["node_id"]) if event_data.get("node_id") else None,
                    timestamp=datetime.fromtimestamp(event_data["timestamp"]),
                    data=event_data.get("data", {})
                )
                
        except Exception as e:
            logger.error(f"Error in Redis event subscription for {execution_id}: {e}")
            # Fall back to polling
    
    # Simplified event stream using state changes
    logger.info(f"Using polling for event stream {execution_id}")
    
    # Track last update
    last_update = 0
    sequence = 0
    
    try:
        while True:
            # Get latest state
            state = await state_store.get_state(execution_id)
            
            if state and state.last_updated > last_update:
                # State has changed - generate a synthetic event
                last_update = state.last_updated
                sequence += 1
                
                # Create a state change event
                yield ExecutionEvent(
                    execution_id=execution_id,
                    sequence=sequence,
                    event_type=EventType.STATE_CHANGED,
                    node_id=NodeID(state.current_node_id) if state.current_node_id else None,
                    timestamp=datetime.fromtimestamp(state.last_updated),
                    data={
                        "status": state.status,
                        "node_statuses": state.node_statuses,
                        "variables": state.variables
                    }
                )
                
                # Check if execution is complete
                if state.status in ['completed', 'failed', 'aborted']:
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
    info: strawberry.Info[GraphQLContext]
) -> AsyncGenerator[NodeExecution, None]:
    """Stream node execution updates."""
    context: GraphQLContext = info.context
    state_store = context.state_store
    
    # Redis is no longer used for subscriptions
    redis_client = None
    
    node_event_types = [
        EventType.NODE_STARTED,
        EventType.NODE_COMPLETED,
        EventType.NODE_FAILED,
        EventType.NODE_SKIPPED,
        EventType.NODE_PAUSED,
        EventType.NODE_RUNNING
    ]
    
    if redis_client:
        # Use Redis pub/sub for real-time updates
        logger.info(f"Using Redis pub/sub for node updates {execution_id}")
        subscription_manager = RedisSubscriptionManager(redis_client)
        
        try:
            async for event_data in subscription_manager.subscribe_to_execution(execution_id):
                # Filter for node-related events
                event_type_str = event_data.get("event_type")
                if event_type_str not in [et.value for et in node_event_types]:
                    continue
                
                # Extract node info from event data
                node_id = event_data.get("node_id")
                if not node_id:
                    continue
                    
                node_type = event_data.get("data", {}).get('node_type', 'job')
                
                # Filter by node types if specified
                if node_types and node_type not in [nt.value for nt in node_types]:
                    continue
                
                # Map event type to status
                status_map = {
                    'node_started': 'started',
                    'node_completed': 'completed',
                    'node_failed': 'failed',
                    'node_skipped': 'skipped',
                    'node_paused': 'paused',
                    'node_resumed': 'running'
                }
                status = status_map.get(event_type_str, 'running')
                
                # Create NodeExecution update
                yield NodeExecution(
                    execution_id=execution_id,
                    node_id=NodeID(node_id),
                    node_type=NodeType(node_type),
                    status=status,
                    progress=event_data.get("data", {}).get('progress'),
                    output=event_data.get("data", {}).get('output'),
                    error=event_data.get("data", {}).get('error'),
                    tokens_used=event_data.get("data", {}).get('token_usage', {}).get('total'),
                    timestamp=datetime.fromtimestamp(event_data["timestamp"])
                )
                
        except Exception as e:
            logger.error(f"Error in Redis node update subscription for {execution_id}: {e}")
            # Fall back to polling
    
    # Fallback to polling if Redis is not available
    logger.info(f"Using polling for node updates {execution_id}")
    
    # Track processed events
    processed_events = set()
    
    try:
        while True:
            # Get latest state
            state = await state_store.get_state(execution_id)
            
            # Filter for node-related events
            node_events = [
                e for e in events 
                if EventType(e.event_type) in node_event_types
                and e.sequence not in processed_events
            ]
            
            for event in node_events:
                processed_events.add(event.sequence)
                
                # Extract node info from event data
                node_id = event.node_id
                if not node_id:
                    continue
                    
                node_type = event.data.get('node_type', 'job')
                
                # Filter by node types if specified
                if node_types and node_type not in [nt.value for nt in node_types]:
                    continue
                
                # Map event type to status
                status_map = {
                    EventType.NODE_STARTED: 'started',
                    EventType.NODE_COMPLETED: 'completed',
                    EventType.NODE_FAILED: 'failed',
                    EventType.NODE_SKIPPED: 'skipped',
                    EventType.NODE_PAUSED: 'paused',
                    EventType.NODE_RUNNING: 'running'
                }
                status = status_map.get(EventType(event.event_type), 'running')
                
                # Create NodeExecution update
                yield NodeExecution(
                    execution_id=execution_id,
                    node_id=NodeID(node_id),
                    node_type=NodeType(node_type),
                    status=status,
                    progress=event.data.get('progress'),
                    output=event.data.get('output'),
                    error=event.data.get('error'),
                    tokens_used=event.data.get('token_usage', {}).get('total'),
                    timestamp=datetime.fromtimestamp(event.timestamp)
                )
                
            # Check if execution is complete
            state = await event_store.replay(execution_id)
            if state and state.status in ['completed', 'failed', 'aborted']:
                break
            
            # Poll interval (100ms)
            await asyncio.sleep(0.1)
            
    except asyncio.CancelledError:
        logger.info(f"Node update subscription cancelled for execution {execution_id}")
        raise
    except Exception as e:
        logger.error(f"Error in node update stream for {execution_id}: {e}")
        raise

async def diagram_change_stream(diagram_id: DiagramID, info: strawberry.Info[GraphQLContext]) -> AsyncGenerator[DomainDiagram, None]:
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

async def interactive_prompt_stream(execution_id: ExecutionID, info: strawberry.Info[GraphQLContext]) -> AsyncGenerator[InteractivePrompt, None]:
    """Stream interactive prompts."""
    context: GraphQLContext = info.context
    state_store = context.state_store
    
    # Redis is no longer used for subscriptions
    redis_client = None
    
    if redis_client:
        # Use Redis pub/sub for real-time updates
        logger.info(f"Using Redis pub/sub for interactive prompts {execution_id}")
        subscription_manager = RedisSubscriptionManager(redis_client)
        
        try:
            async for event_data in subscription_manager.subscribe_to_execution(execution_id):
                # Filter for interactive prompt events
                if event_data.get("event_type") != EventType.INTERACTIVE_PROMPT.value:
                    continue
                
                node_id = event_data.get("node_id")
                if not node_id:
                    continue
                
                yield InteractivePrompt(
                    execution_id=execution_id,
                    node_id=NodeID(node_id),
                    prompt=event_data.get("data", {}).get('prompt', 'User input required'),
                    timeout_seconds=event_data.get("data", {}).get('timeout'),
                    timestamp=datetime.fromtimestamp(event_data["timestamp"])
                )
                
        except Exception as e:
            logger.error(f"Error in Redis interactive prompt subscription for {execution_id}: {e}")
            # Fall back to polling
    
    # Fallback to polling if Redis is not available
    logger.info(f"Using polling for interactive prompts {execution_id}")
    
    # Track processed prompts
    processed_prompts = set()
    
    try:
        while True:
            # Get latest state
            state = await state_store.get_state(execution_id)
            
            # Filter for interactive prompt events
            prompt_events = [
                e for e in events 
                if e.event_type == EventType.INTERACTIVE_PROMPT
                and e.sequence not in processed_prompts
            ]
            
            for event in prompt_events:
                processed_prompts.add(event.sequence)
                
                yield InteractivePrompt(
                    execution_id=execution_id,
                    node_id=NodeID(event.node_id),
                    prompt=event.data.get('prompt', 'User input required'),
                    timeout_seconds=event.data.get('timeout'),
                    timestamp=datetime.fromtimestamp(event.timestamp)
                )
            
            # Check if execution is complete
            state = await event_store.replay(execution_id)
            if state and state.status in ['completed', 'failed', 'aborted']:
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
        'cancelled': ExecutionStatus.ABORTED
    }
    return status_map.get(status.lower(), ExecutionStatus.STARTED)