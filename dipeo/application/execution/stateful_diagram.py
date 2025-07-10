"""Stateful wrapper around ExecutableDiagram that maintains execution context."""

from typing import Any, Dict, List, Optional, Set

from dipeo.core.dynamic.execution_context import ExecutionContext
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.models import NodeExecutionStatus, NodeID, NodeState, NodeType


class StatefulExecutableDiagram:
    """Stateful wrapper that combines an ExecutableDiagram with ExecutionContext.
    
    This provides a more convenient interface for step-by-step execution by
    maintaining state and providing methods to query ready nodes and advance
    execution progress.
    """
    
    def __init__(self, diagram: ExecutableDiagram, context: ExecutionContext):
        """Initialize with a diagram and execution context.
        
        Args:
            diagram: The immutable ExecutableDiagram structure
            context: The mutable ExecutionContext for tracking state
        """
        self._diagram = diagram
        self._context = context
        
        # Initialize all nodes to pending state
        for node in self._diagram.nodes:
            if not self._context.get_node_state(node.id):
                self._context.set_node_state(
                    node.id,
                    NodeState(
                        node_id=node.id,
                        status=NodeExecutionStatus.PENDING
                    )
                )
    
    @property
    def diagram(self) -> ExecutableDiagram:
        """Get the underlying ExecutableDiagram."""
        return self._diagram
    
    @property
    def context(self) -> ExecutionContext:
        """Get the execution context."""
        return self._context
    
    def get_ready_nodes(self) -> List[ExecutableNode]:
        """Get all nodes that are ready to execute based on dependencies.
        
        A node is ready if:
        1. It's in PENDING state
        2. All its dependencies (incoming nodes) have completed
        3. For conditional dependencies, the condition evaluated to true
        
        Returns:
            List of nodes ready for execution
        """
        ready_nodes = []
        
        for node in self._diagram.nodes:
            if self._is_node_ready(node):
                ready_nodes.append(node)
        
        return ready_nodes
    
    def next(self) -> List[ExecutableNode]:
        """Get the next set of nodes ready for execution.
        
        This is an alias for get_ready_nodes() to provide a more
        intuitive interface for iterative execution.
        
        Returns:
            List of nodes ready for execution
        """
        return self.get_ready_nodes()
    
    def advance(self, node_id: NodeID, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark a node as completed and store its result.
        
        This advances the execution by marking a node complete, which may
        make downstream nodes ready for execution.
        
        Args:
            node_id: The ID of the node that completed
            result: Optional execution result to store
        """
        # Update node state to completed
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.COMPLETED
            self._context.set_node_state(node_id, state)
        
        # Store result if provided
        if result is not None:
            self._context.set_node_result(node_id, result)
        
        # Add to completed nodes list
        completed = self._context.get_completed_nodes()
        if node_id not in completed:
            # The context should handle this internally, but we ensure it's tracked
            pass
    
    def mark_node_running(self, node_id: NodeID) -> None:
        """Mark a node as currently running.
        
        Args:
            node_id: The ID of the node to mark as running
        """
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.RUNNING
            self._context.set_node_state(node_id, state)
            self._context.set_current_node(node_id)
    
    def mark_node_failed(self, node_id: NodeID, error: Optional[Exception] = None) -> None:
        """Mark a node as failed.
        
        Args:
            node_id: The ID of the node that failed
            error: Optional exception that caused the failure
        """
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.FAILED
            if error:
                state.error = str(error)
            self._context.set_node_state(node_id, state)
    
    def is_complete(self) -> bool:
        """Check if the entire diagram execution is complete.
        
        The diagram is complete when all reachable nodes have been executed
        or when all end nodes have been reached.
        
        Returns:
            True if execution is complete, False otherwise
        """
        # Check if all end nodes are complete
        end_nodes = self._diagram.get_end_nodes()
        if end_nodes:
            all_ends_complete = all(
                self._context.is_node_complete(node.id) 
                for node in end_nodes
            )
            if all_ends_complete:
                return True
        
        # Check if there are any pending or running nodes
        for node in self._diagram.nodes:
            state = self._context.get_node_state(node.id)
            if state and state.status in (NodeExecutionStatus.PENDING, NodeExecutionStatus.RUNNING):
                # Check if this node is reachable
                if self._is_node_reachable(node):
                    return False
        
        return True
    
    def get_execution_path(self) -> List[NodeID]:
        """Get the execution path taken so far.
        
        Returns:
            List of node IDs in the order they were executed
        """
        # Get completed nodes and sort by completion order
        # This assumes the context tracks execution order
        return self._context.get_completed_nodes()
    
    def _is_node_ready(self, node: ExecutableNode) -> bool:
        """Check if a node is ready for execution.
        
        Args:
            node: The node to check
            
        Returns:
            True if the node is ready, False otherwise
        """
        # Check node state
        state = self._context.get_node_state(node.id)
        if not state or state.status != NodeExecutionStatus.PENDING:
            return False
        
        # Start nodes are always ready if pending
        if node.type == NodeType.start:
            return True
        
        # Check all dependencies
        incoming_edges = self._diagram.get_incoming_edges(node.id)
        if not incoming_edges:
            # No dependencies, ready to execute
            return True
        
        # Check each dependency
        for edge in incoming_edges:
            source_node = self._diagram.get_node(edge.source_node_id)
            if not source_node:
                continue
            
            # Check if dependency is complete
            if not self._context.is_node_complete(edge.source_node_id):
                return False
            
            # Handle conditional dependencies
            if source_node.type == NodeType.condition:
                # Check if this edge was the chosen branch
                if not self._is_conditional_edge_active(edge, source_node):
                    # This path wasn't taken, so this node isn't reachable
                    return False
        
        return True
    
    def _is_node_reachable(self, node: ExecutableNode) -> bool:
        """Check if a node is reachable given the current execution state.
        
        A node is reachable if there's a path from a completed or running node
        to this node, considering conditional branches.
        
        Args:
            node: The node to check
            
        Returns:
            True if the node is reachable, False otherwise
        """
        # Start nodes are always reachable
        if node.type == NodeType.start:
            return True
        
        # Use BFS to check reachability from completed/running nodes
        visited: Set[NodeID] = set()
        queue: List[NodeID] = []
        
        # Start from all completed and running nodes
        for check_node in self._diagram.nodes:
            state = self._context.get_node_state(check_node.id)
            if state and state.status in (NodeExecutionStatus.COMPLETED, NodeExecutionStatus.RUNNING):
                queue.append(check_node.id)
        
        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == node.id:
                return True
            
            # Add downstream nodes
            current_node = self._diagram.get_node(current_id)
            if current_node:
                for next_node in self._diagram.get_next_nodes(current_id):
                    # For conditional nodes, only follow active branches
                    if current_node.type == NodeType.condition:
                        edge = next((e for e in self._diagram.get_outgoing_edges(current_id) 
                                   if e.target_node_id == next_node.id), None)
                        if edge and not self._is_conditional_edge_active(edge, current_node):
                            continue
                    
                    if next_node.id not in visited:
                        queue.append(next_node.id)
        
        return False
    
    def _is_conditional_edge_active(self, edge, condition_node: ExecutableNode) -> bool:
        """Check if a conditional edge is the active branch.
        
        Args:
            edge: The edge to check
            condition_node: The condition node
            
        Returns:
            True if this edge is the active branch, False otherwise
        """
        # Get the condition result
        result = self._context.get_node_result(condition_node.id)
        if not result:
            return False
        
        # Check the condition evaluation
        condition_value = result.get("value", False)
        edge_metadata = edge.metadata or {}
        
        # Check if this edge matches the condition result
        # This assumes edges have metadata indicating which branch they represent
        is_true_branch = edge_metadata.get("branch") == "true"
        is_false_branch = edge_metadata.get("branch") == "false"
        
        if is_true_branch and condition_value:
            return True
        if is_false_branch and not condition_value:
            return True
        
        # If no branch metadata, check edge labels or output names
        if edge.source_output:
            if edge.source_output == "true" and condition_value:
                return True
            if edge.source_output == "false" and not condition_value:
                return True
        
        # Default: assume single output means always active
        return True