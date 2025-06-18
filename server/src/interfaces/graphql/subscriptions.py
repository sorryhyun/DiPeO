"""GraphQL subscription definitions for real-time updates without Redis."""
import strawberry
from typing import AsyncGenerator, Optional, List
import asyncio
import logging
from datetime import datetime

from .types.domain import ExecutionState, ExecutionEvent, DomainDiagram
from .types.scalars import ExecutionID, DiagramID, NodeID, JSONScalar
from .types.enums import EventType
from src.shared.domain import NodeType, ExecutionStatus
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
                        progress=_calculate_progress(state)
                    )
                    
                    # Check if execution is complete
                    if state.status in ['completed', 'failed', 'aborted']:
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
        last_update = 0
        sequence = 0
        last_node_statuses = {}
        
        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)
                
                if state and state.last_updated > last_update:
                    # State has changed
                    last_update = state.last_updated
                    
                    # Generate events based on state changes
                    current_node_statuses = state.node_statuses or {}
                    
                    # Check for node status changes
                    for node_id, status in current_node_statuses.items():
                        old_status = last_node_statuses.get(node_id)
                        
                        if old_status != status:
                            # Node status changed
                            sequence += 1
                            event_type = _get_event_type_for_status(status)
                            
                            # Filter by event types if specified
                            if event_types and event_type not in event_types:
                                continue
                            
                            yield ExecutionEvent(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=event_type,
                                node_id=NodeID(node_id),
                                timestamp=datetime.fromtimestamp(state.last_updated),
                                data={
                                    "status": status,
                                    "output": state.node_outputs.get(node_id),
                                    "error": state.node_errors.get(node_id) if hasattr(state, 'node_errors') else None
                                }
                            )
                    
                    # Update tracked statuses
                    last_node_statuses = current_node_statuses.copy()
                    
                    # Check if execution is complete
                    if state.status in ['completed', 'failed', 'aborted']:
                        # Generate final event
                        sequence += 1
                        final_event_type = {
                            'completed': EventType.EXECUTION_COMPLETED,
                            'failed': EventType.EXECUTION_FAILED,
                            'aborted': EventType.EXECUTION_ABORTED
                        }.get(state.status, EventType.STATE_CHANGED)
                        
                        if not event_types or final_event_type in event_types:
                            yield ExecutionEvent(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=final_event_type,
                                node_id=None,
                                timestamp=datetime.fromtimestamp(state.last_updated),
                                data={"status": state.status, "error": state.error}
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
        last_update = 0
        last_node_statuses = {}
        
        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)
                
                if state and state.last_updated > last_update:
                    # State has changed
                    last_update = state.last_updated
                    
                    # Check for node status changes
                    current_node_statuses = state.node_statuses or {}
                    
                    for node_id, status in current_node_statuses.items():
                        old_status = last_node_statuses.get(node_id)
                        
                        if old_status != status:
                            # Node status changed
                            # Get node type from diagram
                            node_type = _get_node_type(state.diagram, node_id) if state.diagram else NodeType.JOB
                            
                            # Filter by node types if specified
                            if node_types and node_type not in node_types:
                                continue
                            
                            # Get node output and token usage
                            output = state.node_outputs.get(node_id)
                            tokens_used = None
                            
                            if output and isinstance(output, dict) and 'token_usage' in output:
                                tokens_used = output['token_usage'].get('total')
                            
                            yield NodeExecution(
                                execution_id=execution_id,
                                node_id=NodeID(node_id),
                                node_type=node_type,
                                status=status,
                                progress=None,  # Could calculate based on status
                                output=output,
                                error=state.node_errors.get(node_id) if hasattr(state, 'node_errors') else None,
                                tokens_used=tokens_used,
                                timestamp=datetime.fromtimestamp(state.last_updated)
                            )
                    
                    # Update tracked statuses
                    last_node_statuses = current_node_statuses.copy()
                    
                    # Check if execution is complete
                    if state.status in ['completed', 'failed', 'aborted']:
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
    ) -> AsyncGenerator[DomainDiagram, None]:
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
                
                if state and hasattr(state, 'interactive_prompts'):
                    # Check for new prompts
                    for prompt_id, prompt_data in state.interactive_prompts.items():
                        if prompt_id not in processed_prompts:
                            processed_prompts.add(prompt_id)
                            
                            yield InteractivePrompt(
                                execution_id=execution_id,
                                node_id=NodeID(prompt_data['node_id']),
                                prompt=prompt_data['prompt'],
                                timeout_seconds=prompt_data.get('timeout'),
                                timestamp=datetime.fromtimestamp(prompt_data.get('timestamp', state.last_updated))
                            )
                
                # Check if execution is complete
                if state and state.status in ['completed', 'failed', 'aborted']:
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


def _calculate_progress(state) -> float:
    """Calculate execution progress as percentage."""
    if not state.node_statuses:
        return 0.0
    
    total_nodes = len(state.node_statuses)
    completed_nodes = len([s for s in state.node_statuses.values() if s == 'completed'])
    
    return (completed_nodes / total_nodes) * 100 if total_nodes > 0 else 0.0


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
    return status_event_map.get(status, EventType.STATE_CHANGED)


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