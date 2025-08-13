"""Refactored typed execution engine using unified ExecutionContext.

This engine manages diagram execution with a clean separation of concerns:
- ExecutionContext handles all state management
- Engine focuses on orchestration and parallelization
- Event-based architecture for decoupled notifications
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.typed_execution_context import TypedExecutionContext
from dipeo.core.events import EventEmitter, EventType, ExecutionEvent
from dipeo.core.execution.runtime_resolver import RuntimeResolver
from dipeo.diagram_generated import ExecutionState, NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution import DomainDynamicOrderCalculator
from dipeo.infrastructure.config import get_settings
from dipeo.infrastructure.events import NullEventBus

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry
    from dipeo.core.ports import ExecutionObserver

logger = logging.getLogger(__name__)


class TypedExecutionEngine:
    """Refactored execution engine with clean separation of concerns.
    
    This engine:
    - Uses TypedExecutionContext for all state management
    - Focuses on execution orchestration
    - Manages parallel node execution
    - Coordinates event notifications
    """
    
    def __init__(
        self, 
        service_registry: "ServiceRegistry",
        runtime_resolver: RuntimeResolver,
        order_calculator: Any | None = None,
        event_bus: EventEmitter | None = None,
        observers: list["ExecutionObserver"] | None = None
    ):
        self.service_registry = service_registry
        self.runtime_resolver = runtime_resolver
        self.order_calculator = order_calculator or DomainDynamicOrderCalculator()
        self._settings = get_settings()
        self._managed_event_bus = False
        
        if observers and not event_bus:
            from dipeo.infrastructure.events.observer_adapter import create_event_bus_with_observers
            self.event_bus = create_event_bus_with_observers(observers)
            self._managed_event_bus = True
        else:
            self.event_bus = event_bus or NullEventBus()
    
    async def execute(
        self,
        diagram: ExecutableDiagram,
        execution_state: ExecutionState,
        options: dict[str, Any],
        container: Optional["Container"] = None,
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute a diagram using the unified execution context."""
        
        # Start event bus if we're managing it
        if self._managed_event_bus:
            await self.event_bus.start()
        
        context = None
        try:
            # Create execution context
            context = TypedExecutionContext.from_execution_state(
                execution_state=execution_state,
                diagram=diagram,
                service_registry=self.service_registry,
                runtime_resolver=self.runtime_resolver,
                event_bus=self.event_bus,
                container=container
            )
            
            # Extract metadata from options
            for key, value in options.get('metadata', {}).items():
                context.set_execution_metadata(key, value)
            
            # Emit execution started event
            await context.emit_event(
                EventType.EXECUTION_STARTED,
                {
                    "diagram_id": context.diagram_id,
                    "diagram_name": diagram.metadata.get("name", "unknown") if diagram.metadata else "unknown"
                }
            )
            
            # Store interactive handler in service registry for handlers to access
            from dipeo.application.registry import ServiceKey
            self.service_registry.register(ServiceKey("diagram"), diagram)
            self.service_registry.register(ServiceKey("execution_context"), {
                "interactive_handler": interactive_handler
            })
            
            # Main execution loop
            step_count = 0
            while not context.is_execution_complete():
                # Get ready nodes
                ready_nodes = self._get_ready_nodes_from_context(context)
                
                if not ready_nodes:
                    # No nodes ready, wait briefly
                    await asyncio.sleep(self._settings.node_ready_poll_interval)
                    continue
                
                step_count += 1
                
                # Execute ready nodes
                results = await self._execute_nodes(ready_nodes, context)
                
                # Calculate progress
                progress = context.calculate_progress()
                
                # Yield step result
                yield {
                    "type": "step_complete",
                    "step": step_count,
                    "executed_nodes": list(results.keys()),
                    "progress": progress,
                }
            
            # Execution complete
            execution_path = [str(node_id) for node_id in context.get_completed_nodes()]
            from dipeo.diagram_generated import Status
            
            await context.emit_event(
                EventType.EXECUTION_COMPLETED,
                {
                    "status": Status.COMPLETED,
                    "total_steps": step_count,
                    "execution_path": execution_path
                }
            )
            
            yield {
                "type": "execution_complete",
                "total_steps": step_count,
                "execution_path": execution_path,
            }
            
        except Exception as e:
            # Emit execution completed with failed status
            from dipeo.diagram_generated import Status
            
            if context:
                await context.emit_event(
                    EventType.EXECUTION_COMPLETED,
                    {
                        "status": Status.FAILED,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
            
            yield {
                "type": "execution_error",
                "error": str(e),
            }
            raise
        finally:
            # Stop event bus if we're managing it
            if self._managed_event_bus:
                await self.event_bus.stop()
    
    def _get_ready_nodes_from_context(self, context: TypedExecutionContext) -> list[ExecutableNode]:
        """Get ready nodes using the order calculator."""
        # Build execution context for order calculator
        node_outputs = {}
        node_exec_counts = {}
        
        for node_id in context.get_completed_nodes():
            output = context.get_node_output(node_id)
            if output:
                node_outputs[str(node_id)] = output
            node_exec_counts[str(node_id)] = context.get_node_execution_count(node_id)
        
        # Create a minimal context wrapper for the order calculator
        class OrderCalculatorContext:
            def __init__(self, ctx: TypedExecutionContext, outputs: dict, counts: dict):
                self._context = ctx
                self._node_outputs = outputs
                self._node_exec_counts = counts
            
            def get_metadata(self, key: str) -> Any:
                return self._context.get_execution_metadata().get(key)
            
            def get_variable(self, name: str) -> Any:
                return self._context.get_variable(name)
            
            def get_node_output(self, node_id: str | NodeID) -> Any:
                return self._node_outputs.get(str(node_id))
            
            def get_node_execution_count(self, node_id: str | NodeID) -> int:
                return self._node_exec_counts.get(str(node_id), 0)
            
            def is_first_execution(self, node_id: str | NodeID) -> bool:
                return self.get_node_execution_count(node_id) <= 1
            
            def get_node_state(self, node_id: str | NodeID) -> Any:
                return self._context.get_node_state(node_id)
            
            @property
            def current_node_id(self) -> NodeID | None:
                return self._context.current_node_id
            
            @property
            def execution_id(self) -> str:
                return self._context.execution_id
            
            @property
            def diagram_id(self) -> str:
                return self._context.diagram_id
        
        calc_context = OrderCalculatorContext(context, node_outputs, node_exec_counts)
        
        # Pass the actual context or calc_context depending on the calculator implementation
        # DomainDynamicOrderCalculator can handle extracting states from either
        return self.order_calculator.get_ready_nodes(
            diagram=context.diagram,
            context=calc_context  # type: ignore
        )
    
    async def _execute_nodes(
        self,
        nodes: list[ExecutableNode],
        context: TypedExecutionContext
    ) -> dict[str, dict[str, Any]]:
        """Execute nodes with optional parallelization."""
        max_concurrent = 20
        
        # Single node - execute directly
        if len(nodes) == 1:
            node = nodes[0]
            result = await self._execute_single_node(node, context)
            return {str(node.id): result}
        
        # Multiple nodes - execute in parallel with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(node: ExecutableNode) -> tuple[str, dict[str, Any]]:
            async with semaphore:
                result = await self._execute_single_node(node, context)
                return str(node.id), result
        
        # Execute all nodes in parallel
        tasks = [execute_with_semaphore(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        output = {}
        for node_id, result in results:
            if isinstance(result, Exception):
                raise result
            output[node_id] = result
        
        return output
    
    async def _execute_single_node(
        self,
        node: ExecutableNode,
        context: TypedExecutionContext
    ) -> dict[str, Any]:
        """Execute a single node with event notifications."""
        node_id = node.id
        start_time = time.time()
        
        # Emit node started event
        await context.emit_event(
            EventType.NODE_STARTED,
            {
                "node_id": str(node_id),
                "node_type": node.type,
                "node_name": getattr(node, 'name', str(node_id))
            }
        )
        
        try:
            # For PersonJobNode, check max_iteration BEFORE incrementing count
            from dipeo.diagram_generated.generated_nodes import PersonJobNode
            if isinstance(node, PersonJobNode):
                current_count = context.get_node_execution_count(node_id)
                if current_count >= node.max_iteration:
                    logger.info(f"PersonJobNode {node_id} has reached max_iteration ({node.max_iteration}), transitioning to MAXITER_REACHED")
                    
                    # Transition directly to MAXITER_REACHED without running
                    from dipeo.core.execution.node_output import TextOutput
                    from dipeo.diagram_generated.enums import Status
                    output = TextOutput(
                        value="",
                        node_id=node_id,
                        status=Status.MAXITER_REACHED,
                        metadata="{}"
                    )
                    context.transition_node_to_maxiter(node_id, output)
                    
                    # Emit completion event with MAXITER_REACHED status
                    await context.emit_event(
                        EventType.NODE_COMPLETED,
                        {
                            "node_id": str(node_id),
                            "node_type": node.type,
                            "node_name": getattr(node, 'name', str(node_id)),
                            "status": "MAXITER_REACHED",
                            "output": {"value": "", "status": "MAXITER_REACHED"},
                            "metrics": {
                                "execution_time_ms": 0,
                                "execution_count": current_count
                            }
                        }
                    )
                    
                    return {"value": "", "status": "MAXITER_REACHED"}
            
            # Transition to running state
            with context.executing_node(node_id):
                exec_count = context.transition_node_to_running(node_id)
                
                # Get handler
                handler = self._get_handler(node.type)
                
                # Resolve inputs
                inputs = context.resolve_node_inputs(node)
                
                # Create ExecutionRequest with diagram metadata
                from dipeo.application.execution.execution_request import ExecutionRequest
                
                # Include diagram metadata in request metadata
                request_metadata = {}
                if hasattr(context.diagram, 'metadata') and context.diagram.metadata:
                    request_metadata['diagram_source_path'] = context.diagram.metadata.get('diagram_source_path')
                    request_metadata['diagram_id'] = context.diagram.metadata.get('diagram_id')
                
                request = ExecutionRequest(
                    node=node,
                    context=context,  # Pass the context directly
                    inputs=inputs,
                    services=self.service_registry,
                    metadata=request_metadata,
                    execution_id=context.execution_id,
                    parent_container=context.container,
                    parent_registry=self.service_registry
                )
                
                # Call pre_execute hook first
                output = await handler.pre_execute(request)
                
                # If pre_execute returned output, use it; otherwise execute normally
                if output is None:
                    output = await handler.execute_request(request)
            
            # Calculate execution metrics
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Extract token usage from output metadata if available (do this BEFORE marking node as completed)
            token_usage = None
            if hasattr(output, 'metadata') and output.metadata:
                # Use get_metadata_dict() to parse JSON metadata
                if hasattr(output, 'get_metadata_dict'):
                    metadata_dict = output.get_metadata_dict()
                    token_usage = metadata_dict.get('token_usage')
            
            # Handle node completion based on type (this marks node as completed)
            await self._handle_node_completion(node, output, context)
            
            # Emit node completed event
            node_state = context.get_node_state(node_id)
            event_data = {
                "node_id": str(node_id),
                "node_type": node.type,
                "node_name": getattr(node, 'name', str(node_id)),
                "status": node_state.status.value if node_state else "unknown",
                "output": self._serialize_output(output),
                "node_state": node_state,  # Include the full node state for observers
                "metrics": {
                    "duration_ms": duration_ms,
                    "start_time": start_time,
                    "end_time": end_time,
                    "execution_count": exec_count
                }
            }
            
            # Add token usage to metrics if available
            if token_usage:
                event_data["metrics"]["token_usage"] = token_usage
            
            await context.emit_event(EventType.NODE_COMPLETED, event_data)
            
            # Return result
            if hasattr(output, 'to_dict'):
                return output.to_dict()
            elif hasattr(output, 'value'):
                result = {"value": output.value}
                if hasattr(output, 'metadata') and output.metadata:
                    result["metadata"] = output.metadata
                return result
            else:
                return {"value": output}
            
        except Exception as e:
            logger.error(f"Error executing node {node_id}: {e}", exc_info=True)
            
            # Transition to failed state
            context.transition_node_to_failed(node_id, str(e))
            
            # Emit node failed event
            await context.emit_event(
                EventType.NODE_FAILED,
                {
                    "node_id": str(node_id),
                    "node_type": node.type,
                    "node_name": getattr(node, 'name', str(node_id)),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
    
    def _get_handler(self, node_type: str):
        """Get handler for node type."""
        from dipeo.application import get_global_registry
        from dipeo.application.execution.handler_factory import HandlerFactory
        
        registry = get_global_registry()
        if not hasattr(registry, '_service_registry') or registry._service_registry is None:
            HandlerFactory(self.service_registry)
        
        return registry.create_handler(node_type)
    
    async def _handle_node_completion(
        self,
        node: ExecutableNode,
        output: Any,
        context: TypedExecutionContext
    ) -> None:
        """Handle node completion and state transitions."""
        # All nodes complete normally - PersonJob max_iteration is handled in the handler
        context.transition_node_to_completed(node.id, output)
    
    def _serialize_output(self, output: Any) -> dict[str, Any]:
        """Serialize node output for event data."""
        try:
            if hasattr(output, 'to_dict'):
                return output.to_dict()
            elif hasattr(output, 'value'):
                result = {"value": output.value}
                if hasattr(output, 'metadata') and output.metadata:
                    result["metadata"] = output.metadata
                return result
            else:
                return {"value": str(output)}
        except Exception as e:
            logger.warning(f"Failed to serialize output: {e}")
            return {"value": "output_serialization_failed"}