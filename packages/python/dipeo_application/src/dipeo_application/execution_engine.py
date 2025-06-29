"""Core execution engine that can be used by both server and CLI."""

from typing import AsyncIterator, Optional, Protocol, Any
from dataclasses import dataclass
import asyncio
import logging

from dipeo_core import RuntimeContext, get_global_registry
from dipeo_domain import NodeOutput
from .execution_view import LocalExecutionView

log = logging.getLogger(__name__)


class ExecutionObserver(Protocol):
    """Protocol for execution observers (e.g., state persistence, streaming)."""
    
    async def on_execution_start(self, execution_id: str, diagram_id: Optional[str]) -> None: ...
    async def on_node_start(self, execution_id: str, node_id: str) -> None: ...
    async def on_node_complete(self, execution_id: str, node_id: str, output: NodeOutput) -> None: ...
    async def on_node_error(self, execution_id: str, node_id: str, error: str) -> None: ...
    async def on_execution_complete(self, execution_id: str) -> None: ...
    async def on_execution_error(self, execution_id: str, error: str) -> None: ...


@dataclass
class ExecutionEngine:
    """Core execution engine with observer pattern for extensibility."""
    
    service_registry: Any
    observers: list[ExecutionObserver]
    
    async def execute(
        self,
        diagram: Any,
        execution_id: str,
        options: dict[str, Any],
        interactive_handler: Optional[Any] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute diagram with observer notifications."""
        
        # Notify observers of start
        for observer in self.observers:
            await observer.on_execution_start(execution_id, diagram.metadata.id if diagram.metadata else None)
        
        # Build execution view
        execution_view = LocalExecutionView(diagram)
        
        # Get handler registry
        registry = get_global_registry()
        
        # Assign handlers to nodes
        for node_id, node_view in execution_view.node_views.items():
            node_def = registry.get(node_view.node.type)
            if not node_def:
                raise ValueError(f"No handler for node type: {node_view.node.type}")
            node_view.handler = node_def.handler
            node_view._handler_def = node_def
        
        try:
            # Execute topological levels
            for level in execution_view.execution_order:
                await self._execute_level(level, execution_id, options, execution_view, interactive_handler)
            
            # Handle iterative nodes
            await self._execute_iterations(execution_view, execution_id, options, interactive_handler)
            
            # Notify completion
            for observer in self.observers:
                await observer.on_execution_complete(execution_id)
                
        except Exception as e:
            # Notify error
            for observer in self.observers:
                await observer.on_execution_error(execution_id, str(e))
            raise
        
        # Empty generator - observers handle all updates
        return
        yield  # Make this a generator
    
    async def _execute_level(self, nodes, execution_id, options, execution_view, interactive_handler):
        """Execute all nodes in a level concurrently."""
        tasks = []
        for node_view in nodes:
            if self._can_execute(node_view):
                tasks.append(self._execute_node(node_view, execution_id, options, execution_view, interactive_handler))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_node(self, node_view, execution_id, options, execution_view, interactive_handler):
        """Execute a single node with observer notifications."""
        # Notify start
        for observer in self.observers:
            await observer.on_node_start(execution_id, node_view.id)
        
        try:
            # Create runtime context
            context = self._create_runtime_context(node_view, execution_id, options, execution_view)
            
            # Get inputs and services
            inputs = node_view.get_active_inputs()
            services = self.service_registry.get_handler_services(
                node_view._handler_def.requires_services
            )
            
            # Add special services
            services['diagram'] = execution_view.diagram
            services['execution_context'] = {'interactive_handler': interactive_handler}
            
            # Execute handler
            output = await node_view.handler(
                props=node_view._handler_def.node_schema.model_validate(node_view.data),
                context=context,
                inputs=inputs,
                services=services,
            )
            
            # Store output
            node_view.output = output
            node_view.exec_count += 1
            
            # Notify completion
            for observer in self.observers:
                await observer.on_node_complete(execution_id, node_view.id, output)
                
        except Exception as e:
            log.error(f"Node {node_view.id} failed: {e}")
            for observer in self.observers:
                await observer.on_node_error(execution_id, node_view.id, str(e))
            raise
    
    def _can_execute(self, node_view):
        """Check if node can execute."""
        return node_view.output is None and all(
            edge.source_view.output is not None 
            for edge in node_view.incoming_edges
        )
    
    def _create_runtime_context(self, node_view, execution_id, options, execution_view):
        """Create runtime context for node execution."""
        edges = [
            {
                "id": ev.arrow.id,
                "source": ev.arrow.source,
                "target": ev.arrow.target,
                "sourceHandle": getattr(ev.arrow, "source_handle_id", ev.arrow.source),
                "targetHandle": getattr(ev.arrow, "target_handle_id", ev.arrow.target),
            }
            for ev in execution_view.edge_views
        ]
        
        nodes = [
            {
                "id": nv.id,
                "type": nv.type,
                "data": nv.data,
            }
            for nv in execution_view.node_views.values()
        ]
        
        return RuntimeContext(
            execution_id=execution_id,
            current_node_id=node_view.id,
            edges=edges,
            nodes=nodes,
            variables=options.get('variables', {}),
            exec_cnt={nv.id: nv.exec_count for nv in execution_view.node_views.values()},
            diagram_id=execution_view.diagram.metadata.id if execution_view.diagram.metadata else None,
        )
    
    async def _execute_iterations(self, execution_view, execution_id, options, interactive_handler):
        """Execute iterative nodes (loops, conditions)."""
        max_iterations = options.get('max_iterations', 100)
        
        for iteration in range(max_iterations):
            ready_nodes = []
            
            for node_view in execution_view.node_views.values():
                # Check max iteration for specific nodes
                if node_view.node.type in ["job", "person_job"]:
                    max_iter = node_view.data.get("maxIteration", 1)
                    if node_view.exec_count >= max_iter:
                        continue
                
                if self._can_execute(node_view):
                    ready_nodes.append(node_view)
            
            if not ready_nodes:
                break
            
            await self._execute_level(ready_nodes, execution_id, options, execution_view, interactive_handler)