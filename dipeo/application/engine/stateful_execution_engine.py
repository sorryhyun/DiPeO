"""Refactored execution engine using StatefulExecutableDiagram and iterators."""

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
    from dipeo.application.execution.protocols import ExecutionObserver
    from dipeo.models import DomainDiagram
    from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode

log = logging.getLogger(__name__)


class StatefulExecutionEngine:
    """Refactored execution engine using StatefulExecutableDiagram.
    
    This engine uses the new stateful diagram wrapper and execution iterator
    pattern for cleaner execution flow management.
    """
    
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
        """Execute using an ExecutableDiagram and ExecutionContext.
        
        This is the main execution method that uses the new stateful architecture.
        
        Args:
            executable_diagram: The resolved ExecutableDiagram
            context: The execution context for state management
            execution_id: Unique execution identifier
            options: Execution options (max_parallel_nodes, etc.)
            interactive_handler: Optional handler for interactive nodes
            
        Yields:
            Execution updates as dictionaries
        """
        # Create stateful wrapper
        stateful_diagram = StatefulExecutableDiagram(executable_diagram, context)
        
        # Notify observers of execution start
        for observer in self.observers:
            diagram_id = context.get_global_context().get("diagram_id")
            await observer.on_execution_start(execution_id, diagram_id)
        
        try:
            # Create async execution iterator
            max_parallel = options.get("max_parallel_nodes", 10)
            iterator = AsyncExecutionIterator(
                stateful_diagram=stateful_diagram,
                max_parallel_nodes=max_parallel,
                node_executor=self._create_node_executor_wrapper(
                    context, options, interactive_handler
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
                if stateful_diagram.is_complete():
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
        """Execute with pre-prepared execution context (compatibility method).
        
        This method maintains compatibility with the existing interface while
        internally using the new stateful execution approach.
        """
        # Extract ExecutableDiagram if available
        executable_diagram = getattr(diagram, '_executable_diagram', None)
        if not executable_diagram:
            raise ValueError("No ExecutableDiagram found - diagram must be resolved first")
        
        # Create UnifiedExecutionContext from controller's state
        if hasattr(controller, 'state_adapter') and controller.state_adapter:
            # Get execution state from the adapter
            execution_state = controller.state_adapter.execution_state
            
            # Create context from execution state
            context = UnifiedExecutionContext(
                execution_state=execution_state,
                container=getattr(self.service_registry, '_container', None),
            )
        else:
            raise ValueError("Controller must have a state_adapter")
        
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
                    "executed_nodes": len(update["progress"]["completed_nodes"]),
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
        interactive_handler: Optional[Any]
    ):
        """Create a node executor function for the iterator.
        
        This wraps the existing NodeExecutor to work with the iterator pattern.
        """
        async def execute_node(node: "ExecutableNode") -> Dict[str, Any]:
            # Create a node-specific context view
            node_context = context.create_node_view(str(node.id))
            
            # Notify observers of node start
            for observer in self.observers:
                await observer.on_node_start(
                    context.get_execution_id(), 
                    str(node.id), 
                    node.type
                )
            
            try:
                # Execute the node using existing node executor logic
                # This requires adapting the interface slightly
                result = await self._execute_single_node(
                    node=node,
                    context=node_context,
                    options=options,
                    interactive_handler=interactive_handler
                )
                
                # Notify observers of node completion
                for observer in self.observers:
                    await observer.on_node_complete(
                        context.get_execution_id(),
                        str(node.id),
                        result
                    )
                
                return result
                
            except Exception as e:
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
        """Execute a single node and return its result.
        
        This adapts the ExecutableNode to work with the existing handler system.
        """
        # Get the handler for this node type
        handler = self.node_executor.handler_registry.get_handler(node.type)
        if not handler:
            raise ValueError(f"No handler registered for node type: {node.type}")
        
        # Execute the node
        output = await handler.execute(
            node_id=str(node.id),
            node_data=node.to_dict() if hasattr(node, 'to_dict') else {},
            context=context,
            options=options,
            interactive_handler=interactive_handler
        )
        
        # Convert output to result format
        if output:
            return {
                "value": output.value,
                "metadata": output.metadata or {}
            }
        else:
            return {"value": None}
    
    def _check_endpoint_executed(
        self, 
        diagram: "ExecutableDiagram", 
        context: UnifiedExecutionContext
    ) -> bool:
        """Check if any endpoint node has been executed."""
        for node in diagram.get_end_nodes():
            if context.is_node_complete(node.id):
                return True
        return False