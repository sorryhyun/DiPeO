# Refactored execution engine using StatefulExecutableDiagram and iterators.

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Dict, Optional

from dipeo.application.execution.context import UnifiedExecutionContext
from dipeo.application.execution.iterators import AsyncExecutionIterator
from dipeo.application.execution.stateful_diagram import StatefulExecutableDiagram
from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage

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
    
    async def execute_with_executable(
        self,
        executable_diagram: "ExecutableDiagram",
        context: UnifiedExecutionContext,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        # Create stateful wrapper
        stateful_diagram = StatefulExecutableDiagram(executable_diagram, context)
        
        # Notify observers of execution start
        for observer in self.observers:
            diagram_id = context.get_global_context().get("diagram_id")
            await observer.on_execution_start(execution_id, diagram_id)
        
        try:
            # Create async execution iterator
            max_parallel = options.get("max_parallel_nodes", 10)
            
            # The diagram will be passed through context's global context
            # No need to extract it here
            
            # Get controller from context's execution state
            controller = getattr(context.execution_state, '_controller', None)
            
            iterator = AsyncExecutionIterator(
                stateful_diagram=stateful_diagram,
                max_parallel_nodes=max_parallel,
                node_executor=self._create_node_executor_wrapper(
                    context, options, interactive_handler, 
                    diagram=None,  # Will be retrieved from context
                    controller=controller
                )
            )
            
            # Execute using iterator pattern
            step_count = 0
            async for step in iterator:
                if not step.nodes:
                    # Empty step - waiting for running nodes
                    await asyncio.sleep(0.1)
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
                is_complete = stateful_diagram.is_complete()
                log.debug(f"After step {step_count}, is_complete={is_complete}")
                if is_complete:
                    log.info(f"Execution marked as complete after step {step_count}")
                    break
            
            # Notify completion
            for observer in self.observers:
                await observer.on_execution_complete(execution_id)
            
            # Final completion update
            yield {
                "type": "execution_complete",
                "total_steps": step_count,
                "execution_path": stateful_diagram.get_execution_path(),
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
        
        # Create UnifiedExecutionContext from controller's state
        if hasattr(controller, 'state_adapter') and controller.state_adapter:
            # Get execution state from the adapter
            execution_state = controller.state_adapter.execution_state
            
            # Store controller reference in execution state for later access
            execution_state._controller = controller
            
            # Create context from execution state
            context = UnifiedExecutionContext(
                execution_state=execution_state,
                container=getattr(self.service_registry, '_container', None),
            )
        else:
            raise ValueError("Controller must have a state_adapter")
        
        # Store diagram in context for access by node executor
        context.update_global_context({"diagram": diagram})
        
        # Delegate to new execution method
        async for update in self.execute_with_executable(
            executable_diagram=executable_diagram,
            context=context,
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
                        executable_diagram, context
                    )
                }
            else:
                yield update
    
    def _create_node_executor_wrapper(
        self,
        context: UnifiedExecutionContext,
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
                # Get diagram from context if not provided
                execution_diagram = diagram
                if not execution_diagram:
                    # Try to get from context's global context
                    global_ctx = context.get_global_context()
                    execution_diagram = global_ctx.get("diagram") if global_ctx else None
                
                if not execution_diagram:
                    raise ValueError("No diagram available for execution")
                
                # Get controller from context if not provided
                execution_controller = controller
                if not execution_controller:
                    # Try to get from execution state
                    execution_controller = getattr(context.execution_state, '_controller', None)
                
                if not execution_controller:
                    raise ValueError("No controller available for execution")
                
                # Actually execute the node using NodeExecutor
                await self.node_executor.execute_node(
                    node_id=str(node.id),
                    diagram=execution_diagram,
                    controller=execution_controller,
                    execution_id=context.get_execution_id(),
                    options=options,
                    interactive_handler=interactive_handler
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
                        context.get_execution_id(),
                        str(node.id),
                        str(e)
                    )
                raise
        
        return execute_node
    
    async def _execute_single_node(
        self,
        node: "ExecutableNode",
        context: UnifiedExecutionContext,
        options: Dict[str, Any],
        interactive_handler: Optional[Any]
    ) -> Dict[str, Any]:
        # We need to use the existing node_executor, but it expects a DomainDiagram
        # For now, create a minimal wrapper that provides the necessary interface
        
        # The node_executor.execute_node method expects:
        # - node_id: str
        # - diagram: DomainDiagram
        # - controller: ExecutionController
        # - execution_id: str
        # - options: dict
        # - interactive_handler: Optional
        
        # Since we don't have direct access to these in this context,
        # we need to extract the result from the node execution
        # For now, just return a simple result indicating execution
        
        log.debug(f"Executing node {node.id} of type {node.type}")
        
        # Return a simple result for now
        # In a real implementation, this would invoke the actual handler
        return {
            "value": f"Executed {node.type} node {node.id}",
            "metadata": {"node_type": str(node.type)}
        }
    
    def _check_endpoint_executed(
        self, 
        diagram: "ExecutableDiagram", 
        context: UnifiedExecutionContext
    ) -> bool:
        for node in diagram.get_end_nodes():
            if context.is_node_complete(node.id):
                return True
        return False