"""Execution mutations using ServiceRegistry."""

import asyncio
import logging
import uuid

import strawberry

from dipeo.application.execution import ExecuteDiagramUseCase
from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT, MESSAGE_ROUTER, STATE_STORE
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import EventType, Status
from dipeo.diagram_generated.graphql_backups.inputs import (
    ExecuteDiagramInput,
    ExecutionControlInput,
    InteractiveResponseInput,
    UpdateNodeStateInput,
)
from dipeo.diagram_generated.graphql_backups.operations import (
    CONTROL_EXECUTION_MUTATION,
    EXECUTE_DIAGRAM_MUTATION,
    SEND_INTERACTIVE_RESPONSE_MUTATION,
    UPDATE_NODE_STATE_MUTATION,
    ControlExecutionOperation,
    ExecuteDiagramOperation,
    SendInteractiveResponseOperation,
    UpdateNodeStateOperation,
)
from dipeo.diagram_generated.graphql_backups.results import ExecutionResult
from dipeo.infrastructure.diagram.adapters import UnifiedSerializerAdapter

logger = logging.getLogger(__name__)


# Standalone resolver functions for use with OperationExecutor
async def execute_diagram(registry: ServiceRegistry, input: ExecuteDiagramInput) -> ExecutionResult:
    """
    Resolver for ExecuteDiagram operation.
    Uses the generated EXECUTE_DIAGRAM_MUTATION query string.
    """
    try:
        state_store = registry.resolve(STATE_STORE)
        message_router = registry.resolve(MESSAGE_ROUTER)
        integrated_service = registry.resolve(DIAGRAM_PORT)
        if integrated_service and hasattr(integrated_service, "initialize"):
            await integrated_service.initialize()

        domain_diagram = None
        diagram_source_path = None
        if input.diagram_id:
            diagram_source_path = input.diagram_id
            if hasattr(integrated_service, "get_diagram_model"):
                domain_diagram = await integrated_service.get_diagram_model(input.diagram_id)
            elif hasattr(integrated_service, "load_from_file"):
                domain_diagram = await integrated_service.load_from_file(input.diagram_id)
            else:
                diagram_dict = await integrated_service.get_diagram(input.diagram_id)
                serializer = UnifiedSerializerAdapter()
                await serializer.initialize()
                import json

                json_content = json.dumps(diagram_dict)
                domain_diagram = serializer.deserialize_from_storage(json_content, "native")
        elif input.diagram_data:
            serializer = UnifiedSerializerAdapter()
            await serializer.initialize()
            format_hint = input.diagram_data.get("version") or input.diagram_data.get("format")
            if format_hint in ["light", "readable"]:
                import yaml

                content = yaml.dump(input.diagram_data, default_flow_style=False, sort_keys=False)
                domain_diagram = serializer.deserialize_from_storage(content, format_hint)
            else:
                import json

                json_content = json.dumps(input.diagram_data)
                domain_diagram = serializer.deserialize_from_storage(json_content, "native")
        else:
            raise ValueError("Either diagram_id or diagram_data must be provided")

        if not domain_diagram:
            raise ValueError("Diagram not found")

        use_case = ExecuteDiagramUseCase(
            service_registry=registry,
            state_store=state_store,
            message_router=message_router,
        )

        options = {
            "variables": input.variables or {},
            "debug_mode": input.debug_mode or False,
            "max_iterations": input.max_iterations or 100,
            "timeout_seconds": input.timeout_seconds or 3600,
        }

        if diagram_source_path:
            options["diagram_source_path"] = diagram_source_path

        execution_id = ExecutionID(f"exec_{uuid.uuid4().hex}")

        async def run_execution():
            async for _update in use_case.execute_diagram(
                diagram=domain_diagram,
                options=options,
                execution_id=str(execution_id),
            ):
                pass

        _background_task = asyncio.create_task(run_execution())
        await asyncio.sleep(0.1)

        if execution_id:
            execution = await state_store.get_state(str(execution_id))
            result = ExecutionResult.success_result(
                data=execution, message="Execution started successfully"
            )
            result.execution = execution
            return result
        else:
            return ExecutionResult.error_result(error="Failed to start execution")

    except Exception as e:
        logger.error(f"Failed to execute diagram: {e}")
        return ExecutionResult.error_result(error=f"Failed to execute diagram: {e!s}")


