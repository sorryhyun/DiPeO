# Refactored execution engine using ExecutionRuntime.

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_runtime import ExecutionRuntime
from dipeo.application.execution.iterators.simple_iterator import SimpleAsyncIterator
from dipeo.core.execution.node_executor import ModernNodeExecutor
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
        self._modern_executor: ModernNodeExecutor | None = None
        self._settings = get_settings()
    
    async def execute(
        self,
        execution_runtime: ExecutionRuntime,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        
        # Initialize ModernNodeExecutor with the runtime's tracker
        if hasattr(execution_runtime, '_tracker'):
            self._modern_executor = ModernNodeExecutor(execution_runtime._tracker)
        
        # Notify observers of execution start
        for observer in self.observers:
            diagram_id = execution_runtime.diagram_id
            await observer.on_execution_start(execution_id, diagram_id)
        
        try:
            # Create async execution iterator
            # max_parallel = options.get("max_parallel_nodes", 10)  # Reserved for future use
            
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
                    # Use shorter interval from settings for more responsive execution
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
            # Use ModernNodeExecutor for cleaner execution flow
            if not self._modern_executor:
                raise RuntimeError("ModernNodeExecutor not initialized")
            
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
                
                # Execute using ModernNodeExecutor
                output = await self._modern_executor.execute_node(
                    node=node,
                    context=execution_runtime,
                    inputs=inputs,
                    handler=handler
                )
                
                # Update node state without calling tracker (ModernNodeExecutor already did that)
                # This also stores the output
                execution_runtime.update_node_state_without_tracker(node.id, output)
                
                # Handle PersonJobNode special logic
                from dipeo.core.static.generated_nodes import PersonJobNode
                
                if isinstance(node, PersonJobNode):
                    exec_count = execution_runtime.get_node_execution_count(node.id)
                    
                    if exec_count >= node.max_iteration:
                        # Check if output indicates max iteration was hit
                        if output and output.metadata and output.metadata.get("skipped") and "Max iteration" in output.metadata.get("reason", ""):
                            log.debug(f"[ModernNodeExecutor] Setting node {node.id} to MAXITER_REACHED status")
                            execution_runtime.transition_node_to_maxiter(node.id)
                    else:
                        # Not at max iteration yet, reset to pending for next iteration
                        log.debug(f"[ModernNodeExecutor] Resetting node {node.id} to PENDING for next iteration")
                        execution_runtime.reset_node(node.id)
                
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