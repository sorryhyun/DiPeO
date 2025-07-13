# Refactored execution engine using StatefulExecutableDiagram and iterators.

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Dict, Optional

from dipeo.application.execution.iterators import AsyncExecutionIterator
from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage
from dipeo.infra.config.settings import get_settings

from .node_executor import NodeExecutor

if TYPE_CHECKING:
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.application.protocols import ExecutionObserver
    from dipeo.models import DomainDiagram
    from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode

log = logging.getLogger(__name__)


class StatefulExecutionEngine:
    # Refactored execution engine using StatefulExecutableDiagram and execution iterator pattern
    
    def __init__(
        self, 
        service_registry: "UnifiedServiceRegistry", 
        observers: list["ExecutionObserver"] | None = None
    ):
        self.service_registry = service_registry
        self.observers = observers or []
        self.node_executor = NodeExecutor(service_registry, observers)
        self._settings = get_settings()
    
    async def execute_with_executable(
        self,
        executable_diagram: "ExecutableDiagram",
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
            
            # The diagram will be passed through context's global context
            # No need to extract it here
            
            # Get controller from execution state if available
            controller = getattr(stateful_execution.state, '_controller', None)
            
            # Store executable diagram reference for node executor
            self._executable_diagram = executable_diagram
            
            iterator = AsyncExecutionIterator(
                stateful_execution=stateful_execution,
                max_parallel_nodes=max_parallel,
                node_executor=self._create_node_executor_wrapper(
                    stateful_execution, options, interactive_handler, 
                    diagram=None,  # Will be retrieved from stateful_execution
                    controller=controller
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
                log.info(f"Executing step {step_count} with {len(step.nodes)} nodes")
                
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
    
    async def execute_prepared(
        self,
        diagram: "DomainDiagram",
        controller: Any,  # ExecutionController - kept for compatibility
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        # Extract ExecutableDiagram if available
        executable_diagram = getattr(diagram, '_executable_diagram', None)
        if not executable_diagram:
            raise ValueError("No ExecutableDiagram found - diagram must be resolved first")
        
        # Get TypedStatefulExecution from controller
        if hasattr(controller, 'execution') and controller.execution:
            # Get execution state from the execution
            execution_state = controller.execution.state
            
            # Store controller reference in execution state for later access
            execution_state._controller = controller
            
            # Get or create TypedStatefulExecution
            stateful_execution = getattr(execution_state, '_stateful_execution', None)
            if not stateful_execution:
                # Create it if not exists (backward compatibility)
                from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
                stateful_execution = TypedStatefulExecution(
                    diagram=executable_diagram,
                    execution_state=execution_state,
                    service_registry=self.service_registry,
                    container=getattr(self.service_registry, '_container', None)
                )
        else:
            raise ValueError("Controller must have an execution property")
        
        # Store domain diagram reference for node executor
        self._current_domain_diagram = diagram
        
        # Delegate to new execution method
        async for update in self.execute_with_executable(
            executable_diagram=executable_diagram,
            stateful_execution=stateful_execution,
            execution_id=execution_id,
            options=options,
            interactive_handler=interactive_handler
        ):
            # Transform updates to match expected format
            if update["type"] == "step_complete":
                yield {
                    "type": "iteration_complete", 
                    "iteration": update["step"],
                    "executed_nodes": update["progress"]["completed_nodes"],
                    "endpoint_executed": self._check_endpoint_executed(
                        executable_diagram, stateful_execution
                    )
                }
            else:
                yield update
    
    def _create_node_executor_wrapper(
        self,
        stateful_execution: TypedStatefulExecution,
        options: Dict[str, Any],
        interactive_handler: Optional[Any],
        diagram: Optional["DomainDiagram"] = None,
        controller: Optional[Any] = None
    ):
        async def execute_node(node: "ExecutableNode") -> Dict[str, Any]:
            # For the stateful execution to work properly, we need to ensure
            # that nodes are executed and their results are properly tracked.
            
            log.debug(f"Wrapper executing node {node.id} of type {node.type}")
            
            try:
                # Get diagram from instance if not provided
                execution_diagram = diagram
                if not execution_diagram:
                    execution_diagram = self._current_domain_diagram
                
                if not execution_diagram:
                    raise ValueError("No diagram available for execution")
                
                # Get controller from stateful_execution if not provided
                execution_controller = controller
                if not execution_controller:
                    # Try to get from execution state
                    execution_controller = getattr(stateful_execution.state, '_controller', None)
                
                if not execution_controller:
                    raise ValueError("No controller available for execution")
                
                # Actually execute the node using NodeExecutor
                await self.node_executor.execute_node(
                    node_id=str(node.id),
                    diagram=execution_diagram,
                    controller=execution_controller,
                    execution_id=stateful_execution.execution_id,
                    options=options,
                    interactive_handler=interactive_handler,
                    typed_node=node
                )
                
                log.debug(f"Node {node.id} execution completed")
                
                # Return a result for the iterator
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
    def _check_endpoint_executed(
        self, 
        diagram: "ExecutableDiagram", 
        stateful_execution: TypedStatefulExecution
    ) -> bool:
        for node in diagram.get_end_nodes():
            if stateful_execution.get_node_state(node.id).status == NodeExecutionStatus.COMPLETED:
                return True
        return False