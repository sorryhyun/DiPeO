"""Unified execution engine that simplifies the two-phase execution model.

This module provides a single execution loop that handles both initial
topological execution and iterative execution in a unified manner.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Set

from dipeo_domain.models import NodeOutput, NodeState, NodeType, HandleLabel, NodeExecutionStatus, TokenUsage

log = logging.getLogger(__name__)


@dataclass
class NodeExecutionState:
    """Tracks execution state for a single node."""
    node_id: str
    node_type: str
    exec_count: int = 0
    max_iterations: int = 1
    completed: bool = False
    output: Optional[NodeOutput] = None
    
    def can_execute(self) -> bool:
        """Check if node can execute."""
        if self.completed:
            return False
        return self.exec_count < self.max_iterations
    
    def should_continue_iterating(self) -> bool:
        """Check if node should continue iterating."""
        return not self.completed and self.exec_count < self.max_iterations


@dataclass
class UnifiedExecutionController:
    """Unified controller for execution flow."""
    
    node_states: Dict[str, NodeExecutionState] = field(default_factory=dict)
    ready_queue: List[str] = field(default_factory=list)
    executed_nodes: Set[str] = field(default_factory=set)
    endpoint_executed: bool = False
    iteration_count: int = 0
    max_global_iterations: int = 100
    
    def initialize_nodes(self, node_views: Dict[str, Any]) -> None:
        """Initialize node states from views."""
        for node_id, node_view in node_views.items():
            max_iter = 1
            if node_view.node.type in [NodeType.person_job.value, NodeType.job.value]:
                max_iter = node_view.data.get("max_iteration", 1)
            
            self.node_states[node_id] = NodeExecutionState(
                node_id=node_id,
                node_type=node_view.node.type,
                max_iterations=max_iter
            )
    
    def get_ready_nodes(self, execution_view: Any) -> List[str]:
        """Get all nodes ready for execution."""
        ready = []
        
        for node_id, state in self.node_states.items():
            log.debug(f"Checking node {node_id}: type={state.node_type}, exec_count={state.exec_count}, max_iter={state.max_iterations}, completed={state.completed}")
            if not state.can_execute():
                log.debug(f"  - Node {node_id} cannot execute (completed={state.completed} or reached max iterations)")
                continue
                
            node_view = execution_view.node_views[node_id]
            
            # Check dependencies
            if self._dependencies_satisfied(node_view, execution_view):
                ready.append(node_id)
                log.debug(f"  - Node {node_id} is ready for execution")
            else:
                log.debug(f"  - Node {node_id} dependencies not satisfied")
        
        log.debug(f"Total ready nodes: {ready}")
        return ready
    
    def _dependencies_satisfied(self, node_view: Any, execution_view: Any) -> bool:
        """Check if all dependencies are satisfied for a node."""
        # Start nodes have no dependencies
        if node_view.node.type == NodeType.start.value:
            return True
        
        # Debug logging
        log.debug(f"Checking dependencies for node {node_view.id} (type: {node_view.node.type})")
        
        # For person_job nodes on first execution, only check "first" handle dependencies
        if (node_view.node.type == NodeType.person_job.value and 
            self.node_states[node_view.id].exec_count == 0):
            # Check if this node has any "first" handle connections
            has_first_handle = any(edge.target_handle == "first" for edge in node_view.incoming_edges)
            
            if has_first_handle:
                # If it has first handles, require at least one to be satisfied
                first_handle_satisfied = False
                for edge in node_view.incoming_edges:
                    source_state = self.node_states.get(edge.source_view.id)
                    if not source_state:
                        continue
                        
                    log.debug(f"  - Edge from {edge.source_view.id}, target_handle={edge.target_handle}, source has output={source_state.output is not None}")
                    
                    if edge.target_handle == "first" and source_state.output is not None:
                        first_handle_satisfied = True
                        log.debug(f"  - First handle satisfied by {edge.source_view.id}")
                    elif edge.target_handle != "first":
                        # Ignore non-first handles on first execution
                        log.debug(f"  - Ignoring {edge.target_handle} handle on first execution")
                        
                if first_handle_satisfied:
                    log.debug(f"  -> Dependencies satisfied for {node_view.id} (first execution)")
                    return True
                else:
                    log.debug(f"  -> Dependencies NOT satisfied for {node_view.id} (no first handle input)")
                    return False
            else:
                # If no first handles exist, fall through to normal dependency checking
                log.debug(f"  - No first handles found for {node_view.id}, checking all dependencies normally")
                # Don't return here, let it fall through to the normal dependency check below
        
        # For all other cases, check all dependencies normally
        for edge in node_view.incoming_edges:
            source_state = self.node_states.get(edge.source_view.id)
            if not source_state:
                log.debug(f"  - No state found for source {edge.source_view.id}")
                continue
                
            # Skip "first" edges after first execution
            if (node_view.node.type == NodeType.person_job.value and 
                edge.target_handle == "first" and 
                self.node_states[node_view.id].exec_count > 0):
                log.debug(f"  - Skipping first edge from {edge.source_view.id} (already executed)")
                continue
            
            # Source must have produced output
            if source_state.output is None:
                log.debug(f"  - Dependency {edge.source_view.id} not executed yet (no output)")
                return False
            else:
                log.debug(f"  - Dependency {edge.source_view.id} satisfied (has output, exec_count={source_state.exec_count})")
        
        log.debug(f"  -> All dependencies satisfied for {node_view.id}")
        return True
    
    def mark_executed(self, node_id: str, output: NodeOutput) -> None:
        """Mark node as executed with output."""
        state = self.node_states[node_id]
        state.exec_count += 1
        state.output = output
        
        log.debug(f"Marked {node_id} as executed (exec_count={state.exec_count}, type={state.node_type})")
        
        # Check if node is completed
        if state.exec_count >= state.max_iterations:
            state.completed = True
            log.debug(f"  - Node {node_id} completed (reached max_iterations={state.max_iterations})")
        
        # Track endpoint execution
        if state.node_type == NodeType.endpoint.value:
            self.endpoint_executed = True
        
        self.executed_nodes.add(node_id)
    
    def should_continue(self) -> bool:
        """Check if execution should continue."""
        if self.endpoint_executed:
            return False
            
        if self.iteration_count >= self.max_global_iterations:
            return False
        
        # Check if any node can still execute
        return any(state.can_execute() for state in self.node_states.values())
    
    def increment_iteration(self) -> None:
        """Increment global iteration counter."""
        self.iteration_count += 1


class UnifiedExecutionEngine:
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
        from dipeo_core import get_global_registry
        
        execution_view = LocalExecutionView(diagram)
        controller = UnifiedExecutionController(
            max_global_iterations=options.get("max_iterations", 100)
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
                
                log.debug(f"Iteration {controller.iteration_count}: {len(ready_nodes)} nodes ready")
                log.debug(f"Ready nodes: {ready_nodes}")
                log.debug(f"Executed nodes so far: {controller.executed_nodes}")
                
                if not ready_nodes:
                    # No nodes ready, check for deadlock
                    if not controller.executed_nodes:
                        raise RuntimeError("No nodes ready for execution - possible deadlock")
                    log.debug("No more nodes ready, ending execution")
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
        controller: UnifiedExecutionController,
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
        controller: UnifiedExecutionController,
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
                
                # Execute handler
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
        from dipeo_core.unified_context import UnifiedExecutionContext
        
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