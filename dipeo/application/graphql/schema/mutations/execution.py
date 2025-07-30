"""Execution mutations using UnifiedServiceRegistry."""

import asyncio
import logging
from typing import AsyncGenerator, Dict, Any

import strawberry

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.application.execution import ExecuteDiagramUseCase
from dipeo.core.ports import StateStorePort, MessageRouterPort
from dipeo.diagram_generated.enums import ExecutionStatus, EventType

from ...types.inputs import (
    ExecuteDiagramInput, UpdateNodeStateInput, 
    ExecutionControlInput, InteractiveResponseInput
)
from ...types.results import ExecutionResult

logger = logging.getLogger(__name__)

# Service keys
STATE_STORE = ServiceKey[StateStorePort]("state_store")
MESSAGE_ROUTER = ServiceKey[MessageRouterPort]("message_router")
INTEGRATED_DIAGRAM_SERVICE = ServiceKey("integrated_diagram_service")


def create_execution_mutations(registry: UnifiedServiceRegistry) -> type:
    """Create execution mutation methods with injected service registry."""
    
    @strawberry.type
    class ExecutionMutations:
        @strawberry.mutation
        async def execute_diagram(self, input: ExecuteDiagramInput) -> ExecutionResult:
            try:
                # Get required services
                state_store = registry.require(STATE_STORE)
                message_router = registry.require(MESSAGE_ROUTER)
                integrated_service = registry.require(INTEGRATED_DIAGRAM_SERVICE)
                
                # Get diagram data
                diagram_data = None
                if input.diagram_id:
                    diagram_data = await integrated_service.get_diagram(input.diagram_id)
                elif input.diagram_data:
                    diagram_data = input.diagram_data
                else:
                    raise ValueError("Either diagram_id or diagram_data must be provided")
                
                if not diagram_data:
                    raise ValueError("Diagram not found")
                
                # Create execution use case
                use_case = ExecuteDiagramUseCase(
                    service_registry=registry,
                    state_store=state_store,
                    message_router=message_router,
                )
                
                # Prepare execution options
                options = {
                    "variables": input.variables or {},
                    "debug_mode": input.debug_mode or False,
                    "max_iterations": input.max_iterations or 100,
                    "timeout_seconds": input.timeout_seconds or 3600,
                }
                
                # Generate execution ID
                from dipeo.diagram_generated.domain_models import ExecutionID
                import uuid
                execution_id = ExecutionID(f"exec_{uuid.uuid4().hex}")
                
                # Execute asynchronously
                execution_task = None
                
                async def run_execution():
                    async for update in use_case.execute_diagram(
                        diagram=diagram_data,
                        options=options,
                        execution_id=str(execution_id),
                    ):
                        # Process updates if needed
                        pass
                
                # Start execution in background
                execution_task = asyncio.create_task(run_execution())
                
                # Wait briefly for execution to start
                await asyncio.sleep(0.1)
                
                if execution_id:
                    execution = await state_store.get_state(str(execution_id))
                    return ExecutionResult(
                        success=True,
                        execution_id=str(execution_id),
                        execution=execution,
                        message="Execution started successfully",
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        error="Failed to start execution",
                    )
                
            except Exception as e:
                logger.error(f"Failed to execute diagram: {e}")
                return ExecutionResult(
                    success=False,
                    error=f"Failed to execute diagram: {str(e)}",
                )
        
        @strawberry.mutation
        async def update_node_state(self, input: UpdateNodeStateInput) -> ExecutionResult:
            try:
                state_store = registry.require(STATE_STORE)
                message_router = registry.require(MESSAGE_ROUTER)
                
                # Update node state
                await state_store.update_node_status(
                    execution_id=input.execution_id,
                    node_id=input.node_id,
                    status=input.status,
                    output=input.output,
                    error=input.error,
                )
                
                # Send update event
                await message_router.broadcast_to_execution(
                    execution_id=input.execution_id,
                    message={
                        "type": EventType.NODE_STATUS_CHANGED.value,
                        "node_id": input.node_id,
                        "status": input.status,
                        "output": input.output,
                        "error": input.error,
                    }
                )
                
                # Get updated execution
                execution = await state_store.get_state(input.execution_id)
                
                return ExecutionResult(
                    success=True,
                    execution_id=input.execution_id,
                    execution=execution,
                    message=f"Updated node {input.node_id} state",
                )
                
            except Exception as e:
                logger.error(f"Failed to update node state: {e}")
                return ExecutionResult(
                    success=False,
                    error=f"Failed to update node state: {str(e)}",
                )
        
        @strawberry.mutation
        async def control_execution(self, input: ExecutionControlInput) -> ExecutionResult:
            try:
                state_store = registry.require(STATE_STORE)
                message_router = registry.require(MESSAGE_ROUTER)
                
                # Map action to status
                status_map = {
                    "pause": ExecutionStatus.PAUSED,
                    "resume": ExecutionStatus.RUNNING,
                    "abort": ExecutionStatus.ABORTED,
                }
                
                new_status = status_map.get(input.action)
                if not new_status:
                    raise ValueError(f"Invalid action: {input.action}")
                
                # Update execution status
                await state_store.update_status(
                    input.execution_id, new_status
                )
                
                # Send control event
                await message_router.broadcast_to_execution(
                    execution_id=input.execution_id,
                    message={
                        "type": EventType.EXECUTION_STATUS_CHANGED.value,
                        "action": input.action,
                        "reason": input.reason,
                        "status": new_status.value,
                    }
                )
                
                # Get updated execution
                execution = await state_store.get_state(input.execution_id)
                
                return ExecutionResult(
                    success=True,
                    execution_id=input.execution_id,
                    execution=execution,
                    message=f"Execution {input.action} successful",
                )
                
            except Exception as e:
                logger.error(f"Failed to control execution: {e}")
                return ExecutionResult(
                    success=False,
                    error=f"Failed to control execution: {str(e)}",
                )
        
        @strawberry.mutation
        async def send_interactive_response(
            self, input: InteractiveResponseInput
        ) -> ExecutionResult:
            try:
                message_router = registry.require(MESSAGE_ROUTER)
                state_store = registry.require(STATE_STORE)
                
                # Send interactive response
                await message_router.broadcast_to_execution(
                    execution_id=input.execution_id,
                    message={
                        "type": EventType.INTERACTIVE_RESPONSE.value,
                        "node_id": input.node_id,
                        "response": input.response,
                        "metadata": input.metadata,
                    }
                )
                
                # Get updated execution
                execution = await state_store.get_state(input.execution_id)
                
                return ExecutionResult(
                    success=True,
                    execution_id=input.execution_id,
                    execution=execution,
                    message="Interactive response sent",
                )
                
            except Exception as e:
                logger.error(f"Failed to send interactive response: {e}")
                return ExecutionResult(
                    success=False,
                    error=f"Failed to send interactive response: {str(e)}",
                )
    
    return ExecutionMutations