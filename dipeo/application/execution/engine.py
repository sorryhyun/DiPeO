# Refactored execution engine using ExecutionRuntime.

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_runtime import ExecutionRuntime
from dipeo.application.execution.iterators.simple_iterator import SimpleAsyncIterator
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.infra.config.settings import get_settings

if TYPE_CHECKING:
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.core.ports import ExecutionObserver

log = logging.getLogger(__name__)


class TypedExecutionEngine:
    """Execution engine that works directly with typed ExecutableDiagram and ExecutionRuntime.
    
    This simplified engine leverages the consolidated ExecutionRuntime for cleaner architecture.
    """
    
    def __init__(
        self, 
        service_registry: "UnifiedServiceRegistry", 
        observers: list["ExecutionObserver"] | None = None
    ):
        self.service_registry = service_registry
        self.observers = observers or []
        self._settings = get_settings()
    
    async def execute(
        self,
        execution_runtime: ExecutionRuntime,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        
        # Notify observers of execution start
        for observer in self.observers:
            diagram_id = execution_runtime.diagram_id
            await observer.on_execution_start(execution_id, diagram_id)
        
        try:
            # Create iterator with typed execution
            iterator = SimpleAsyncIterator(
                execution=execution_runtime,
                node_executor=self._create_node_executor_wrapper(
                    execution_runtime, options, interactive_handler, execution_id
                )
            )
            
            # Execute using iterator pattern
            step_count = 0
            async for step in iterator:
                if not step.nodes:
                    # Empty step - waiting for running nodes
                    await asyncio.sleep(self._settings.node_ready_poll_interval)
                    continue
                
                step_count += 1

                # Execute the step
                results = await iterator.execute_step(step)
                
                # Yield progress update
                progress = iterator.get_progress()
                yield {
                    "type": "step_complete",
                    "step": step_count,
                    "executed_nodes": list(results.keys()),
                    "progress": progress,
                }
                
                # Check for completion
                is_complete = execution_runtime.is_complete()
                ready_nodes = execution_runtime.get_ready_nodes()
                if is_complete:
                    break
            
            # Notify completion
            for observer in self.observers:
                await observer.on_execution_complete(execution_id)
            
            # Final completion update
            yield {
                "type": "execution_complete",
                "total_steps": step_count,
                "execution_path": [str(node_id) for node_id in execution_runtime.get_completed_nodes()],
            }
            
        except Exception as e:
            # Notify error
            for observer in self.observers:
                await observer.on_execution_error(execution_id, str(e))
            
            yield {
                "type": "execution_error",
                "error": str(e),
            }
            raise
    
    def _create_node_executor_wrapper(
        self,
        execution_runtime: ExecutionRuntime,
        options: dict[str, Any],
        interactive_handler: Any | None,
        execution_id: str
    ):
        async def execute_node(node: "ExecutableNode") -> dict[str, Any]:
            # Track start for observers
            for observer in self.observers:
                await observer.on_node_start(execution_id, str(node.id))
            
            try:
                # Get handler
                from dipeo.application import get_global_registry
                from dipeo.application.execution.handler_factory import HandlerFactory
                
                registry = get_global_registry()
                
                # Ensure service registry is set
                if not hasattr(registry, '_service_registry') or registry._service_registry is None:
                    HandlerFactory(self.service_registry)
                
                handler = registry.create_handler(node.type)
                
                # Get inputs
                inputs = execution_runtime.resolve_inputs(node)
                
                # Update current node
                execution_runtime._current_node_id[0] = node.id
                
                # Register services
                execution_runtime._service_registry.register("diagram", execution_runtime.diagram)
                execution_runtime._service_registry.register("execution_context", {
                    "interactive_handler": interactive_handler
                })
                
                # Get services dict from handler requirements
                services_dict = {}
                if hasattr(handler, 'requires_services'):
                    for service_name in handler.requires_services:
                        service = execution_runtime.get_service(service_name)
                        if service:
                            services_dict[service_name] = service
                
                # Execute handler directly
                output = await handler.execute(
                    node=node,
                    context=execution_runtime,
                    inputs=inputs,
                    services=services_dict
                )
                
                # Handle PersonJobNode special logic BEFORE marking complete
                from dipeo.core.static.generated_nodes import PersonJobNode, ConditionNode
                
                if isinstance(node, PersonJobNode):
                    exec_count = execution_runtime.get_node_execution_count(node.id)

                    if exec_count >= node.max_iteration:
                        # Always set MAXITER_REACHED when we reach max iterations
                        execution_runtime.transition_node_to_maxiter(node.id, output)

                        # Reset any downstream condition nodes so they can re-evaluate
                        outgoing_edges = execution_runtime.diagram.get_outgoing_edges(node.id)
                        for edge in outgoing_edges:
                            target_node = execution_runtime.diagram.get_node(edge.target_node_id)
                            if target_node and isinstance(target_node, ConditionNode):
                                node_state = execution_runtime.get_node_state(target_node.id)
                                from dipeo.models import NodeExecutionStatus
                                if node_state and node_state.status == NodeExecutionStatus.COMPLETED:
                                    execution_runtime.reset_node(target_node.id)
                    else:
                        # Not at max iteration yet, mark complete then reset to pending for next iteration
                        execution_runtime.transition_node_to_completed(node.id, output)
                        execution_runtime.reset_node(node.id)
                elif isinstance(node, ConditionNode):
                    execution_runtime.transition_node_to_completed(node.id, output)
                else:
                    execution_runtime.transition_node_to_completed(node.id, output)
                
                # Notify observers of completion
                node_state = execution_runtime.get_node_state(node.id)
                for observer in self.observers:
                    await observer.on_node_complete(execution_id, str(node.id), node_state)
                
                # Convert output to dict for iterator
                if hasattr(output, 'to_dict'):
                    return output.to_dict()
                else:
                    return {"value": output.value, "metadata": output.metadata}
                
            except Exception as e:
                log.error(f"Error executing node {node.id}: {e}", exc_info=True)
                # Notify observers of node error
                for observer in self.observers:
                    await observer.on_node_error(execution_id, str(node.id), str(e))
                raise
        
        return execute_node


# Backward compatibility alias
StatefulExecutionEngine = TypedExecutionEngine