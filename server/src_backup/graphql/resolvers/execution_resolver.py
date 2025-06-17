"""Refactored execution resolvers using Pydantic models."""
from typing import Optional, List
import logging
from datetime import datetime

from ..types.domain import ExecutionState, ExecutionEvent
from ..types.scalars import ExecutionID
from ..types.inputs import ExecutionFilterInput
from ..context import GraphQLContext
from ...domain import (
    ExecutionState as PydanticExecutionState,
    ExecutionEvent as PydanticExecutionEvent,
    TokenUsage as PydanticTokenUsage,
    ExecutionStatus
)

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
            
            # Create Pydantic model instance
            token_usage = None
            if execution_state.token_usage:
                token_usage = PydanticTokenUsage(
                    input=execution_state.token_usage.input,
                    output=execution_state.token_usage.output,
                    cached=execution_state.token_usage.cached,
                    total=execution_state.token_usage.total
                )
            
            pydantic_execution = PydanticExecutionState(
                id=execution_state.execution_id,
                status=self._map_status(execution_state.status),
                diagram_id=execution_state.diagram_id,
                started_at=execution_state.start_time,
                ended_at=execution_state.end_time,
                running_nodes=[str(n) for n in execution_state.running_nodes],
                completed_nodes=[str(n) for n in execution_state.completed_nodes],
                skipped_nodes=[str(n) for n in execution_state.skipped_nodes],
                paused_nodes=[str(n) for n in execution_state.paused_nodes],
                failed_nodes=[str(n) for n in execution_state.failed_nodes],
                node_outputs=execution_state.node_outputs,
                variables=execution_state.variables,
                token_usage=token_usage,
                error=execution_state.error
            )
            
            # Strawberry will handle the conversion from Pydantic to GraphQL
            return pydantic_execution
            
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
            
            # Convert to Pydantic ExecutionState objects
            result = []
            for exec_summary in paginated_executions:
                # Get full execution state
                execution_state = event_store.replay(exec_summary['execution_id'])
                if execution_state:
                    token_usage = None
                    if execution_state.token_usage:
                        token_usage = PydanticTokenUsage(
                            input=execution_state.token_usage.input,
                            output=execution_state.token_usage.output,
                            cached=execution_state.token_usage.cached,
                            total=execution_state.token_usage.total
                        )
                    
                    pydantic_execution = PydanticExecutionState(
                        id=execution_state.execution_id,
                        status=self._map_status(execution_state.status),
                        diagram_id=execution_state.diagram_id,
                        started_at=execution_state.start_time,
                        ended_at=execution_state.end_time,
                        running_nodes=[str(n) for n in execution_state.running_nodes],
                        completed_nodes=[str(n) for n in execution_state.completed_nodes],
                        skipped_nodes=[str(n) for n in execution_state.skipped_nodes],
                        paused_nodes=[str(n) for n in execution_state.paused_nodes],
                        failed_nodes=[str(n) for n in execution_state.failed_nodes],
                        node_outputs=execution_state.node_outputs,
                        variables=execution_state.variables,
                        token_usage=token_usage,
                        error=execution_state.error
                    )
                    result.append(pydantic_execution)
            
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
            
            # Convert to Pydantic ExecutionEvent objects
            result = []
            for event in limited_events:
                pydantic_event = PydanticExecutionEvent(
                    execution_id=event.execution_id,
                    sequence=event.sequence,
                    event_type=event.event_type,
                    node_id=str(event.node_id) if event.node_id else None,
                    timestamp=event.timestamp,
                    data=event.data
                )
                result.append(pydantic_event)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get execution events for {execution_id}: {e}")
            return []
    
    def _map_status(self, status: str) -> ExecutionStatus:
        """Map internal status string to Pydantic ExecutionStatus enum."""
        try:
            # Handle some common variations
            if status.lower() == 'cancelled':
                return ExecutionStatus.ABORTED
            return ExecutionStatus(status.lower())
        except ValueError:
            # Fallback to STARTED if unknown status
            return ExecutionStatus.STARTED

execution_resolver = ExecutionResolver()