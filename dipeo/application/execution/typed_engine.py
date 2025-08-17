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

from dipeo.application.execution.scheduler import NodeScheduler
from dipeo.application.execution.typed_execution_context import TypedExecutionContext
from dipeo.core.events import EventEmitter, EventType, ExecutionEvent
from dipeo.core.execution.runtime_resolver_v2 import RuntimeResolverV2
from dipeo.diagram_generated import ExecutionState, NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution import DomainDynamicOrderCalculator
from dipeo.infrastructure.config import get_settings
from dipeo.infrastructure.adapters.events import NullEventBus

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry
    from dipeo.application.migration.compat_imports import ExecutionObserver

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
        runtime_resolver: RuntimeResolverV2,
        order_calculator: Any | None = None,
        event_bus: EventEmitter | None = None,
        observers: list["ExecutionObserver"] | None = None
    ):
        self.service_registry = service_registry
        self.runtime_resolver = runtime_resolver
        self.order_calculator = order_calculator or DomainDynamicOrderCalculator()
        self._settings = get_settings()
        self._managed_event_bus = False
        self._scheduler: NodeScheduler | None = None
        
        if observers and not event_bus:
            from dipeo.infrastructure.adapters.events.legacy.observer_consumer_adapter import create_event_bus_with_observers
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
            
            # Initialize scheduler for this execution
            self._scheduler = NodeScheduler(diagram, self.order_calculator)
            
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
                # Get ready nodes using scheduler
                ready_nodes = await self._scheduler.get_ready_nodes(context)
                
                if not ready_nodes:
                    # No nodes ready, wait briefly
                    await asyncio.sleep(self._settings.node_ready_poll_interval)
                    continue
                
                step_count += 1
                
                # Execute ready nodes
                results = await self._execute_nodes(ready_nodes, context)
                
                # Update scheduler with completed nodes
                for node_id in results.keys():
                    self._scheduler.mark_node_completed(NodeID(node_id), context)
                
                # Calculate progress
                progress = context.calculate_progress()
                
                # Yield step result
                yield {
                    "type": "step_complete",
                    "step": step_count,
                    "executed_nodes": list(results.keys()),
                    "progress": progress,
                    "scheduler_stats": self._scheduler.get_execution_stats(),
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
        """Execute a single node with event notifications.
        
        Simplified version that delegates to helper methods for cleaner organization.
        """
        node_id = node.id
        start_time = time.time()
        
        # Emit node started event
        await self._emit_node_started(context, node)
        
        try:
            # Check for PersonJobNode max iteration
            if await self._should_skip_max_iteration(node, context):
                return await self._handle_max_iteration_reached(node, context)
            
            # Execute the node
            output = await self._execute_node_handler(node, context)
            
            # Process completion
            duration_ms = (time.time() - start_time) * 1000
            token_usage = self._extract_token_usage(output)
            
            # Mark node as completed
            await self._handle_node_completion(node, output, context)
            
            # Emit completion event
            await self._emit_node_completed(
                context, node, output, duration_ms, 
                start_time, token_usage
            )
            
            # Return formatted result
            return self._format_node_result(output)
            
        except Exception as e:
            await self._handle_node_failure(context, node, e)
            raise
    
    async def _should_skip_max_iteration(
        self, 
        node: ExecutableNode, 
        context: TypedExecutionContext
    ) -> bool:
        """Check if PersonJobNode has reached max iterations."""
        from dipeo.diagram_generated.generated_nodes import PersonJobNode
        if isinstance(node, PersonJobNode):
            current_count = context.get_node_execution_count(node.id)
            return current_count >= node.max_iteration
        return False
    
    async def _handle_max_iteration_reached(
        self,
        node: ExecutableNode,
        context: TypedExecutionContext
    ) -> dict[str, Any]:
        """Handle PersonJobNode that has reached max iterations."""
        from dipeo.core.execution.envelope import EnvelopeFactory
        from dipeo.diagram_generated.enums import Status
        
        node_id = node.id
        current_count = context.get_node_execution_count(node_id)
        
        logger.info(
            f"PersonJobNode {node_id} has reached max_iteration "
            f"({node.max_iteration}), transitioning to MAXITER_REACHED"
        )
        
        # Create empty output with MAXITER_REACHED status
        output = EnvelopeFactory.text(
            "",
            node_id=str(node_id),
            meta={"status": Status.MAXITER_REACHED.value}
        )
        
        # Transition state
        context.transition_node_to_maxiter(node_id, output)
        
        # Emit completion event
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
    
    async def _execute_node_handler(
        self,
        node: ExecutableNode,
        context: TypedExecutionContext
    ) -> Any:
        """Execute the node's handler."""
        with context.executing_node(node.id):
            exec_count = context.transition_node_to_running(node.id)
            
            # Get handler
            handler = self._get_handler(node.type)
            
            # Resolve inputs
            inputs = await handler.resolve_envelope_inputs(
                request=type('TempRequest', (), {
                    'node': node,
                    'context': context
                })()
            )
            
            # Create request
            request = self._create_execution_request(
                node, context, inputs
            )
            
            # Execute with pre_execute hook
            output = await handler.pre_execute(request)
            if output is None:
                output = await handler.execute_with_envelopes(request, inputs)
            
            return output
    
    def _create_execution_request(
        self,
        node: ExecutableNode,
        context: TypedExecutionContext,
        inputs: Any
    ) -> "ExecutionRequest":
        """Create an ExecutionRequest for the handler."""
        from dipeo.application.execution.execution_request import ExecutionRequest
        
        # Include diagram metadata
        request_metadata = {}
        if hasattr(context.diagram, 'metadata') and context.diagram.metadata:
            request_metadata['diagram_source_path'] = context.diagram.metadata.get('diagram_source_path')
            request_metadata['diagram_id'] = context.diagram.metadata.get('diagram_id')
        
        return ExecutionRequest(
            node=node,
            context=context,
            inputs=inputs,
            services=self.service_registry,
            metadata=request_metadata,
            execution_id=context.execution_id,
            parent_container=context.container,
            parent_registry=self.service_registry
        )
    
    def _extract_token_usage(self, output: Any) -> dict | None:
        """Extract token usage from output metadata."""
        if hasattr(output, 'metadata') and output.metadata:
            if hasattr(output, 'get_metadata_dict'):
                metadata_dict = output.get_metadata_dict()
                return metadata_dict.get('token_usage')
        return None
    
    async def _emit_node_started(
        self, 
        context: TypedExecutionContext, 
        node: ExecutableNode
    ) -> None:
        """Emit node started event."""
        await context.emit_event(
            EventType.NODE_STARTED,
            {
                "node_id": str(node.id),
                "node_type": node.type,
                "node_name": getattr(node, 'name', str(node.id))
            }
        )
    
    async def _emit_node_completed(
        self,
        context: TypedExecutionContext,
        node: ExecutableNode,
        output: Any,
        duration_ms: float,
        start_time: float,
        token_usage: dict | None
    ) -> None:
        """Emit node completed event."""
        node_state = context.get_node_state(node.id)
        exec_count = context.get_node_execution_count(node.id)
        
        event_data = {
            "node_id": str(node.id),
            "node_type": node.type,
            "node_name": getattr(node, 'name', str(node.id)),
            "status": node_state.status.value if node_state else "unknown",
            "output": self._serialize_output(output),
            "node_state": node_state,
            "metrics": {
                "duration_ms": duration_ms,
                "start_time": start_time,
                "end_time": start_time + duration_ms / 1000,
                "execution_count": exec_count
            }
        }
        
        if token_usage:
            event_data["metrics"]["token_usage"] = token_usage
        
        await context.emit_event(EventType.NODE_COMPLETED, event_data)
    
    async def _handle_node_failure(
        self,
        context: TypedExecutionContext,
        node: ExecutableNode,
        error: Exception
    ) -> None:
        """Handle node execution failure."""
        logger.error(f"Error executing node {node.id}: {error}", exc_info=True)
        
        # Transition to failed state
        context.transition_node_to_failed(node.id, str(error))
        
        # Emit node failed event
        await context.emit_event(
            EventType.NODE_FAILED,
            {
                "node_id": str(node.id),
                "node_type": node.type,
                "node_name": getattr(node, 'name', str(node.id)),
                "error": str(error),
                "error_type": type(error).__name__
            }
        )
    
    def _format_node_result(self, output: Any) -> dict[str, Any]:
        """Format node output for return."""
        if hasattr(output, 'to_dict'):
            return output.to_dict()
        elif hasattr(output, 'value'):
            result = {"value": output.value}
            if hasattr(output, 'metadata') and output.metadata:
                result["metadata"] = output.metadata
            return result
        else:
            return {"value": output}
    
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