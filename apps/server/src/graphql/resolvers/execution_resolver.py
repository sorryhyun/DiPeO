"""Execution resolvers for GraphQL queries and mutations."""
from typing import Optional, List
import logging
from datetime import datetime

from ..types.domain import ExecutionState, ExecutionEvent, TokenUsage
from ..types.scalars import ExecutionID, NodeID
from ..types.inputs import ExecutionFilterInput
from ..types.enums import ExecutionStatus
from ..context import GraphQLContext

logger = logging.getLogger(__name__)

class ExecutionResolver:
    """Resolver for execution-related queries and mutations."""
    
    async def get_execution(self, execution_id: ExecutionID, info) -> Optional[ExecutionState]:
        """Get a single execution by ID."""
        try:
            context: GraphQLContext = info.context
            event_store = context.event_store
            
            # Replay execution state from events
            execution_state = event_store.replay(execution_id)
            
            if not execution_state:
                logger.debug(f"No execution found with ID: {execution_id}")
                return None
            
            # Convert internal state to GraphQL ExecutionState
            return ExecutionState(
                id=execution_state.execution_id,
                status=self._map_status(execution_state.status),
                diagram_id=execution_state.diagram_id,
                started_at=execution_state.start_time,
                ended_at=execution_state.end_time,
                running_nodes=[NodeID(n) for n in execution_state.running_nodes],
                completed_nodes=[NodeID(n) for n in execution_state.completed_nodes],
                skipped_nodes=[NodeID(n) for n in execution_state.skipped_nodes],
                paused_nodes=[NodeID(n) for n in execution_state.paused_nodes],
                failed_nodes=[NodeID(n) for n in execution_state.failed_nodes],
                node_outputs=execution_state.node_outputs,
                variables=execution_state.variables,
                token_usage=TokenUsage(
                    input=execution_state.token_usage.input,
                    output=execution_state.token_usage.output,
                    cached=execution_state.token_usage.cached,
                    total=execution_state.token_usage.total
                ) if execution_state.token_usage else None,
                error=execution_state.error
            )
            
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            return None
    
    async def list_executions(
        self,
        filter: Optional[ExecutionFilterInput],
        limit: int,
        offset: int,
        info
    ) -> List[ExecutionState]:
        """List executions with optional filtering."""
        try:
            context: GraphQLContext = info.context
            event_store = context.event_store
            
            # Get all executions from event store
            executions = event_store.list_executions(limit=limit + offset)
            
            # Apply filtering if provided
            filtered_executions = executions
            if filter:
                # Filter by status
                if filter.status:
                    filtered_executions = [
                        e for e in filtered_executions
                        if self._map_status(e['status']) == filter.status
                    ]
                
                # Filter by diagram ID
                if filter.diagram_id:
                    filtered_executions = [
                        e for e in filtered_executions
                        if e.get('diagram_id') == filter.diagram_id
                    ]
                
                # Filter by date range
                if filter.started_after:
                    filtered_executions = [
                        e for e in filtered_executions
                        if datetime.fromisoformat(e['started_at']) >= filter.started_after
                    ]
                
                if filter.started_before:
                    filtered_executions = [
                        e for e in filtered_executions
                        if datetime.fromisoformat(e['started_at']) <= filter.started_before
                    ]
            
            # Apply pagination
            paginated_executions = filtered_executions[offset:offset + limit]
            
            # Convert to GraphQL ExecutionState objects
            result = []
            for exec_summary in paginated_executions:
                # Get full execution state
                execution_state = event_store.replay(exec_summary['execution_id'])
                if execution_state:
                    result.append(ExecutionState(
                        id=execution_state.execution_id,
                        status=self._map_status(execution_state.status),
                        diagram_id=execution_state.diagram_id,
                        started_at=execution_state.start_time,
                        ended_at=execution_state.end_time,
                        running_nodes=[NodeID(n) for n in execution_state.running_nodes],
                        completed_nodes=[NodeID(n) for n in execution_state.completed_nodes],
                        skipped_nodes=[NodeID(n) for n in execution_state.skipped_nodes],
                        paused_nodes=[NodeID(n) for n in execution_state.paused_nodes],
                        failed_nodes=[NodeID(n) for n in execution_state.failed_nodes],
                        node_outputs=execution_state.node_outputs,
                        variables=execution_state.variables,
                        token_usage=TokenUsage(
                            input=execution_state.token_usage.input,
                            output=execution_state.token_usage.output,
                            cached=execution_state.token_usage.cached,
                            total=execution_state.token_usage.total
                        ) if execution_state.token_usage else None,
                        error=execution_state.error
                    ))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            return []
    
    async def get_execution_events(
        self,
        execution_id: ExecutionID,
        since_sequence: Optional[int],
        limit: int,
        info
    ) -> List[ExecutionEvent]:
        """Get execution events for a specific execution."""
        try:
            context: GraphQLContext = info.context
            event_store = context.event_store
            
            # Get all events for this execution
            all_events = event_store.get_events(execution_id)
            
            # Filter by sequence if provided
            if since_sequence is not None:
                all_events = [e for e in all_events if e.sequence > since_sequence]
            
            # Apply limit
            limited_events = all_events[:limit] if limit > 0 else all_events
            
            # Convert to GraphQL ExecutionEvent objects
            result = []
            for event in limited_events:
                result.append(ExecutionEvent(
                    execution_id=event.execution_id,
                    sequence=event.sequence,
                    event_type=event.event_type,
                    node_id=NodeID(event.node_id) if event.node_id else None,
                    timestamp=event.timestamp,
                    data=event.data
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get execution events for {execution_id}: {e}")
            return []
    
    def _map_status(self, status: str) -> ExecutionStatus:
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

execution_resolver = ExecutionResolver()