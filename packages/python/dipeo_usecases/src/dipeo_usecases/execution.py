"""Local execution service for running diagrams without server dependency."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo_core import BaseService, SupportsExecution, get_global_registry
from dipeo_domain import ExecutionStatus, NodeExecutionStatus
from dipeo_domain.models import DomainDiagram, DomainNode, NodeOutput

from .execution_view import LocalExecutionView, NodeView

if TYPE_CHECKING:
    from .context import ApplicationContext

log = logging.getLogger(__name__)


class LocalExecutionService(BaseService, SupportsExecution):
    """Local execution service for CLI and tests."""

    def __init__(self, app_context: ApplicationContext):
        """Initialize with application context."""
        super().__init__()
        self.app_context = app_context
        self._pending_updates: list[dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the service."""
        # Import handlers to ensure they are registered
        from . import handlers  # noqa: F401

    async def execute_diagram(
        self,
        diagram: dict[str, Any] | str | DomainDiagram,
        options: dict[str, Any],
        execution_id: str,
        interactive_handler=None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute diagram locally with streaming updates."""
        log.info(f"LocalExecutionService.execute_diagram called with execution_id: {execution_id}")

        # Prepare diagram
        if isinstance(diagram, dict):
            diagram_obj = DomainDiagram.model_validate(diagram)
        elif isinstance(diagram, str):
            # In local mode, we expect the diagram to be passed as data, not ID
            raise ValueError("Local execution requires diagram data, not ID")
        else:
            diagram_obj = diagram

        # Create start update
        start_update = {
            "type": "execution_start",
            "execution_id": execution_id,
        }
        yield start_update

        try:
            # Get handlers from registry
            registry = get_global_registry()
            
            # Build execution view
            execution_view = LocalExecutionView(diagram_obj)
            
            # Assign handlers to node views
            for node_id, node_view in execution_view.node_views.items():
                handler_class = registry.get_handler(node_view.node.type)
                if not handler_class:
                    raise ValueError(f"No handler registered for node type: {node_view.node.type}")
                node_view.handler = handler_class()
            
            # Execute nodes in topological order
            for level_num, level_nodes in enumerate(execution_view.execution_order):
                log.info(f"Executing level {level_num} with nodes: {[n.id for n in level_nodes]}")
                
                # Execute all nodes in this level in parallel
                tasks = []
                for node_view in level_nodes:
                    if self._can_execute_node(node_view):
                        tasks.append(self._execute_node(
                            node_view, execution_id, options, execution_view
                        ))
                    else:
                        log.warning(f"Cannot execute node {node_view.id} - dependencies not met")
                
                if tasks:
                    # Gather results and yield updates
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for updates in results:
                        if isinstance(updates, Exception):
                            log.error(f"Node execution failed: {updates}")
                            continue
                        for update in updates:
                            yield update
            
            # Handle iterative execution (for loops, conditions, etc.)
            async for update in self._execute_iterative_nodes(execution_view, execution_id, options):
                yield update

            # Send execution complete
            complete_update = {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": "completed",
            }
            yield complete_update

        except Exception as e:
            log.error(f"Execution failed: {e}")
            error_update = {
                "type": "execution_error",
                "execution_id": execution_id,
                "error": str(e),
            }
            yield error_update
            raise

    def _can_execute_node(self, node_view: NodeView) -> bool:
        """Check if a node can be executed based on its dependencies."""
        # Node can execute if it hasn't been executed yet and all dependencies are satisfied
        if node_view.output is not None:
            return False
        
        # Check if all incoming edges have outputs
        for edge in node_view.incoming_edges:
            if edge.source_view.output is None:
                return False
        
        return True

    async def _execute_node(
        self,
        node_view: NodeView,
        execution_id: str,
        options: dict[str, Any],
        execution_view: LocalExecutionView,
    ) -> list[dict[str, Any]]:
        """Execute a single node and return updates."""
        updates = []
        
        # Send running update
        updates.append({
            "type": "node_update",
            "execution_id": execution_id,
            "node_id": node_view.id,
            "status": "running",
        })
        
        try:
            # Create runtime context
            from dipeo_core import RuntimeContext
            
            context = RuntimeContext(
                execution_id=execution_id,
                current_node_id=node_view.id,
                variables=options.get("variables", {}),
            )
            
            # Get inputs from connected nodes
            inputs = node_view.get_active_inputs()
            
            # Get required services
            required_services = {}
            if node_view.handler:
                for service_name in node_view.handler.requires_services:
                    service = getattr(self.app_context, f"{service_name}_service", None)
                    if service:
                        required_services[service_name] = service
                
                # Execute handler
                output = await node_view.handler.execute(
                    props=node_view.handler.schema.model_validate(node_view.data),
                    context=context,
                    inputs=inputs,
                    services=required_services,
                )
                
                # Store output in node view
                node_view.output = output
                node_view.exec_count += 1
                
                # Send completion update
                updates.append({
                    "type": "node_update",
                    "execution_id": execution_id,
                    "node_id": node_view.id,
                    "status": "completed",
                    "output": output.model_dump() if output else None,
                })
            
        except Exception as e:
            log.error(f"Node {node_view.id} execution failed: {e}")
            updates.append({
                "type": "node_update",
                "execution_id": execution_id,
                "node_id": node_view.id,
                "status": "failed",
                "error": str(e),
            })
        
        return updates

    async def _execute_iterative_nodes(
        self,
        execution_view: LocalExecutionView,
        execution_id: str,
        options: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute nodes that require iteration (loops, conditions)."""
        max_iterations = 100
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Find nodes that are ready to execute
            ready_nodes = []
            for node_id, node_view in execution_view.node_views.items():
                # Check max iteration for job/person_job nodes
                if node_view.node.type in ["job", "person_job"]:
                    max_iter = node_view.data.get("maxIteration", 1)
                    if node_view.exec_count >= max_iter:
                        continue
                
                # Check if node can execute
                if self._can_execute_node(node_view):
                    ready_nodes.append(node_view)
            
            if not ready_nodes:
                break
            
            # Execute ready nodes in parallel
            tasks = []
            for node_view in ready_nodes:
                tasks.append(self._execute_node(node_view, execution_id, options, execution_view))
            
            # Gather results and yield updates
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for updates in results:
                    if isinstance(updates, Exception):
                        log.error(f"Iterative node execution failed: {updates}")
                        continue
                    for update in updates:
                        yield update