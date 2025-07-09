"""Unified execution controller for managing execution flow and state.

This module provides the controller that tracks node execution states
and determines which nodes are ready to execute based on dependencies.
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from dipeo.domain.services.execution import ExecutionFlowService
from dipeo.models import NodeOutput, NodeType

if TYPE_CHECKING:
    from .execution_view import LocalExecutionView, NodeView

log = logging.getLogger(__name__)


@dataclass
class NodeExecutionState:
    """Tracks execution state for a single node."""
    node_id: str
    node_type: str
    exec_count: int = 0
    max_iterations: int = 1
    completed: bool = False
    output: NodeOutput | None = None
    
    def can_execute(self) -> bool:
        """Check if node can execute."""
        if self.completed:
            return False
        return self.exec_count < self.max_iterations
    
    def should_continue_iterating(self) -> bool:
        """Check if node should continue iterating."""
        return not self.completed and self.exec_count < self.max_iterations


@dataclass
class ExecutionController:
    """Unified controller for execution flow."""
    
    execution_flow_service: ExecutionFlowService
    node_states: dict[str, NodeExecutionState] = field(default_factory=dict)
    ready_queue: list[str] = field(default_factory=list)
    executed_nodes: set[str] = field(default_factory=set)
    endpoint_executed: bool = False
    iteration_count: int = 0
    max_global_iterations: int = 100
    
    def initialize_nodes(self, node_views: dict[str, "NodeView"]) -> None:
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
    
    def get_ready_nodes(self, execution_view: "LocalExecutionView") -> list[str]:
        """Get all nodes ready for execution."""
        # Delegate to domain service
        node_outputs = {state.node_id: state.output for state in self.node_states.values() if state.output}
        node_exec_counts = {state.node_id: state.exec_count for state in self.node_states.values()}
        
        ready_nodes = self.execution_flow_service.get_ready_nodes(
            diagram=execution_view.diagram,
            executed_nodes=self.executed_nodes,
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts
        )
        
        # Filter by nodes that can still execute based on local state
        ready = []
        for node in ready_nodes:
            state = self.node_states.get(node.id)
            if state and state.can_execute():
                ready.append(node.id)
        
        log.debug(f"Ready nodes: {ready}")
        return ready
    
    
    def mark_executed(self, node_id: str, output: NodeOutput) -> None:
        """Mark node as executed with output."""
        state = self.node_states[node_id]
        state.exec_count += 1
        state.output = output
        
        log.debug(f"Marked node {node_id} as executed (exec_count: {state.exec_count}, has_output: {output is not None})")
        
        # Check if node is completed
        if state.exec_count >= state.max_iterations:
            state.completed = True
        
        # Track endpoint execution
        if state.node_type == NodeType.endpoint.value:
            self.endpoint_executed = True
        
        self.executed_nodes.add(node_id)
    
    def should_continue(self) -> bool:
        """Check if execution should continue."""
        if self.iteration_count >= self.max_global_iterations:
            return False
            
        # Check endpoint execution status
        return any(state.can_execute() for state in self.node_states.values()) and not self.endpoint_executed
    
    def increment_iteration(self) -> None:
        """Increment global iteration counter."""
        self.iteration_count += 1