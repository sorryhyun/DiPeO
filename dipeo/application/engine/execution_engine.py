"""Unified execution engine that simplifies the two-phase execution model.

This module provides a single execution loop that handles both initial
topological execution and iterative execution in a unified manner.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo.models import NodeExecutionStatus, NodeState, NodeType, TokenUsage

from .execution_controller import ExecutionController
from .node_executor import NodeExecutor

if TYPE_CHECKING:
    from dipeo.application.execution.context import ApplicationExecutionContext
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.domain.services.execution.protocols import ExecutionObserver
    from dipeo.models import DomainDiagram

    from .execution_view import LocalExecutionView, NodeView

log = logging.getLogger(__name__)


class ExecutionEngine:
    """Execution engine focused on coordination and concurrency management.
    
    This engine delegates node-level execution to NodeExecutor while managing:
    - Execution loop coordination
    - Concurrency control
    - Batch execution
    - Event dispatching
    """
    
    def __init__(self, service_registry: "UnifiedServiceRegistry", observers: list["ExecutionObserver"] | None = None):
        self.service_registry = service_registry
        self.observers = observers or []
        self._concurrency_semaphore: asyncio.Semaphore | None = None
        self.node_executor = NodeExecutor(service_registry, observers)
    
    async def execute(
        self,
        diagram: "DomainDiagram",
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute diagram - DEPRECATED.
        
        This method is deprecated and only kept for backward compatibility.
        All diagram preparation and setup should be done in the service layer
        (ExecuteDiagramUseCase) before calling execute_prepared.
        
        Since local execution is not supported, this method should not be used.
        """
        raise NotImplementedError(
            "Direct execution via ExecutionEngine.execute() is deprecated. "
            "Use ExecuteDiagramUseCase for server execution with proper setup and persistence."
        )
    
    async def execute_prepared(
        self,
        execution_view: "LocalExecutionView",
        controller: ExecutionController,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute with pre-prepared execution context.
        
        This method focuses purely on execution flow without any setup or preparation.
        All diagram preparation, handler initialization, and service configuration
        should be done by the calling service layer.
        """
        
        # Initialize concurrency control
        max_concurrent = options.get("max_parallel_nodes", 10)
        self._concurrency_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Notify observers
        for observer in self.observers:
            diagram_id = None
            if hasattr(execution_view, 'diagram') and execution_view.diagram.metadata:
                diagram_id = execution_view.diagram.metadata.id
            await observer.on_execution_start(execution_id, diagram_id)
        
        try:
            # Unified execution loop
            while controller.should_continue():
                # Get all ready nodes
                ready_nodes = controller.get_ready_nodes(execution_view)
                
                # Execute ready nodes
                
                if not ready_nodes:
                    # No nodes ready, check for deadlock
                    if controller.state_adapter and not controller.state_adapter.get_executed_nodes():
                        raise RuntimeError("No nodes ready for execution - possible deadlock")
                    break
                
                # Execute ready nodes concurrently
                await self._execute_batch(
                    ready_nodes,
                    execution_view,
                    controller,
                    execution_id,
                    options,
                    interactive_handler
                )
                
                # Increment iteration counter
                controller.increment_iteration()
                
                # Yield execution update
                yield {
                    "type": "iteration_complete",
                    "iteration": controller.iteration_count,
                    "executed_nodes": len(controller.state_adapter.get_executed_nodes()),
                    "endpoint_executed": controller.state_adapter.is_endpoint_executed()
                }
            
            # Notify completion
            for observer in self.observers:
                await observer.on_execution_complete(execution_id)
                
        except Exception as e:
            # Notify error
            for observer in self.observers:
                await observer.on_execution_error(execution_id, str(e))
            raise
    
    async def _execute_batch(
        self,
        node_ids: list[str],
        execution_view: Any,
        controller: ExecutionController,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None
    ) -> None:
        """Execute a batch of nodes concurrently.
        
        Manages concurrency control and parallel execution of multiple nodes.
        """
        tasks = []
        
        for node_id in node_ids:
            node_view = execution_view.node_views[node_id]
            # Create task with semaphore control
            task = self._execute_node_with_semaphore(
                node_view,
                execution_view,
                controller,
                execution_id,
                options,
                interactive_handler
            )
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for _i, result in enumerate(results):
                if isinstance(result, Exception):
                    log.error(f"Node execution failed: {result}")
                    raise result
    
    async def _execute_node_with_semaphore(
        self,
        node_view: "NodeView",
        execution_view: "LocalExecutionView",
        controller: ExecutionController,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Any | None
    ) -> None:
        """Execute a node with concurrency control."""
        async with self._concurrency_semaphore:
            await self.node_executor.execute_node(
                node_view,
                execution_view,
                controller,
                execution_id,
                options,
                interactive_handler
            )
    
