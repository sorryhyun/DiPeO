"""GraphQL mutations for diagram execution operations."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

import strawberry
from dipeo_domain import (
    DiagramID,
    ExecutionID,
    ExecutionStatus,
    NodeExecutionStatus,
    TokenUsage,
)
from dipeo_domain import (
    ExecutionState as ExecutionStateForGraphQL,
)
from dipeo_domain import ExecutionStatus as DomainExecutionStatus

from ..context import GraphQLContext
from ..types import (
    ExecuteDiagramInput,
    ExecutionControlInput,
    ExecutionResult,
    InteractiveResponseInput,
)

logger = logging.getLogger(__name__)


@strawberry.type
class ExecutionMutations:
    """Handles diagram execution via GraphQL API."""

    @strawberry.mutation
    async def execute_diagram(
        self, input: ExecuteDiagramInput, info
    ) -> ExecutionResult:
        """Starts diagram execution with provided configuration."""
        try:
            context: GraphQLContext = info.context
            execution_service = context.execution_service
            state_store = context.state_store

            if input.diagram_data:
                diagram_data = input.diagram_data
                # The execution service expects dict format, so we don't need to convert
            elif input.diagram_id:
                # Use new services
                storage_service = context.diagram_storage_service
                path = await storage_service.find_by_id(input.diagram_id)
                if path:
                    diagram_data = await storage_service.read_file(path)
                else:
                    return ExecutionResult(success=False, error="Diagram not found")
            else:
                return ExecutionResult(success=False, error="No diagram data provided")

            execution_id = str(uuid.uuid4())

            options = {
                "debugMode": input.debug_mode,
                "maxIterations": input.max_iterations,
                "timeout": input.timeout_seconds,
            }

            diagram_id = (
                input.diagram_id if input.diagram_id else None
            )
            await state_store.create_execution(execution_id, diagram_id, options)

            # Start the actual execution asynchronously
            async def run_execution():
                try:
                    logger.info(f"Starting run_execution for {execution_id}")
                    async for update in execution_service.execute_diagram(
                        diagram=diagram_data,
                        options=options,
                        execution_id=execution_id
                    ):
                        # Updates are handled by the execution service
                        pass
                except Exception as e:
                    logger.error(f"Execution failed for {execution_id}: {e}")
                    await state_store.update_status(
                        execution_id, DomainExecutionStatus.FAILED, error=str(e)
                    )

            # Launch execution in background
            asyncio.create_task(run_execution())

            # Execution starts asynchronously; client monitors via subscriptions
            execution = ExecutionStateForGraphQL(
                id=ExecutionID(execution_id),
                status=DomainExecutionStatus.STARTED,
                diagram_id=DiagramID(diagram_id) if diagram_id else None,
                started_at=datetime.now(timezone.utc).isoformat(),
                ended_at=None,
                node_states={},
                node_outputs={},
                token_usage=TokenUsage(input=0, output=0, cached=None, total=0),
                error=None,
                variables={},
            )

            return ExecutionResult(
                success=True,
                execution=execution,
                execution_id=execution_id,
                message=f"Started execution {execution_id}",
            )

        except ValueError as e:
            logger.error(f"Validation error executing diagram: {e}")
            return ExecutionResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to execute diagram: {e}")
            return ExecutionResult(
                success=False, error=f"Failed to execute diagram: {e!s}"
            )

    @strawberry.mutation
    async def control_execution(
        self, input: ExecutionControlInput, info
    ) -> ExecutionResult:
        """Controls execution state (pause/resume/abort/skip)."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router

            state = await state_store.get_state(input.execution_id)
            if not state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {input.execution_id} not found",
                )

            if input.action == "pause":
                if input.node_id:
                    await state_store.update_node_status(
                        input.execution_id,
                        input.node_id,
                        NodeExecutionStatus.PAUSED,
                    )
                else:
                    await state_store.update_status(
                        input.execution_id, DomainExecutionStatus.PAUSED
                    )
            elif input.action == "resume":
                if input.node_id:
                    await state_store.update_node_status(
                        input.execution_id,
                        input.node_id,
                        NodeExecutionStatus.RUNNING,
                    )
                else:
                    await state_store.update_status(
                        input.execution_id, DomainExecutionStatus.RUNNING
                    )
            elif input.action == "abort":
                await state_store.update_status(
                    input.execution_id, DomainExecutionStatus.ABORTED
                )
            elif input.action == "skip" and input.node_id:
                await state_store.update_node_status(
                    input.execution_id,
                    input.node_id,
                    NodeExecutionStatus.SKIPPED,
                    skip_reason="Manual skip",
                )

            control_message = {
                "type": f"{input.action}_{'node' if input.node_id else 'execution'}",
                "execution_id": input.execution_id,
                "node_id": input.node_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await message_router.broadcast_to_execution(
                input.execution_id, control_message
            )

            updated_state = await state_store.get_state(input.execution_id)

            execution_state = ExecutionStateForGraphQL(
                id=ExecutionID(input.execution_id),
                status=updated_state.status,
                diagram_id=updated_state.diagram_id,
                started_at=updated_state.started_at,
                ended_at=updated_state.ended_at,
                node_states=updated_state.node_states,
                node_outputs=updated_state.node_outputs,
                token_usage=updated_state.token_usage
                or TokenUsage(input=0, output=0, cached=None, total=0),
                error=updated_state.error,
                variables=updated_state.variables,
            )

            return ExecutionResult(
                success=True,
                execution=execution_state,
                message=f"Execution control '{input.action}' sent successfully",
            )

        except ValueError as e:
            logger.error(f"Validation error controlling execution: {e}")
            return ExecutionResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to control execution: {e}")
            return ExecutionResult(
                success=False, error=f"Failed to control execution: {e!s}"
            )

    @strawberry.mutation
    async def submit_interactive_response(
        self, input: InteractiveResponseInput, info
    ) -> ExecutionResult:
        """Handles interactive node responses from users."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router

            execution_state = await state_store.get_state(input.execution_id)
            if not execution_state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {input.execution_id} not found",
                )

            if execution_state.status not in [
                DomainExecutionStatus.STARTED,
                DomainExecutionStatus.RUNNING,
            ]:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {input.execution_id} is not running (status: {execution_state.status})",
                )

            interactive_message = {
                "type": "interactive_response",
                "executionId": input.execution_id,
                "nodeId": input.node_id,
                "response": input.response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await message_router.broadcast_to_execution(
                input.execution_id, interactive_message
            )

            updated_state = await state_store.get_state(input.execution_id)

            execution = ExecutionStateForGraphQL(
                id=ExecutionID(input.execution_id),
                status=updated_state.status,
                diagram_id=updated_state.diagram_id,
                started_at=updated_state.started_at,
                ended_at=updated_state.ended_at,
                node_states=updated_state.node_states,
                node_outputs=updated_state.node_outputs,
                token_usage=updated_state.token_usage
                or TokenUsage(input=0, output=0, cached=None, total=0),
                error=updated_state.error,
                variables=updated_state.variables,
            )

            return ExecutionResult(
                success=True,
                execution=execution,
                message=f"Interactive response submitted for node {input.node_id}",
            )

        except ValueError as e:
            logger.error(f"Validation error submitting response: {e}")
            return ExecutionResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to submit interactive response: {e}", exc_info=True)
            return ExecutionResult(
                success=False, error=f"Failed to submit interactive response: {e!s}"
            )


def _map_status(status: str) -> ExecutionStatus:
    """Maps status string to ExecutionStatus enum."""
    status_map = {
        "started": ExecutionStatus.STARTED,
        "running": ExecutionStatus.RUNNING,
        "paused": ExecutionStatus.PAUSED,
        "completed": ExecutionStatus.COMPLETED,
        "failed": ExecutionStatus.FAILED,
        "cancelled": ExecutionStatus.ABORTED,
    }
    return status_map.get(status.lower(), ExecutionStatus.STARTED)


def _map_action_to_status(action: str, current_status: str) -> ExecutionStatus:
    """Maps control action to execution status."""
    current = _map_status(current_status)
    action_map = {
        "pause": ExecutionStatus.PAUSED,
        "resume": ExecutionStatus.RUNNING,
        "abort": ExecutionStatus.ABORTED,
        "cancel": ExecutionStatus.ABORTED,
        "skip_node": current,
    }

    return action_map.get(action.lower(), current)
