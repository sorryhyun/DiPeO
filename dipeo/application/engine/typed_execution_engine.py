# Refactored execution engine using ExecutionRuntime.

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_runtime import ExecutionRuntime
from dipeo.application.execution.iterators.simple_iterator import SimpleAsyncIterator
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.infra.config.settings import get_settings

from .node_executor import NodeExecutor

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
        self.node_executor = NodeExecutor(service_registry, observers)
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
            # For the execution runtime to work properly, we need to ensure
            # that nodes are executed and their results are properly tracked.
            

            try:
                # Execute using the typed node executor with full type safety
                await self.node_executor.execute_node(
                    node=node,
                    execution=execution_runtime,
                    handler=None,  # Will be resolved by executor
                    execution_id=execution_id,
                    options=options,
                    interactive_handler=interactive_handler
                )
                

                # Get the actual node output that was stored by the executor
                node_output = execution_runtime.state.node_outputs.get(str(node.id))
                if node_output:
                    # Return the NodeOutput instance directly to avoid double wrapping
                    return node_output
                else:
                    # Fallback if no output was stored - create a proper NodeOutput
                    from dipeo.models import NodeOutput
                    return NodeOutput(
                        value={"status": "completed", "node_id": str(node.id)},
                        metadata={"node_type": str(node.type)},
                        node_id=str(node.id)
                    )
                
            except Exception as e:
                log.error(f"Error executing node {node.id}: {e}", exc_info=True)
                # Notify observers of node error
                for observer in self.observers:
                    await observer.on_node_error(
                        execution_runtime.execution_id,
                        str(node.id),
                        str(e)
                    )
                raise
        
        return execute_node


# Backward compatibility alias
StatefulExecutionEngine = TypedExecutionEngine