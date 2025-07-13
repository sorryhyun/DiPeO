# Refactored execution engine using StatefulExecutableDiagram and iterators.

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Dict, Optional

from dipeo.application.execution.iterators import AsyncExecutionIterator
from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage
from dipeo.infra.config.settings import get_settings
from dipeo.core.static.executable_diagram import ExecutableNode

from .node_executor import NodeExecutor

if TYPE_CHECKING:
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.application.protocols import ExecutionObserver

log = logging.getLogger(__name__)


class TypedExecutionEngine:
    """Execution engine that works directly with typed ExecutableDiagram and TypedStatefulExecution.
    
    This is the simplified engine from Phase 6 that leverages static typing throughout.
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
        stateful_execution: TypedStatefulExecution,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        
        # Notify observers of execution start
        for observer in self.observers:
            diagram_id = stateful_execution.diagram_id
            await observer.on_execution_start(execution_id, diagram_id)
        
        try:
            # Create async execution iterator
            max_parallel = options.get("max_parallel_nodes", 10)
            
            # Create iterator with typed execution
            iterator = AsyncExecutionIterator(
                stateful_execution=stateful_execution,
                max_parallel_nodes=max_parallel,
                node_executor=self._create_node_executor_wrapper(
                    stateful_execution, options, interactive_handler
                ),
                node_ready_poll_interval=self._settings.node_ready_poll_interval,
                max_poll_retries=self._settings.node_ready_max_polls
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
                is_complete = stateful_execution.is_complete()
                if is_complete:
                    break
            
            # Notify completion
            for observer in self.observers:
                await observer.on_execution_complete(execution_id)
            
            # Final completion update
            yield {
                "type": "execution_complete",
                "total_steps": step_count,
                "execution_path": [str(node_id) for node_id in stateful_execution.get_completed_nodes()],
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
        stateful_execution: TypedStatefulExecution,
        options: Dict[str, Any],
        interactive_handler: Optional[Any]
    ):
        async def execute_node(node: "ExecutableNode") -> Dict[str, Any]:
            # For the stateful execution to work properly, we need to ensure
            # that nodes are executed and their results are properly tracked.
            

            try:
                # Execute using the typed node executor with full type safety
                await self.node_executor.execute_node(
                    node=node,
                    execution=stateful_execution,
                    handler=None,  # Will be resolved by executor
                    execution_id=stateful_execution.execution_id,
                    options=options,
                    interactive_handler=interactive_handler
                )
                

                # Get the actual node output that was stored by the executor
                node_output = stateful_execution.state.node_outputs.get(str(node.id))
                if node_output:
                    # Return the actual output value
                    return {
                        "value": node_output.value,
                        "metadata": node_output.metadata
                    }
                else:
                    # Fallback if no output was stored
                    return {
                        "value": {"status": "completed", "node_id": str(node.id)},
                        "metadata": {"node_type": str(node.type)}
                    }
                
            except Exception as e:
                log.error(f"Error executing node {node.id}: {e}", exc_info=True)
                # Notify observers of node error
                for observer in self.observers:
                    await observer.on_node_error(
                        stateful_execution.execution_id,
                        str(node.id),
                        str(e)
                    )
                raise
        
        return execute_node


# Backward compatibility alias
StatefulExecutionEngine = TypedExecutionEngine