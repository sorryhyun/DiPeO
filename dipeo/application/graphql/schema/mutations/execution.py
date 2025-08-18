"""Execution mutations using ServiceRegistry."""

import asyncio
import logging
from typing import AsyncGenerator, Dict, Any

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_SERVICE, STATE_STORE, MESSAGE_ROUTER
from dipeo.application.execution import ExecuteDiagramUseCase
from dipeo.application.migration.compat_imports import StateStorePort, MessageRouterPort
from dipeo.diagram_generated.enums import Status, EventType

from ...types.inputs import (
    ExecuteDiagramInput, UpdateNodeStateInput, 
    ExecutionControlInput, InteractiveResponseInput
)
from ...types.results import ExecutionResult

logger = logging.getLogger(__name__)


def create_execution_mutations(registry: ServiceRegistry) -> type:
    """Create execution mutation methods with injected service registry."""
    
    @strawberry.type
    class ExecutionMutations:
        @strawberry.mutation
        async def execute_diagram(self, input: ExecuteDiagramInput) -> ExecutionResult:
            try:
                # Get required services
                state_store = registry.resolve(STATE_STORE)
                message_router = registry.resolve(MESSAGE_ROUTER)
                integrated_service = registry.resolve(DIAGRAM_SERVICE)
                
                # Initialize diagram service if needed
                if integrated_service and hasattr(integrated_service, 'initialize'):
                    await integrated_service.initialize()
                
                # Get diagram data - must be DomainDiagram for type safety
                from dipeo.diagram_generated import DomainDiagram
                
                domain_diagram = None
                diagram_source_path = None  # Track the original source path
                if input.diagram_id:
                    diagram_source_path = input.diagram_id  # Store the original path
                    # Load diagram model by ID
                    if hasattr(integrated_service, 'get_diagram_model'):
                        domain_diagram = await integrated_service.get_diagram_model(input.diagram_id)
                    elif hasattr(integrated_service, 'load_from_file'):
                        # Try to load from file
                        domain_diagram = await integrated_service.load_from_file(input.diagram_id)
                    else:
                        # Fallback: get dict and convert
                        diagram_dict = await integrated_service.get_diagram(input.diagram_id)
                        # Convert dict to DomainDiagram
                        from dipeo.infrastructure.services.diagram import DiagramConverterService
                        converter = DiagramConverterService()
                        await converter.initialize()
                        import json
                        json_content = json.dumps(diagram_dict)
                        domain_diagram = converter.deserialize_from_storage(json_content, "native")
                elif input.diagram_data:
                    # Direct dict provided - need to convert to DomainDiagram
                    from dipeo.infrastructure.services.diagram import DiagramConverterService
                    converter = DiagramConverterService()
                    await converter.initialize()
                    
                    # Detect format from the dict
                    format_hint = input.diagram_data.get("version") or input.diagram_data.get("format")
                    if format_hint in ["light", "readable"]:
                        # Light or readable format - convert to YAML
                        import yaml
                        content = yaml.dump(input.diagram_data, default_flow_style=False, sort_keys=False)
                        domain_diagram = converter.deserialize_from_storage(content, format_hint)
                    else:
                        # Native format - convert to JSON
                        import json
                        json_content = json.dumps(input.diagram_data)
                        domain_diagram = converter.deserialize_from_storage(json_content, "native")
                else:
                    raise ValueError("Either diagram_id or diagram_data must be provided")
                
                if not domain_diagram:
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
                
                # Add diagram source path if available
                if diagram_source_path:
                    options["diagram_source_path"] = diagram_source_path
                
                # Generate execution ID
                from dipeo.diagram_generated.domain_models import ExecutionID
                import uuid
                execution_id = ExecutionID(f"exec_{uuid.uuid4().hex}")
                
                # Execute asynchronously
                execution_task = None
                
                async def run_execution():
                    async for update in use_case.execute_diagram(
                        diagram=domain_diagram,
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
                state_store = registry.resolve(STATE_STORE)
                message_router = registry.resolve(MESSAGE_ROUTER)
                
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
                state_store = registry.resolve(STATE_STORE)
                message_router = registry.resolve(MESSAGE_ROUTER)
                
                # Map action to status
                status_map = {
                    "pause": Status.PAUSED,
                    "resume": Status.RUNNING,
                    "abort": Status.ABORTED,
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
                message_router = registry.resolve(MESSAGE_ROUTER)
                state_store = registry.resolve(STATE_STORE)
                
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