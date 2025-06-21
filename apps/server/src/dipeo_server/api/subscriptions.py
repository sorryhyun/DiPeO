"""GraphQL subscription definitions for real-time updates without Redis."""
import strawberry
from typing import AsyncGenerator, Optional, List
import asyncio
import logging
from datetime import datetime

from .scalars_types import ExecutionID, DiagramID, NodeID, JSONScalar
from .domain_types import ExecutionState, ExecutionEvent, DomainDiagramType
from dipeo_server.core import NodeType, ExecutionStatus
from dipeo_domain import EventType, NodeExecutionStatus
from dipeo_domain import ExecutionState as PydanticExecutionState
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
    """Root subscription type for DiPeO GraphQL API using polling."""
    
    @strawberry.subscription
    async def execution_updates(
        self, 
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID
    ) -> AsyncGenerator[ExecutionState, None]:
        """Subscribe to execution state updates using polling."""
        context: GraphQLContext = info.context
        state_store = context.state_store
        
        logger.info(f"Starting execution updates subscription for {execution_id}")
        
        # Track last update time
        last_update = 0
        
        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)
                
                if state:
                    # The state store now returns PydanticExecutionState directly
                    # Just yield it - Strawberry will handle the conversion
                    yield state
                    
                    # Check if execution is complete
                    if state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.ABORTED]:
                        logger.info(f"Execution {execution_id} completed with status: {state.status}")
                        break
                
                # Poll interval (100ms)
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in execution stream for {execution_id}: {e}")
            raise
    
    @strawberry.subscription
    async def execution_events(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        event_types: Optional[List[EventType]] = None
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Subscribe to specific execution events using state changes."""
        context: GraphQLContext = info.context
        state_store = context.state_store
        
        logger.info(f"Starting event stream subscription for {execution_id}")
        
        # Track last update and node states
        sequence = 0
        last_node_states = {}
        
        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)
                
                if state:
                    # Generate events based on state changes
                    current_node_states = state.node_states or {}
                    
                    # Check for node status changes
                    for node_id, node_state in current_node_states.items():
                        old_state = last_node_states.get(node_id)
                        
                        if not old_state or old_state.status != node_state.status:
                            # Node status changed
                            sequence += 1
                            event_type = _get_event_type_for_node_status(node_state.status)
                            
                            # Filter by event types if specified
                            if event_types and event_type not in event_types:
                                continue
                            
                            # Get node output if available
                            node_output = state.node_outputs.get(node_id)
                            output_value = node_output.value if node_output else None
                            
                            yield ExecutionEvent(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=event_type,
                                node_id=NodeID(node_id),
                                timestamp=node_state.ended_at or node_state.started_at or datetime.now().isoformat(),
                                data={
                                    "status": node_state.status.value,
                                    "output": output_value,
                                    "error": node_state.error
                                }
                            )
                    
                    # Update tracked states
                    last_node_states = current_node_states.copy()
                    
                    # Check if execution is complete
                    if state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.ABORTED]:
                        # Generate final event
                        sequence += 1
                        final_event_type = {
                            ExecutionStatus.COMPLETED: EventType.EXECUTION_COMPLETED,
                            ExecutionStatus.FAILED: EventType.EXECUTION_FAILED,
                            ExecutionStatus.ABORTED: EventType.EXECUTION_ABORTED
                        }.get(state.status, EventType.EXECUTION_UPDATE)
                        
                        if not event_types or final_event_type in event_types:
                            yield ExecutionEvent(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=final_event_type,
                                node_id=None,
                                timestamp=datetime.fromtimestamp(state.last_updated).isoformat(),
                                data={"status": state.status.value, "error": state.error}
                            )
                        
                        logger.info(f"Event stream completed for execution {execution_id}")
                        break
                
                # Poll interval (100ms)
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"Event subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in event stream for {execution_id}: {e}")
            raise
    
    @strawberry.subscription
    async def node_updates(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        node_types: Optional[List[NodeType]] = None
    ) -> AsyncGenerator[NodeExecution, None]:
        """Subscribe to node execution updates, optionally filtered by type."""
        context: GraphQLContext = info.context
        state_store = context.state_store
        
        logger.info(f"Starting node updates subscription for {execution_id}")
        
        # Track last update and node states
        last_node_states = {}
        
        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)
                
                if state:
                    # Check for node status changes
                    current_node_states = state.node_states or {}
                    
                    for node_id, node_state in current_node_states.items():
                        old_state = last_node_states.get(node_id)
                        
                        if not old_state or old_state.status != node_state.status:
                            # Node status changed
                            # Get node type from diagram metadata if available
                            node_type = NodeType.JOB  # Default
                            
                            # Filter by node types if specified
                            if node_types and node_type not in node_types:
                                continue
                            
                            # Get node output and token usage
                            node_output = state.node_outputs.get(node_id)
                            output_value = node_output.value if node_output else None
                            tokens_used = None
                            
                            if node_state.token_usage:
                                tokens_used = node_state.token_usage.total
                            
                            yield NodeExecution(
                                execution_id=execution_id,
                                node_id=NodeID(node_id),
                                node_type=node_type,
                                status=node_state.status.value,
                                progress=None,  # Could calculate based on status
                                output=output_value,
                                error=node_state.error,
                                tokens_used=tokens_used,
                                timestamp=datetime.fromisoformat(node_state.ended_at or node_state.started_at or datetime.now().isoformat())
                            )
                    
                    # Update tracked states
                    last_node_states = current_node_states.copy()
                    
                    # Check if execution is complete
                    if state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.ABORTED]:
                        logger.info(f"Node updates completed for execution {execution_id}")
                        break
                
                # Poll interval (100ms)
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"Node update subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in node update stream for {execution_id}: {e}")
            raise
    
    @strawberry.subscription
    async def diagram_changes(
        self,
        info: strawberry.Info[GraphQLContext],
        diagram_id: DiagramID
    ) -> AsyncGenerator[DomainDiagramType, None]:
        """Subscribe to diagram changes - placeholder for future implementation."""
        logger.warning(f"Diagram change stream not yet implemented for {diagram_id}")
        # This would require file watching or version control integration
        while False:  # Never yields
            yield
    
    @strawberry.subscription
    async def interactive_prompts(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID
    ) -> AsyncGenerator[InteractivePrompt, None]:
        """Subscribe to interactive prompts that need user input."""
        context: GraphQLContext = info.context
        state_store = context.state_store
        
        logger.info(f"Starting interactive prompts subscription for {execution_id}")
        
        # Track processed prompts
        processed_prompts = set()
        
        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)
                
                # The new state model doesn't have interactive_prompts field
                # This feature needs to be reimplemented if needed
                
                # Check if execution is complete
                if state and state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.ABORTED]:
                    logger.info(f"Interactive prompts completed for execution {execution_id}")
                    break
                
                # Poll interval (100ms)
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"Interactive prompt subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in interactive prompt stream for {execution_id}: {e}")
            raise


# Helper functions
def _map_status(status: str) -> ExecutionStatus:
    """Map internal status string to GraphQL ExecutionStatus enum."""
    status_map = {
        'started': ExecutionStatus.STARTED,
        'running': ExecutionStatus.RUNNING,
        'paused': ExecutionStatus.PAUSED,
        'completed': ExecutionStatus.COMPLETED,
        'failed': ExecutionStatus.FAILED,
        'cancelled': ExecutionStatus.ABORTED,
        'aborted': ExecutionStatus.ABORTED
    }
    return status_map.get(status.lower(), ExecutionStatus.STARTED)


def _get_event_type_for_status(status: str) -> EventType:
    """Map node status to event type."""
    status_event_map = {
        'started': EventType.NODE_STARTED,
        'running': EventType.NODE_RUNNING,
        'completed': EventType.NODE_COMPLETED,
        'failed': EventType.NODE_FAILED,
        'skipped': EventType.NODE_SKIPPED,
        'paused': EventType.NODE_PAUSED
    }
    return status_event_map.get(status, EventType.EXECUTION_UPDATE)


def _get_event_type_for_node_status(status: NodeExecutionStatus) -> EventType:
    """Map NodeExecutionStatus enum to EventType."""
    status_event_map = {
        NodeExecutionStatus.PENDING: EventType.NODE_STARTED,
        NodeExecutionStatus.RUNNING: EventType.NODE_RUNNING,
        NodeExecutionStatus.COMPLETED: EventType.NODE_COMPLETED,
        NodeExecutionStatus.FAILED: EventType.NODE_FAILED,
        NodeExecutionStatus.SKIPPED: EventType.NODE_SKIPPED,
        NodeExecutionStatus.PAUSED: EventType.NODE_PAUSED
    }
    return status_event_map.get(status, EventType.EXECUTION_UPDATE)


def _get_node_type(diagram: dict, node_id: str) -> NodeType:
    """Extract node type from diagram data."""
    if not diagram or 'nodes' not in diagram:
        return NodeType.JOB
    
    node = diagram['nodes'].get(node_id, {})
    node_type_str = node.get('type', 'job')
    
    # Map string to NodeType enum
    try:
        return NodeType(node_type_str)
    except ValueError:
        return NodeType.JOB