"""Refactored execution resolvers using Pydantic models."""
from typing import Optional, List
import logging
from datetime import datetime

from ..types.domain import ExecutionState, ExecutionEvent
from ..types.scalars import ExecutionID
from ..types.inputs import ExecutionFilterInput
from ..context import GraphQLContext
from src.__generated__.models import (
    ExecutionState as PydanticExecutionState,
    ExecutionEvent as PydanticExecutionEvent,
    NodeExecutionStatus,
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
            state_store = context.state_store
            
            # Get execution state - now returns generated ExecutionState directly
            execution_state = await state_store.get_state(execution_id)
            
            if not execution_state:
                logger.debug(f"No execution found with ID: {execution_id}")
                return None
            
            # The state store now returns the Pydantic ExecutionState directly
            # Just return it - Strawberry will handle the conversion
            return execution_state
            
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
            state_store = context.state_store
            
            # Get all executions from state store
            executions = await state_store.list_executions(limit=limit + offset)
            
            # Apply filtering if provided
            filtered_executions = executions
            if filter:
                # Filter by status
                if filter.status:
                    filtered_executions = [
                        e for e in filtered_executions
                        if e['status'] == filter.status.value
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
                execution_state = await state_store.get_state(exec_summary['execution_id'])
                if execution_state:
                    result.append(execution_state)
            
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
        # Events are no longer stored with the new SimpleStateStore
        # This method returns an empty list for backward compatibility
        logger.info(f"get_execution_events called for {execution_id} - returning empty list (events no longer stored)")
        return []
    
execution_resolver = ExecutionResolver()