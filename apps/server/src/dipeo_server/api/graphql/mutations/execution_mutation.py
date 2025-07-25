"""GraphQL mutations for diagram execution operations."""

import asyncio
import logging
import uuid
from datetime import UTC, datetime

import strawberry
from dipeo.models import (
    ExecutionStatus,
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
    # Handles diagram execution via GraphQL API

    @strawberry.mutation
    async def execute_diagram(self, data: ExecuteDiagramInput, info) -> ExecutionResult:
        try:
            context: GraphQLContext = info.context
            execution_service = context.execution_service
            state_store = context.get_service("state_store")

            if state_store is None:
                logger.error("State store is None!")
                return ExecutionResult(
                    success=False, error="State store not initialized"
                )

            if execution_service is None:
                logger.error("Execution service is None!")
                return ExecutionResult(
                    success=False, error="Execution service not initialized"
                )
            
            # Set the container on the execution service
            execution_service.container = context.container

            if data.diagram_data:
                # The execution service will validate as DomainDiagram which expects lists
                # If the data is in backend format (dict of dicts), it needs to stay as dict
                # because the execution service handles the conversion internally
                diagram_data = data.diagram_data
            elif data.diagram_id:
                # Use integrated service
                integrated_service = context.get_service("integrated_diagram_service")
                diagram_data = await integrated_service.get_diagram(data.diagram_id)
                if not diagram_data:
                    return ExecutionResult(success=False, error="Diagram not found")
            else:
                return ExecutionResult(success=False, error="No diagram data provided")

            execution_id = str(uuid.uuid4())

            options = {
                "debugMode": data.debug_mode,
                "maxIterations": data.max_iterations,
                "timeout": data.timeout_seconds,
                "variables": data.variables or {},
            }

            diagram_id = data.diagram_id if data.diagram_id else None
            execution = await state_store.create_execution(
                execution_id, diagram_id, data.variables
            )

            # Start the actual execution asynchronously
            async def run_execution():
                try:
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

            return ExecutionResult(
                success=True,
                execution=execution,  # Use the domain model directly, Strawberry will convert it
                execution_id=execution_id,
                message=f"Started execution {execution_id}",
            )

        except ValueError as e:
            logger.error(f"Validation error executing diagram: {e}")
            return ExecutionResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            import traceback

            logger.error(f"Failed to execute diagram: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return ExecutionResult(
                success=False, error=f"Failed to execute diagram: {e!s}"
            )

    @strawberry.mutation
    async def control_execution(
        self, data: ExecutionControlInput, info
    ) -> ExecutionResult:
        try:
            context: GraphQLContext = info.context
            state_store = context.get_service("state_store")
            message_router = context.get_service("message_router")

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

            return ExecutionResult(
                success=True,
                execution=updated_state,
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
        try:
            context: GraphQLContext = info.context
            state_store = context.get_service("state_store")
            message_router = context.get_service("message_router")

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

            return ExecutionResult(
                success=True,
                execution=updated_state,
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


def _map_status(status: str) -> ExecutionStatus:
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
    current = _map_status(current_status)
    action_map = {
        "pause": ExecutionStatus.PAUSED,
        "resume": ExecutionStatus.RUNNING,
        "abort": ExecutionStatus.ABORTED,
        "cancel": ExecutionStatus.ABORTED,
        "skip_node": current,
    }

    return action_map.get(action.lower(), current)
