"""Refactored execution-related GraphQL mutations using Pydantic models."""
import strawberry
import logging
import uuid
from datetime import datetime

from .results_types import ExecutionResult
from .inputs_types import ExecuteDiagramInput, ExecutionControlInput, InteractiveResponseInput
from .context import GraphQLContext
from dipeo_server.domains.diagram.models import ExecutionState as ExecutionStateForGraphQL
from dipeo_server.core import ExecutionStatus
from .models.input_models import (
    ExecuteDiagramInput as PydanticExecuteDiagramInput,
    ExecutionControlInput as PydanticExecutionControlInput,
    InteractiveResponseInput as PydanticInteractiveResponseInput
)

logger = logging.getLogger(__name__)


@strawberry.type
class ExecutionMutations:
    """Mutations for diagram execution operations."""
    
    @strawberry.mutation
    async def execute_diagram(self, input: ExecuteDiagramInput, info) -> ExecutionResult:
        """Start executing a diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            execution_service = context.execution_service
            state_store = context.state_store
            message_router = context.message_router
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticExecuteDiagramInput(
                diagram_id=input.diagram_id,
                diagram_data=input.diagram_data,
                debug_mode=input.debug_mode,
                max_iterations=input.max_iterations,
                timeout_seconds=input.timeout_seconds
            )
            
            # Get diagram data either from ID or directly from input
            if pydantic_input.diagram_data:
                # Use provided diagram data directly (in-memory execution)
                diagram_data = pydantic_input.diagram_data
            elif pydantic_input.diagram_id:
                # Load diagram from file system
                diagram_data = diagram_service.load_diagram(pydantic_input.diagram_id)
                if not diagram_data:
                    return ExecutionResult(
                        success=False,
                        error="Diagram not found"
                    )
            else:
                return ExecutionResult(
                    success=False,
                    error="No diagram data provided"
                )
            
            # Generate execution ID
            execution_id = str(uuid.uuid4())
            
            # Prepare options with validated values
            options = {
                'debugMode': pydantic_input.debug_mode,
                'maxIterations': pydantic_input.max_iterations,  # Already validated >= 1
                'timeout': pydantic_input.timeout_seconds  # Already validated >= 1
            }
            
            # Create initial execution state
            await state_store.create_execution(execution_id, diagram_data, options)
            
            # Start execution in background
            # Note: In a real implementation, this would start the execution
            # asynchronously and return immediately. The client would then
            # subscribe to updates via GraphQL subscriptions.
            
            # Create Pydantic execution state model
            execution = ExecutionStateForGraphQL(
                id=execution_id,
                status=ExecutionStatus.STARTED,
                diagram_id=pydantic_input.diagram_id,
                started_at=datetime.now().isoformat(),
                ended_at=None,
                running_nodes=[],
                completed_nodes=[],
                skipped_nodes=[],
                paused_nodes=[],
                failed_nodes=[],
                node_outputs={},
                variables={},
                token_usage=None,
                error=None
            )
            
            return ExecutionResult(
                success=True,
                execution=execution,  # Strawberry will handle conversion
                execution_id=execution_id,
                message=f"Started execution {execution_id}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error executing diagram: {e}")
            return ExecutionResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to execute diagram: {e}")
            return ExecutionResult(
                success=False,
                error=f"Failed to execute diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def control_execution(
        self, 
        input: ExecutionControlInput,
        info
    ) -> ExecutionResult:
        """Control a running execution (pause, resume, abort, skip)."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticExecutionControlInput(
                execution_id=input.execution_id,
                action=input.action,
                node_id=input.node_id
            )
            
            # Check if execution exists
            state = await state_store.get_state(pydantic_input.execution_id)
            if not state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {pydantic_input.execution_id} not found"
                )
            
            # Update state based on action
            if pydantic_input.action == 'pause':
                if pydantic_input.node_id:
                    await state_store.update_node_status(pydantic_input.execution_id, pydantic_input.node_id, 'paused')
                else:
                    await state_store.update_status(pydantic_input.execution_id, 'paused')
            elif pydantic_input.action == 'resume':
                if pydantic_input.node_id:
                    await state_store.update_node_status(pydantic_input.execution_id, pydantic_input.node_id, 'resumed')
                else:
                    await state_store.update_status(pydantic_input.execution_id, 'started')
            elif pydantic_input.action == 'abort':
                await state_store.update_status(pydantic_input.execution_id, 'aborted')
            elif pydantic_input.action == 'skip' and pydantic_input.node_id:
                await state_store.update_node_status(pydantic_input.execution_id, pydantic_input.node_id, 'skipped')
            
            # Broadcast control message via message router
            control_message = {
                'type': f'{pydantic_input.action}_{"node" if pydantic_input.node_id else "execution"}',
                'execution_id': pydantic_input.execution_id,
                'node_id': pydantic_input.node_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Route message to execution
            await message_router.broadcast_to_execution(pydantic_input.execution_id, control_message)
            
            # Get updated state
            updated_state = await state_store.get_state(pydantic_input.execution_id)
            
            # Convert to GraphQL execution state
            execution_state = ExecutionStateForGraphQL(
                id=pydantic_input.execution_id,
                status=_map_status(updated_state.status),
                diagram_id=updated_state.diagram.get('id'),
                started_at=datetime.fromtimestamp(updated_state.start_time).isoformat(),
                ended_at=datetime.fromtimestamp(updated_state.end_time).isoformat() if updated_state.end_time else None,
                running_nodes=[nid for nid, status in updated_state.node_statuses.items() if status == 'started'],
                completed_nodes=[nid for nid, status in updated_state.node_statuses.items() if status == 'completed'],
                skipped_nodes=updated_state.skipped_nodes,
                paused_nodes=updated_state.paused_nodes,
                failed_nodes=[nid for nid, status in updated_state.node_statuses.items() if status == 'failed'],
                node_outputs=updated_state.node_outputs,
                variables=updated_state.variables,
                token_usage=None,
                error=updated_state.error
            )
            
            return ExecutionResult(
                success=True,
                execution=execution_state,  # Strawberry will handle conversion
                message=f"Execution control '{pydantic_input.action}' sent successfully"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error controlling execution: {e}")
            return ExecutionResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to control execution: {e}")
            return ExecutionResult(
                success=False,
                error=f"Failed to control execution: {str(e)}"
            )
    
    @strawberry.mutation
    async def submit_interactive_response(
        self,
        input: InteractiveResponseInput,
        info
    ) -> ExecutionResult:
        """Submit a response to an interactive prompt."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticInteractiveResponseInput(
                execution_id=input.execution_id,
                node_id=input.node_id,
                response=input.response
            )
            
            # Check if execution exists by getting its state
            execution_state = await state_store.get_state(pydantic_input.execution_id)
            if not execution_state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {pydantic_input.execution_id} not found"
                )
            
            # Check if execution is still running
            if execution_state.status not in ['started', 'running']:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {pydantic_input.execution_id} is not running (status: {execution_state.status})"
                )
            
            # Clear interactive prompt after receiving response
            await state_store.clear_interactive_prompt(pydantic_input.execution_id)
            
            # Route the interactive response message to subscribed handlers
            interactive_message = {
                'type': 'interactive_response',
                'executionId': pydantic_input.execution_id,
                'nodeId': pydantic_input.node_id,
                'response': pydantic_input.response,
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast to all connections subscribed to this execution
            await message_router.broadcast_to_execution(pydantic_input.execution_id, interactive_message)
            
            # Get updated execution state
            updated_state = await state_store.get_state(pydantic_input.execution_id)
            
            # Convert to Pydantic ExecutionState model
            execution = ExecutionStateForGraphQL(
                id=pydantic_input.execution_id,
                status=_map_status(updated_state.status),
                diagram_id=updated_state.diagram.get('id', ''),
                started_at=datetime.fromtimestamp(updated_state.start_time).isoformat(),
                ended_at=datetime.fromtimestamp(updated_state.end_time).isoformat() if updated_state.end_time else None,
                running_nodes=[node_id for node_id, status in updated_state.node_statuses.items() if status == 'started'],
                completed_nodes=[node_id for node_id, status in updated_state.node_statuses.items() if status == 'completed'],
                skipped_nodes=list(updated_state.skipped_nodes),
                paused_nodes=list(updated_state.paused_nodes),
                failed_nodes=[node_id for node_id, status in updated_state.node_statuses.items() if status == 'failed'],
                node_outputs=updated_state.node_outputs,
                variables=updated_state.variables,
                token_usage=None,  # Would need to convert token usage format
                error=updated_state.error
            )
            
            return ExecutionResult(
                success=True,
                execution=execution,  # Strawberry will handle conversion
                message=f"Interactive response submitted for node {pydantic_input.node_id}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error submitting response: {e}")
            return ExecutionResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to submit interactive response: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                error=f"Failed to submit interactive response: {str(e)}"
            )


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


def _map_action_to_status(action: str, current_status: str) -> ExecutionStatus:
    """Map control action to new execution status."""
    # Map current status string to enum first
    current = _map_status(current_status)
    
    # Determine new status based on action
    action_map = {
        'pause': ExecutionStatus.PAUSED,
        'resume': ExecutionStatus.RUNNING,
        'abort': ExecutionStatus.ABORTED,
        'cancel': ExecutionStatus.ABORTED,
        'skip_node': current,  # Skip doesn't change overall execution status
    }
    
    return action_map.get(action.lower(), current)