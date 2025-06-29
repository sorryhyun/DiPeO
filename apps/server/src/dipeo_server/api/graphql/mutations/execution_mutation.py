"""GraphQL mutations for diagram execution operations."""

import asyncio
import logging
import uuid
from datetime import UTC, datetime

import strawberry
from dipeo_domain import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    ExecutionStatus,
    TokenUsage,
)

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
    async def execute_diagram(self, data: ExecuteDiagramInput, info) -> ExecutionResult:
        """Starts diagram execution with provided configuration."""
        try:
            context: GraphQLContext = info.context
            execution_service = context.execution_service
            state_store = context.state_store

            if data.diagram_data:
                diagram_data = data.diagram_data
                # The execution service expects dict format, so we don't need to convert
            elif data.diagram_id:
                # Use new services
                storage_service = context.diagram_storage_service
                path = await storage_service.find_by_id(data.diagram_id)
                if path:
                    diagram_data = await storage_service.read_file(path)
                else:
                    return ExecutionResult(success=False, error="Diagram not found")
            else:
                return ExecutionResult(success=False, error="No diagram data provided")

            execution_id = str(uuid.uuid4())

            options = {
                "debugMode": data.debug_mode,
                "maxIterations": data.max_iterations,
                "timeout": data.timeout_seconds,
            }

            diagram_id = data.diagram_id if data.diagram_id else None
            await state_store.create_execution(execution_id, diagram_id, options)

            # Start the actual execution asynchronously
            async def run_execution():
                try:
                    logger.info(f"Starting run_execution for {execution_id}")
                    async for _ in execution_service.execute_diagram(
                        diagram=diagram_data, options=options, execution_id=execution_id
                    ):
                        # Updates are handled by the execution service
                        pass
                except Exception as ex:
                    import traceback
                    logger.error(f"Execution failed for {execution_id}: {ex}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    await state_store.update_status(
                        execution_id, ExecutionStatus.FAILED, error=str(ex)
                    )

            # Launch execution in background
            asyncio.create_task(run_execution())

            # Execution starts asynchronously; client monitors via subscriptions
            execution = ExecutionState(
                id=ExecutionID(execution_id),
                status=ExecutionStatus.PENDING,
                diagramId=DiagramID(diagram_id) if diagram_id else None,
                startedAt=datetime.now(UTC).isoformat(),
                endedAt=None,
                nodeStates={},
                nodeOutputs={},
                tokenUsage=TokenUsage(input=0, output=0, cached=None, total=0),
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
        self, data: ExecutionControlInput, info
    ) -> ExecutionResult:
        """Controls execution state (pause/resume/abort/skip)."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router

            state = await state_store.get_state(data.execution_id)
            if not state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {data.execution_id} not found",
                )

            if data.action == "pause":
                if data.node_id:
                    pass
                else:
                    await state_store.update_status(
                        data.execution_id, ExecutionStatus.PAUSED
                    )
            elif data.action == "resume":
                if data.node_id:
                    pass
                else:
                    await state_store.update_status(
                        data.execution_id, ExecutionStatus.RUNNING
                    )
            elif data.action == "abort":
                await state_store.update_status(
                    data.execution_id, ExecutionStatus.ABORTED
                )
            elif data.action == "skip" and data.node_id:
                pass

            control_message = {
                "type": f"{data.action}_{'node' if data.node_id else 'execution'}",
                "execution_id": data.execution_id,
                "node_id": data.node_id,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            await message_router.broadcast_to_execution(
                data.execution_id, control_message
            )

            updated_state = await state_store.get_state(data.execution_id)

            execution_state = ExecutionMutations._create_execution_state(
                data.execution_id, updated_state
            )

            return ExecutionResult(
                success=True,
                execution=execution_state,
                message=f"Execution control '{data.action}' sent successfully",
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
        self, data: InteractiveResponseInput, info
    ) -> ExecutionResult:
        """Handles interactive node responses from users."""
        try:
            context: GraphQLContext = info.context
            state_store = context.state_store
            message_router = context.message_router

            execution_state = await state_store.get_state(data.execution_id)
            if not execution_state:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {data.execution_id} not found",
                )

            if execution_state.status not in [
                ExecutionStatus.PENDING,
                ExecutionStatus.RUNNING,
            ]:
                return ExecutionResult(
                    success=False,
                    error=f"Execution {data.execution_id} is not running (status: {execution_state.status})",
                )

            interactive_message = {
                "type": "interactive_response",
                "executionId": data.execution_id,
                "nodeId": data.node_id,
                "response": data.response,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            await message_router.broadcast_to_execution(
                data.execution_id, interactive_message
            )

            updated_state = await state_store.get_state(data.execution_id)

            execution = ExecutionMutations._create_execution_state(
                data.execution_id, updated_state
            )

            return ExecutionResult(
                success=True,
                execution=execution,
                message=f"Interactive response submitted for node {data.node_id}",
            )

        except ValueError as e:
            logger.error(f"Validation error submitting response: {e}")
            return ExecutionResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to submit interactive response: {e}", exc_info=True)
            return ExecutionResult(
                success=False, error=f"Failed to submit interactive response: {e!s}"
            )

    @staticmethod
    def _create_execution_state(execution_id: str, state) -> ExecutionState:
        return ExecutionState(
            id=ExecutionID(execution_id),
            status=state.status,
            diagramId=state.diagram_id,
            startedAt=state.started_at,
            endedAt=state.ended_at,
            nodeStates=state.node_states,
            nodeOutputs=state.node_outputs,
            tokenUsage=state.token_usage
            or TokenUsage(input=0, output=0, cached=None, total=0),
            error=state.error,
            variables=state.variables,
        )


def _map_status(status: str) -> ExecutionStatus:
    """Maps status string to ExecutionStatus enum."""
    status_map = {
        "pending": ExecutionStatus.PENDING,
        "running": ExecutionStatus.RUNNING,
        "paused": ExecutionStatus.PAUSED,
        "completed": ExecutionStatus.COMPLETED,
        "failed": ExecutionStatus.FAILED,
        "cancelled": ExecutionStatus.ABORTED,
    }
    return status_map.get(status.lower(), ExecutionStatus.PENDING)


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
