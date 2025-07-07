"""Unified execution engine that simplifies the two-phase execution model.

This module provides a single execution loop that handles both initial
topological execution and iterative execution in a unified manner.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from dipeo.models import NodeType, NodeExecutionStatus, NodeState, TokenUsage

from .execution_controller import ExecutionController

log = logging.getLogger(__name__)


class ExecutionEngine:
    """Simplified execution engine with unified execution loop."""
    
    def __init__(self, service_registry: Any, observers: Optional[List[Any]] = None):
        self.service_registry = service_registry
        self.observers = observers or []
        self._concurrency_semaphore: Optional[asyncio.Semaphore] = None
    
    async def execute(
        self,
        diagram: Any,
        execution_id: str,
        options: Dict[str, Any],
        interactive_handler: Optional[Any] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute diagram with unified execution loop."""
        
        # Initialize
        max_concurrent = options.get("max_parallel_nodes", 10)
        self._concurrency_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Notify observers
        for observer in self.observers:
            await observer.on_execution_start(
                execution_id, diagram.metadata.id if diagram.metadata else None
            )
        
        # Create execution view and controller
        from .execution_view import LocalExecutionView
        from dipeo.core import get_global_registry
        
        # Get domain services from service registry if available
        input_resolution_service = None
        execution_flow_service = None
        if hasattr(self.service_registry, 'get'):
            input_resolution_service = self.service_registry.get('input_resolution_service')
            execution_flow_service = self.service_registry.get('execution_flow_service')
        
        execution_view = LocalExecutionView(diagram, input_resolution_service)
        
        controller = ExecutionController(
            max_global_iterations=options.get("max_iterations", 100),
            execution_flow_service=execution_flow_service
        )
        
        # Initialize handlers
        registry = get_global_registry()
        for node_id, node_view in execution_view.node_views.items():
            node_def = registry.get(node_view.node.type)
            if not node_def:
                raise ValueError(f"No handler for node type: {node_view.node.type}")
            node_view.handler = node_def.handler
            node_view._handler_def = node_def
        
        # Initialize controller with nodes
        controller.initialize_nodes(execution_view.node_views)
        
        try:
            # Unified execution loop
            while controller.should_continue():
                # Get all ready nodes
                ready_nodes = controller.get_ready_nodes(execution_view)
                
                # Execute ready nodes
                
                if not ready_nodes:
                    # No nodes ready, check for deadlock
                    if not controller.executed_nodes:
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
                    "executed_nodes": len(controller.executed_nodes),
                    "endpoint_executed": controller.endpoint_executed
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
        node_ids: List[str],
        execution_view: Any,
        controller: ExecutionController,
        execution_id: str,
        options: Dict[str, Any],
        interactive_handler: Optional[Any]
    ) -> None:
        """Execute a batch of nodes concurrently."""
        tasks = []
        
        for node_id in node_ids:
            node_view = execution_view.node_views[node_id]
            task = self._execute_node(
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
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    log.error(f"Node execution failed: {result}")
                    raise result
    
    async def _execute_node(
        self,
        node_view: Any,
        execution_view: Any,
        controller: ExecutionController,
        execution_id: str,
        options: Dict[str, Any],
        interactive_handler: Optional[Any]
    ) -> None:
        """Execute a single node."""
        async with self._concurrency_semaphore:
            # Track start time
            start_time = datetime.utcnow()
            
            # Notify observers
            for observer in self.observers:
                await observer.on_node_start(execution_id, node_view.id)
            
            try:
                # Create runtime context
                context = self._create_runtime_context(
                    node_view, execution_id, options, execution_view
                )
                
                # Get inputs
                inputs = node_view.get_active_inputs()
                
                # Get services
                services = self.service_registry.get_handler_services(
                    node_view._handler_def.requires_services
                )
                services["diagram"] = execution_view.diagram
                services["execution_context"] = {
                    "interactive_handler": interactive_handler
                }
                
                # Prepare node data
                node_data = node_view.data.copy() if node_view.data else {}
                if node_view.node.type == NodeType.person_job.value:
                    node_data.setdefault("first_only_prompt", "")
                    node_data.setdefault("max_iteration", 1)
                
                # Execute handler directly with UnifiedExecutionContext
                output = await node_view.handler(
                    props=node_view._handler_def.node_schema.model_validate(node_data),
                    context=context,
                    inputs=inputs,
                    services=services,
                )
                
                # Update state
                node_view.output = output
                node_view.exec_count += 1
                controller.mark_executed(node_view.id, output)
                
                # Create NodeState with output and timing information
                end_time = datetime.utcnow()
                
                # Extract token usage from output metadata if available
                token_usage = None
                if output and output.metadata and "token_usage" in output.metadata:
                    token_usage_data = output.metadata["token_usage"]
                    if token_usage_data:
                        token_usage = TokenUsage(**token_usage_data)
                
                node_state = NodeState(
                    status=NodeExecutionStatus.COMPLETED,
                    started_at=start_time.isoformat(),
                    ended_at=end_time.isoformat(),
                    error=None,
                    token_usage=token_usage,
                    output=output
                )
                
                # Notify observers
                for observer in self.observers:
                    await observer.on_node_complete(
                        execution_id, node_view.id, node_state
                    )
                    
            except Exception as e:
                # Notify observers
                for observer in self.observers:
                    await observer.on_node_error(execution_id, node_view.id, str(e))
                raise
    
    def _create_runtime_context(
        self, node_view: Any, execution_id: str, options: Dict[str, Any], execution_view: Any
    ) -> Any:
        """Create runtime context for node execution."""
        from dipeo.application import UnifiedExecutionContext
        
        # Convert diagram structure to dict format
        edges = [
            {
                "source": arrow.source,
                "target": arrow.target,
                "data": arrow.data,
            }
            for arrow in execution_view.diagram.arrows
        ]
        
        nodes = []
        for node in execution_view.diagram.nodes:
            if hasattr(node, "model_dump"):
                nodes.append(node.model_dump())
            else:
                nodes.append(node)
        
        # Collect outputs
        outputs = {}
        for nv in execution_view.node_views.values():
            if nv.output is not None:
                outputs[nv.id] = nv.output
        
        return UnifiedExecutionContext(
            execution_id=execution_id,
            current_node_id=node_view.id,
            edges=edges,
            nodes=nodes,
            variables=options.get("variables", {}),
            node_outputs=outputs,
            exec_counts={nv.id: nv.exec_count for nv in execution_view.node_views.values()},
            diagram_id=execution_view.diagram.metadata.id if execution_view.diagram.metadata else None,
        )