async def update_node_state(
    registry: ServiceRegistry, input: UpdateNodeStateInput
) -> ExecutionResult:
    """
    Resolver for UpdateNodeState operation.
    Uses the generated UPDATE_NODE_STATE_MUTATION query string.
    """
    try:
        state_store = registry.resolve(STATE_STORE)
        message_router = registry.resolve(MESSAGE_ROUTER)

        await state_store.update_node_status(
            execution_id=input.execution_id,
            node_id=input.node_id,
            status=input.status,
            output=input.output,
            error=input.error,
        )

        await message_router.broadcast_to_execution(
            execution_id=input.execution_id,
            message={
                "type": EventType.NODE_STATUS_CHANGED.value,
                "node_id": input.node_id,
                "status": input.status,
                "output": input.output,
                "error": input.error,
            },
        )

        execution = await state_store.get_state(input.execution_id)
        result = ExecutionResult.success_result(
            data=execution, message=f"Updated node {input.node_id} state"
        )
        result.execution = execution
        return result

    except Exception as e:
        logger.error(f"Failed to update node state: {e}")
        return ExecutionResult.error_result(error=f"Failed to update node state: {e!s}")


async def control_execution(
    registry: ServiceRegistry, input: ExecutionControlInput
) -> ExecutionResult:
    """
    Resolver for ControlExecution operation.
    Uses the generated CONTROL_EXECUTION_MUTATION query string.
    """
    try:
        state_store = registry.resolve(STATE_STORE)
        message_router = registry.resolve(MESSAGE_ROUTER)

        status_map = {
            "pause": Status.PAUSED,
            "resume": Status.RUNNING,
            "abort": Status.ABORTED,
        }

        new_status = status_map.get(input.action)
        if not new_status:
            raise ValueError(f"Invalid action: {input.action}")

        await state_store.update_status(input.execution_id, new_status)

        await message_router.broadcast_to_execution(
            execution_id=input.execution_id,
            message={
                "type": EventType.EXECUTION_STATUS_CHANGED.value,
                "action": input.action,
                "reason": input.reason,
                "status": new_status.value,
            },
        )

        execution = await state_store.get_state(input.execution_id)
        result = ExecutionResult.success_result(
            data=execution, message=f"Execution {input.action} successful"
        )
        result.execution = execution
        return result

    except Exception as e:
        logger.error(f"Failed to control execution: {e}")
        return ExecutionResult.error_result(error=f"Failed to control execution: {e!s}")


async def send_interactive_response(
    registry: ServiceRegistry, input: InteractiveResponseInput
) -> ExecutionResult:
    """
    Resolver for SendInteractiveResponse operation.
    Uses the generated SEND_INTERACTIVE_RESPONSE_MUTATION query string.
    """
    try:
        message_router = registry.resolve(MESSAGE_ROUTER)
        state_store = registry.resolve(STATE_STORE)

        await message_router.broadcast_to_execution(
            execution_id=input.execution_id,
            message={
                "type": EventType.INTERACTIVE_RESPONSE.value,
                "node_id": input.node_id,
                "response": input.response,
                "metadata": input.metadata,
            },
        )

        execution = await state_store.get_state(input.execution_id)
        result = ExecutionResult.success_result(data=execution, message="Interactive response sent")
        result.execution = execution
        return result

    except Exception as e:
        logger.error(f"Failed to send interactive response: {e}")
        return ExecutionResult.error_result(error=f"Failed to send interactive response: {e!s}")


def create_execution_mutations(registry: ServiceRegistry) -> type:
    """Create execution mutation methods with injected registry."""

    @strawberry.type
    class ExecutionMutations:
        @strawberry.mutation
        async def execute_diagram(self, input: ExecuteDiagramInput) -> ExecutionResult:
            """Mutation method that delegates to standalone resolver."""
            return await execute_diagram(registry, input)

        @strawberry.mutation
        async def update_node_state(self, input: UpdateNodeStateInput) -> ExecutionResult:
            """Mutation method that delegates to standalone resolver."""
            return await update_node_state(registry, input)

        @strawberry.mutation
        async def control_execution(self, input: ExecutionControlInput) -> ExecutionResult:
            """Mutation method that delegates to standalone resolver."""
            return await control_execution(registry, input)

        @strawberry.mutation
        async def send_interactive_response(
            self, input: InteractiveResponseInput
        ) -> ExecutionResult:
            """Mutation method that delegates to standalone resolver."""
            return await send_interactive_response(registry, input)

    return ExecutionMutations
