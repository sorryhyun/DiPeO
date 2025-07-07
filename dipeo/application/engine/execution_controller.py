"""Unified execution controller for managing execution flow and state.

This module provides the controller that tracks node execution states
and determines which nodes are ready to execute based on dependencies.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from dipeo.models import NodeOutput, NodeType


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
class ExecutionController:
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
            if not state.can_execute():
                continue
                
            node_view = execution_view.node_views[node_id]
            
            # Check dependencies
            if self._dependencies_satisfied(node_view, execution_view):
                ready.append(node_id)
        
        return ready
    
    def _dependencies_satisfied(self, node_view: Any, execution_view: Any) -> bool:
        """Check if all dependencies are satisfied for a node."""
        # Start nodes have no dependencies
        if node_view.node.type == NodeType.start.value:
            return True
        
        # Check dependencies for node
        
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
                        
                    if edge.target_handle == "first" and source_state.output is not None:
                        first_handle_satisfied = True
                    elif edge.target_handle != "first":
                        # Ignore non-first handles on first execution
                        pass
                        
                if first_handle_satisfied:
                    return True
                else:
                    return False
            else:
                # If no first handles exist, fall through to normal dependency checking
                pass
        
        # For all other cases, check all dependencies normally
        for edge in node_view.incoming_edges:
            source_state = self.node_states.get(edge.source_view.id)
            if not source_state:
                continue
                
            # Skip "first" edges after first execution
            if (node_view.node.type == NodeType.person_job.value and 
                edge.target_handle == "first" and 
                self.node_states[node_view.id].exec_count > 0):
                continue
            
            # Source must have produced output
            if source_state.output is None:
                return False
        
        return True
    
    def mark_executed(self, node_id: str, output: NodeOutput) -> None:
        """Mark node as executed with output."""
        state = self.node_states[node_id]
        state.exec_count += 1
        state.output = output
        
        # Check if node is completed
        if state.exec_count >= state.max_iterations:
            state.completed = True
        
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