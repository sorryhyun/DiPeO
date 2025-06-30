"""Use case for monitoring diagram executions."""

from typing import TYPE_CHECKING, Any, Optional
from collections.abc import AsyncIterator
from dipeo_core import BaseService, Result, Error
from dipeo_domain.models import ExecutionStatus, DiagramID, NodeExecutionStatus

if TYPE_CHECKING:
    from dipeo_domain.domains.ports import StateStorePort, MessageRouterPort
    from dipeo_domain.domains.execution.models import ExecutionState


class MonitorExecutionUseCase(BaseService):
    """Use case for monitoring and querying execution state."""
    
    def __init__(
        self,
        state_store: "StateStorePort",
        message_router: "MessageRouterPort",
    ):
        """Initialize with required services."""
        super().__init__()
        self.state_store = state_store
        self.message_router = message_router
    
    async def get_execution_status(
        self,
        execution_id: str,
    ) -> Result[dict[str, Any], Error]:
        """Get current status of an execution.
        
        Args:
            execution_id: ID of execution to query
            
        Returns:
            Result containing execution status or error
        """
        try:
            state = await self.state_store.get_state(execution_id)
            if not state:
                return Result.err(Error(
                    code="EXECUTION_NOT_FOUND",
                    message=f"Execution {execution_id} not found"
                ))
            
            # Build status summary
            status = {
                "execution_id": state.execution_id,
                "diagram_id": state.diagram_id,
                "status": state.status.value if hasattr(state.status, 'value') else state.status,
                "started_at": state.started_at,
                "completed_at": state.completed_at,
                "error": state.error,
                "node_states": {},
                "token_usage": state.token_usage.model_dump() if state.token_usage else None,
            }
            
            # Add node states
            for node_id, node_state in state.node_states.items():
                status["node_states"][node_id] = {
                    "status": node_state.status.value if hasattr(node_state.status, 'value') else node_state.status,
                    "started_at": node_state.started_at,
                    "completed_at": node_state.completed_at,
                    "error": node_state.error,
                    "execution_count": node_state.execution_count,
                }
            
            return Result.ok(status)
            
        except Exception as e:
            return Result.err(Error(
                code="STATUS_QUERY_ERROR",
                message=f"Failed to get execution status: {str(e)}"
            ))
    
    async def list_executions(
        self,
        diagram_id: Optional[DiagramID] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[list[dict[str, Any]], Error]:
        """List executions with optional filters.
        
        Args:
            diagram_id: Filter by diagram ID
            status: Filter by execution status
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Result containing list of executions or error
        """
        try:
            executions = await self.state_store.list_executions(
                diagram_id=diagram_id,
                status=status,
                limit=limit,
                offset=offset,
            )
            
            # Convert to simplified format
            results = []
            for exec_state in executions:
                results.append({
                    "execution_id": exec_state.execution_id,
                    "diagram_id": exec_state.diagram_id,
                    "status": exec_state.status.value if hasattr(exec_state.status, 'value') else exec_state.status,
                    "started_at": exec_state.started_at,
                    "completed_at": exec_state.completed_at,
                    "error": exec_state.error,
                })
            
            return Result.ok(results)
            
        except Exception as e:
            return Result.err(Error(
                code="LIST_EXECUTIONS_ERROR",
                message=f"Failed to list executions: {str(e)}"
            ))
    
    async def get_node_outputs(
        self,
        execution_id: str,
        node_id: Optional[str] = None,
    ) -> Result[dict[str, Any], Error]:
        """Get outputs for execution nodes.
        
        Args:
            execution_id: ID of execution
            node_id: Optional specific node ID
            
        Returns:
            Result containing node outputs or error
        """
        try:
            state = await self.state_store.get_state(execution_id)
            if not state:
                return Result.err(Error(
                    code="EXECUTION_NOT_FOUND",
                    message=f"Execution {execution_id} not found"
                ))
            
            if node_id:
                # Get specific node output
                output = state.node_outputs.get(node_id)
                if not output:
                    return Result.err(Error(
                        code="NODE_OUTPUT_NOT_FOUND",
                        message=f"No output found for node {node_id}"
                    ))
                return Result.ok({node_id: output.model_dump()})
            else:
                # Get all node outputs
                outputs = {
                    nid: output.model_dump()
                    for nid, output in state.node_outputs.items()
                }
                return Result.ok(outputs)
                
        except Exception as e:
            return Result.err(Error(
                code="OUTPUT_QUERY_ERROR",
                message=f"Failed to get node outputs: {str(e)}"
            ))
    
    async def stream_execution_updates(
        self,
        execution_id: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream real-time updates for an execution.
        
        Args:
            execution_id: ID of execution to monitor
            
        Yields:
            Execution update events
        """
        # Subscribe to message router for this execution
        async for update in self.message_router.subscribe(execution_id):
            yield update
    
    async def cancel_execution(
        self,
        execution_id: str,
    ) -> Result[bool, Error]:
        """Cancel a running execution.
        
        Args:
            execution_id: ID of execution to cancel
            
        Returns:
            Result indicating success or error
        """
        try:
            # Update state to cancelled
            state = await self.state_store.get_state(execution_id)
            if not state:
                return Result.err(Error(
                    code="EXECUTION_NOT_FOUND",
                    message=f"Execution {execution_id} not found"
                ))
            
            # Check if already completed
            if state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
                return Result.err(Error(
                    code="EXECUTION_ALREADY_FINISHED",
                    message=f"Execution {execution_id} already {state.status}"
                ))
            
            # Send cancellation message
            await self.message_router.publish(execution_id, {
                "type": "execution_cancelled",
                "execution_id": execution_id,
            })
            
            return Result.ok(True)
            
        except Exception as e:
            return Result.err(Error(
                code="CANCEL_ERROR",
                message=f"Failed to cancel execution: {str(e)}"
            ))