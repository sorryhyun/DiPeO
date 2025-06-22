"""GraphQL mutations for diagram execution operations."""
import strawberry
import logging
import uuid
from datetime import datetime

from .results_types import ExecutionResult
from .inputs_types import ExecuteDiagramInput, ExecutionControlInput, InteractiveResponseInput
from .context import GraphQLContext
from dipeo_domain import ExecutionState as ExecutionStateForGraphQL, TokenUsage, ExecutionID, DiagramID
from dipeo_server.core import ExecutionStatus
from dipeo_domain import NodeExecutionStatus, ExecutionStatus as DomainExecutionStatus
from .models.input_models import (
    ExecuteDiagramInput as PydanticExecuteDiagramInput,
    ExecutionControlInput as PydanticExecutionControlInput,
    InteractiveResponseInput as PydanticInteractiveResponseInput
)

logger = logging.getLogger(__name__)


@strawberry.type
class ExecutionMutations:
    """Handles diagram execution via GraphQL API."""
    
    @strawberry.mutation
    async def execute_diagram(self, input: ExecuteDiagramInput, info) -> ExecutionResult:
        """Starts diagram execution with provided configuration."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            execution_service = context.execution_service
            state_store = context.state_store
            message_router = context.message_router
            
            pydantic_input = PydanticExecuteDiagramInput(
                diagram_id=input.diagram_id,
                diagram_data=input.diagram_data,
                debug_mode=input.debug_mode,
                max_iterations=input.max_iterations,
                timeout_seconds=input.timeout_seconds
            )
            
            if pydantic_input.diagram_data:
                diagram_data = pydantic_input.diagram_data
            elif pydantic_input.diagram_id:
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
            
            execution_id = str(uuid.uuid4())
            
            options = {
                'debugMode': pydantic_input.debug_mode,
                'maxIterations': pydantic_input.max_iterations,
                'timeout': pydantic_input.timeout_seconds
            }
            
            diagram_id = pydantic_input.diagram_id if pydantic_input.diagram_id else None
            await state_store.create_execution(execution_id, diagram_id, options)
            
            # Execution starts asynchronously; client monitors via subscriptions
            execution = ExecutionStateForGraphQL(
                id=ExecutionID(execution_id),
                status=DomainExecutionStatus.STARTED,
                diagram_id=DiagramID(diagram_id) if diagram_id else None,
                started_at=datetime.now().isoformat(),
                ended_at=None,
                node_states={},
                node_outputs={},
                token_usage=TokenUsage(input=0, output=0, cached=None, total=0),
                error=None,
                variables={}
            )
            
            return ExecutionResult(
                success=True,
                execution=execution,
                execution_id=execution_id,
                message=f"Started execution {execution_id}"
            )
            
        except ValueError as e:
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
        """Controls execution state (pause/resume/abort/skip)."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router
            
            pydantic_input = PydanticExecutionControlInput(
                execution_id=input.execution_id,
                action=input.action,
                node_id=input.node_id
            )
            
            state = await state_store.get_state(pydantic_input.execution_id)
            if not state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {pydantic_input.execution_id} not found"
                )
            
            if pydantic_input.action == 'pause':
                if pydantic_input.node_id:
                    await state_store.update_node_status(pydantic_input.execution_id, pydantic_input.node_id, NodeExecutionStatus.PAUSED)
                else:
                    await state_store.update_status(pydantic_input.execution_id, DomainExecutionStatus.PAUSED)
            elif pydantic_input.action == 'resume':
                if pydantic_input.node_id:
                    await state_store.update_node_status(pydantic_input.execution_id, pydantic_input.node_id, NodeExecutionStatus.RUNNING)
                else:
                    await state_store.update_status(pydantic_input.execution_id, DomainExecutionStatus.RUNNING)
            elif pydantic_input.action == 'abort':
                await state_store.update_status(pydantic_input.execution_id, DomainExecutionStatus.ABORTED)
            elif pydantic_input.action == 'skip' and pydantic_input.node_id:
                await state_store.update_node_status(pydantic_input.execution_id, pydantic_input.node_id, NodeExecutionStatus.SKIPPED, skip_reason='Manual skip')
            
            control_message = {
                'type': f'{pydantic_input.action}_{"node" if pydantic_input.node_id else "execution"}',
                'execution_id': pydantic_input.execution_id,
                'node_id': pydantic_input.node_id,
                'timestamp': datetime.now().isoformat()
            }
            
            await message_router.broadcast_to_execution(pydantic_input.execution_id, control_message)
            
            updated_state = await state_store.get_state(pydantic_input.execution_id)
            
            execution_state = ExecutionStateForGraphQL(
                id=ExecutionID(pydantic_input.execution_id),
                status=updated_state.status,
                diagram_id=updated_state.diagram_id,
                started_at=updated_state.started_at,
                ended_at=updated_state.ended_at,
                node_states=updated_state.node_states,
                node_outputs=updated_state.node_outputs,
                token_usage=updated_state.token_usage or TokenUsage(input=0, output=0, cached=None, total=0),
                error=updated_state.error,
                variables=updated_state.variables
            )
            
            return ExecutionResult(
                success=True,
                execution=execution_state,
                message=f"Execution control '{pydantic_input.action}' sent successfully"
            )
            
        except ValueError as e:
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
        """Handles interactive node responses from users."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router
            
            pydantic_input = PydanticInteractiveResponseInput(
                execution_id=input.execution_id,
                node_id=input.node_id,
                response=input.response
            )
            
            execution_state = await state_store.get_state(pydantic_input.execution_id)
            if not execution_state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {pydantic_input.execution_id} not found"
                )
            
            if execution_state.status not in [DomainExecutionStatus.STARTED, DomainExecutionStatus.RUNNING]:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {pydantic_input.execution_id} is not running (status: {execution_state.status})"
                )
            
            interactive_message = {
                'type': 'interactive_response',
                'executionId': pydantic_input.execution_id,
                'nodeId': pydantic_input.node_id,
                'response': pydantic_input.response,
                'timestamp': datetime.now().isoformat()
            }
            
            await message_router.broadcast_to_execution(pydantic_input.execution_id, interactive_message)
            
            updated_state = await state_store.get_state(pydantic_input.execution_id)
            
            execution = ExecutionStateForGraphQL(
                id=ExecutionID(pydantic_input.execution_id),
                status=updated_state.status,
                diagram_id=updated_state.diagram_id,
                started_at=updated_state.started_at,
                ended_at=updated_state.ended_at,
                node_states=updated_state.node_states,
                node_outputs=updated_state.node_outputs,
                token_usage=updated_state.token_usage or TokenUsage(input=0, output=0, cached=None, total=0),
                error=updated_state.error,
                variables=updated_state.variables
            )
            
            return ExecutionResult(
                success=True,
                execution=execution,
                message=f"Interactive response submitted for node {pydantic_input.node_id}"
            )
            
        except ValueError as e:
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
    """Maps status string to ExecutionStatus enum."""
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
    """Maps control action to execution status."""
    current = _map_status(current_status)
    action_map = {
        'pause': ExecutionStatus.PAUSED,
        'resume': ExecutionStatus.RUNNING,
        'abort': ExecutionStatus.ABORTED,
        'cancel': ExecutionStatus.ABORTED,
        'skip_node': current,
    }
    
    return action_map.get(action.lower(), current)