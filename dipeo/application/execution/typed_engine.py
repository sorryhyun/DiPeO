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
from dipeo.domain.events import EventType, DomainEventBus, DomainEvent
from dipeo.diagram_generated import ExecutionState, NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution import DomainDynamicOrderCalculator
from dipeo.config import get_settings

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

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
        order_calculator: Any | None = None,
        event_bus: DomainEventBus | None = None
    ):
        self.service_registry = service_registry
        self.order_calculator = order_calculator or DomainDynamicOrderCalculator()
        self._settings = get_settings()
        self._managed_event_bus = False
        self._scheduler: NodeScheduler | None = None
        
        # Use provided event bus or create one
        if not event_bus:
            from dipeo.infrastructure.events.adapters import InMemoryEventBus
            self.event_bus = InMemoryEventBus()
            self._managed_event_bus = True
        else:
            self.event_bus = event_bus
    
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
            # Note: We no longer convert events back to observers (EventToObserverAdapter removed)
            # This eliminates unnecessary loops in the event system
            # Observers should be wrapped with ObserverToEventAdapter at injection time instead
        
        context = None
        log_handler = None
        try:
            # Create execution context
            from dipeo.application.execution.states.execution_state_persistence import ExecutionStatePersistence
            from dipeo.diagram_generated import NodeState, Status
            
            context = TypedExecutionContext(
                execution_id=str(execution_state.id),
                diagram_id=str(execution_state.diagram_id),
                diagram=diagram,
                service_registry=self.service_registry,
                event_bus=self.event_bus,
                container=container
            )
            
            # Load persisted state
            node_states = {}  # Temporary dict to load states into
            tracker = context.get_tracker()
            ExecutionStatePersistence.load_from_state(
                execution_state,
                node_states,
                tracker
            )
            
            # Apply loaded states to context
            if node_states:
                context._state_tracker._node_states = node_states
            
            # Initialize remaining nodes
            existing_states = context.state.get_all_node_states()
            for node in diagram.get_nodes_by_type(None) or diagram.nodes:
                if node.id not in existing_states:
                    context._state_tracker.initialize_node(node.id)
            
            # Load variables (metadata is not persisted in ExecutionState)
            context.set_variables(execution_state.variables or {})
            
            # Store parent metadata from options for nested sub-diagrams
            if 'parent_metadata' in options:
                context._parent_metadata = options['parent_metadata']
            
            # Set up execution logging to emit EXECUTION_LOG events
            from dipeo.infrastructure.execution.logging_handler import setup_execution_logging
            log_handler = setup_execution_logging(
                event_bus=self.event_bus,
                execution_id=str(context.execution_id),
                log_level=logging.DEBUG if options.get('debug', False) else logging.INFO
            )
            
            # Initialize scheduler for this execution
            self._scheduler = NodeScheduler(diagram, self.order_calculator, context)
            
            # Set scheduler reference in context for token events
            context.scheduler = self._scheduler
            
            # Extract metadata from options
            for key, value in options.get('metadata', {}).items():
                context.set_execution_metadata(key, value)
            
            # Emit execution started event
            await context.emit_execution_started()
            
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
                    # No nodes ready, wait briefly (using a reasonable default)
                    poll_interval = getattr(self._settings.execution, 'node_ready_poll_interval', 0.01)
                    await asyncio.sleep(poll_interval)
                    continue
                
                step_count += 1
                
                # Execute ready nodes
                results = await self._execute_nodes(ready_nodes, context)
                
                # Update scheduler with completed nodes
                for node_id in results.keys():
                    self._scheduler.mark_node_completed(NodeID(node_id), context)
                
                # Calculate progress
                from dipeo.application.execution.reporting import calculate_progress
                progress = calculate_progress(context)
                
                # Yield step result
                yield {
                    "type": "step_complete",
                    "step": step_count,
                    "executed_nodes": list(results.keys()),
                    "progress": progress,
                    "scheduler_stats": self._scheduler.get_execution_stats(),
                }
            
            # Execution complete
            execution_path = [str(node_id) for node_id in context.state.get_completed_nodes()]
            from dipeo.diagram_generated import Status
            
            await context.emit_execution_completed(
                status=Status.COMPLETED,
                total_steps=step_count,
                execution_path=execution_path
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
                await context.emit_execution_error(e)
            
            yield {
                "type": "execution_error",
                "error": str(e),
            }
            raise
        finally:
            # Teardown execution logging
            if log_handler:
                from dipeo.infrastructure.execution.logging_handler import teardown_execution_logging
                teardown_execution_logging(log_handler)
            
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
        Now includes token consumption and emission for Phase 2.2.
        """
        node_id = node.id
        start_time = time.time()
        
        # Mark node as running in scheduler for concurrency tracking
        epoch = context.current_epoch()
        if self._scheduler:
            self._scheduler.mark_node_running(node_id, epoch)
        
        # Emit node started event
        await self._emit_node_started(context, node)
        
        try:
            # Check for PersonJobNode max iteration
            if await self._should_skip_max_iteration(node, context):
                return await self._handle_max_iteration_reached(node, context)
            
            # Execute the node
            output = await self._execute_node_handler(node, context)
            
            # Emit outputs as tokens (Phase 2.2)
            # Condition nodes handle their own token emission with branch filtering
            from dipeo.diagram_generated import NodeType
            if node.type != NodeType.CONDITION:
                # Convert single output to dict for compatibility
                if output:
                    outputs = {"default": output} if not isinstance(output, dict) else output
                    context.emit_outputs_as_tokens(node_id, outputs, epoch)
            
            # Process completion
            duration_ms = (time.time() - start_time) * 1000
            token_usage = self._extract_token_usage(output)
            
            # Mark node as completed
            await self._handle_node_completion(node, output, context)
            
            # Mark complete in scheduler for concurrency tracking
            if self._scheduler:
                self._scheduler.mark_node_complete(node_id, epoch)
            
            # Emit completion event
            await self._emit_node_completed(
                context, node, output, duration_ms, 
                start_time, token_usage
            )
            
            # Return formatted result
            return self._format_node_result(output)
            
        except Exception as e:
            # Mark complete in scheduler even on failure
            if self._scheduler:
                self._scheduler.mark_node_complete(node_id, epoch)
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
            current_count = context.state.get_node_execution_count(node.id)
            return current_count >= node.max_iteration
        return False
    
    async def _handle_max_iteration_reached(
        self,
        node: ExecutableNode,
        context: TypedExecutionContext
    ) -> dict[str, Any]:
        """Handle PersonJobNode that has reached max iterations."""
        from dipeo.domain.execution.envelope import EnvelopeFactory
        from dipeo.diagram_generated.enums import Status
        
        node_id = node.id
        current_count = context.state.get_node_execution_count(node_id)
        
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
        context.state.transition_to_maxiter(node_id, output)
        
        # Emit completion event for maxiter
        await context.emit_node_completed(node, None, current_count)
        
        return {"value": "", "status": "MAXITER_REACHED"}
    
    async def _execute_node_handler(
        self,
        node: ExecutableNode,
        context: TypedExecutionContext
    ) -> Any:
        """Execute the node's handler."""
        with context.executing_node(node.id):
            exec_count = context.state.transition_to_running(node.id, context.current_epoch())
            
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
            
            # Call post_execute hook if handler defines it
            if hasattr(handler, 'post_execute'):
                output = handler.post_execute(request, output)
            
            return output
    
    def _create_execution_request(
        self,
        node: ExecutableNode,
        context: TypedExecutionContext,
        inputs: Any
    ) -> "ExecutionRequest":
        """Create an ExecutionRequest for the handler."""
        from dipeo.application.execution.execution_request import ExecutionRequest
        
        # Include diagram metadata and parent metadata from context
        request_metadata = {}
        if hasattr(context.diagram, 'metadata') and context.diagram.metadata:
            request_metadata['diagram_source_path'] = context.diagram.metadata.get('diagram_source_path')
            request_metadata['diagram_id'] = context.diagram.metadata.get('diagram_id')
        
        # Propagate parent metadata if we're in a nested sub-diagram
        if hasattr(context, '_parent_metadata') and context._parent_metadata:
            request_metadata.update(context._parent_metadata)
        
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
        await context.emit_node_started(node)
    
    async def _emit_node_completed(
        self,
        context: TypedExecutionContext,
        node: ExecutableNode,
        envelope: Any,  # Should be Envelope but keeping Any for now
        duration_ms: float,
        start_time: float,
        token_usage: dict | None
    ) -> None:
        """Emit node completed event."""
        # Add timing metadata to envelope if it's an Envelope
        if hasattr(envelope, 'meta') and isinstance(envelope.meta, dict):
            envelope.meta['execution_time_ms'] = duration_ms
            if token_usage:
                envelope.meta['token_usage'] = token_usage
        
        exec_count = context.state.get_node_execution_count(node.id)
        await context.emit_node_completed(node, envelope, exec_count)
    
    async def _handle_node_failure(
        self,
        context: TypedExecutionContext,
        node: ExecutableNode,
        error: Exception
    ) -> None:
        """Handle node execution failure."""
        logger.error(f"Error executing node {node.id}: {error}", exc_info=True)
        
        # Transition to failed state
        context.state.transition_to_failed(node.id, str(error))
        
        # Emit node failed event
        await context.emit_node_error(node, error)
    
    def _format_node_result(self, envelope: Any) -> dict[str, Any]:
        """Format envelope output for return."""
        # If it's an Envelope, extract the body
        if hasattr(envelope, 'body'):
            body = envelope.body
            if hasattr(body, 'dict'):
                return body.dict()
            elif hasattr(body, 'model_dump'):
                return body.model_dump()
            elif isinstance(body, dict):
                return body
            else:
                return {"value": str(body)}
        # Fallback for non-Envelope (should be removed eventually)
        elif hasattr(envelope, 'to_dict'):
            return envelope.to_dict()
        elif hasattr(envelope, 'value'):
            result = {"value": envelope.value}
            if hasattr(envelope, 'metadata') and envelope.metadata:
                result["metadata"] = envelope.metadata
            return result
        else:
            return {"value": envelope}
    
    def _get_handler(self, node_type: str):
        """Get handler for node type."""
        from dipeo.application import get_global_registry
        from dipeo.application.execution.handler_factory import HandlerFactory
        
        registry = get_global_registry()
        if not hasattr(registry, '_service_registry') or registry._service_registry is None:
            HandlerFactory(self.service_registry)
        
        # Ensure we use the string value, not the enum itself
        if hasattr(node_type, 'value'):
            node_type = node_type.value
        
        return registry.create_handler(node_type)
    
    async def _handle_node_completion(
        self,
        node: ExecutableNode,
        envelope: Any,  # Should be Envelope
        context: TypedExecutionContext
    ) -> None:
        """Handle node completion and state transitions."""
        # All nodes complete normally - PersonJob max_iteration is handled in the handler
        context.state.transition_to_completed(node.id, envelope)
    
    # DEPRECATED: This method is no longer needed as envelopes handle their own serialization
    # It can be removed once all references are updated
    def _serialize_output(self, envelope: Any) -> dict[str, Any]:
        """[DEPRECATED] Serialize envelope output for event data."""
        try:
            if hasattr(envelope, 'body'):
                body = envelope.body
                if hasattr(body, 'dict'):
                    return body.dict()
                elif hasattr(body, 'model_dump'):
                    return body.model_dump()
                elif isinstance(body, dict):
                    return body
                else:
                    return {"value": str(body)}
            # Fallback for non-Envelope
            elif hasattr(envelope, 'to_dict'):
                return envelope.to_dict()
            elif hasattr(envelope, 'value'):
                result = {"value": envelope.value}
                if hasattr(envelope, 'metadata') and envelope.metadata:
                    result["metadata"] = envelope.metadata
                return result
            else:
                return {"value": str(envelope)}
        except Exception as e:
            logger.warning(f"Failed to serialize output: {e}")
            return {"value": "output_serialization_failed"}