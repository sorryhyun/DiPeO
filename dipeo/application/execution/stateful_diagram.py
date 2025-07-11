# Stateful wrapper around ExecutableDiagram that maintains execution context.

from typing import Any, Dict, List, Optional, Set

from dipeo.core.dynamic.execution_context import ExecutionContext
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.models import NodeExecutionStatus, NodeID, NodeState, NodeType


class StatefulExecutableDiagram:
    # Stateful wrapper that combines an ExecutableDiagram with ExecutionContext.
    
    def __init__(self, diagram: ExecutableDiagram, context: ExecutionContext):
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
        # Get the underlying ExecutableDiagram.
        return self._diagram
    
    @property
    def context(self) -> ExecutionContext:
        # Get the execution context.
        return self._context
    
    def get_ready_nodes(self) -> List[ExecutableNode]:
        # Get all nodes that are ready to execute based on dependencies.
        ready_nodes = []
        
        for node in self._diagram.nodes:
            if self._is_node_ready(node):
                ready_nodes.append(node)
        
        return ready_nodes
    
    def next(self) -> List[ExecutableNode]:
        # Get the next set of nodes ready for execution.
        return self.get_ready_nodes()
    
    def advance(self, node_id: NodeID, result: Optional[Dict[str, Any]] = None) -> None:
        # Mark a node as completed and store its result.
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
        # Mark a node as currently running.
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.RUNNING
            self._context.set_node_state(node_id, state)
            self._context.set_current_node(node_id)
    
    def mark_node_failed(self, node_id: NodeID, error: Optional[Exception] = None) -> None:
        # Mark a node as failed.
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.FAILED
            if error:
                state.error = str(error)
            self._context.set_node_state(node_id, state)
    
    def is_complete(self) -> bool:
        # Check if the entire diagram execution is complete.
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if all end nodes are complete
        end_nodes = self._diagram.get_end_nodes()
        if end_nodes:
            all_ends_complete = all(
                self._context.is_node_complete(node.id) 
                for node in end_nodes
            )
            if all_ends_complete:
                logger.debug("All end nodes are complete, execution is finished")
                return True
        
        # Check if there are any pending or running nodes that are reachable
        has_pending_reachable = False
        for node in self._diagram.nodes:
            state = self._context.get_node_state(node.id)
            if state and state.status in (NodeExecutionStatus.PENDING, NodeExecutionStatus.RUNNING):
                # Check if this node is reachable
                is_reachable = self._is_node_reachable(node)
                logger.debug(f"Node {node.id} status={state.status}, reachable={is_reachable}")
                if is_reachable:
                    has_pending_reachable = True
        
        # If we have pending reachable nodes, execution is not complete
        if has_pending_reachable:
            logger.debug("Found pending/running reachable nodes, execution continues")
            return False
        
        logger.debug("No pending/running reachable nodes found, execution is complete")
        return True
    
    def get_execution_path(self) -> List[NodeID]:
        # Get the execution path taken so far.
        # Get completed nodes and sort by completion order
        # This assumes the context tracks execution order
        return self._context.get_completed_nodes()
    
    def _is_node_ready(self, node: ExecutableNode) -> bool:
        # Check if a node is ready for execution.
        import logging
        logger = logging.getLogger(__name__)
        
        # Check node state
        state = self._context.get_node_state(node.id)
        if not state or state.status != NodeExecutionStatus.PENDING:
            logger.debug(f"Node {node.id} not ready: status={state.status if state else 'None'}")
            return False
        
        # Start nodes are always ready if pending
        if node.type == NodeType.start:
            logger.debug(f"Node {node.id} is start node and pending, marking as ready")
            return True
        
        # Check all dependencies
        incoming_edges = self._diagram.get_incoming_edges(node.id)
        if not incoming_edges:
            # No dependencies, ready to execute
            logger.debug(f"Node {node.id} has no dependencies, marking as ready")
            return True
        
        # Special handling for person_job nodes with "first" handle
        if node.type == NodeType.person_job:
            # Check execution count
            exec_count = 0
            completed_nodes = self._context.get_completed_nodes()
            # Simple way to check if this node has executed before
            if node.id in completed_nodes:
                exec_count = 1  # For now, assume 1 if in completed list
            
            logger.debug(f"Node {node.id} is person_job, exec_count={exec_count}")
            
            if exec_count == 0:
                # First execution - only check "first" handle dependencies
                first_edges = [e for e in incoming_edges if e.target_input == "first"]
                if first_edges:
                    logger.debug(f"Node {node.id} has {len(first_edges)} first handle dependencies")
                    # Only check first handle dependencies
                    incoming_edges = first_edges
                else:
                    logger.debug(f"Node {node.id} has no first handle, checking all dependencies")
            else:
                # Subsequent executions - only check non-"first" dependencies
                non_first_edges = [e for e in incoming_edges if e.target_input != "first"]
                logger.debug(f"Node {node.id} subsequent execution, checking {len(non_first_edges)} non-first dependencies")
                incoming_edges = non_first_edges
        
        # Check each dependency
        dependencies_complete = True
        for edge in incoming_edges:
            source_node = self._diagram.get_node(edge.source_node_id)
            if not source_node:
                continue
            
            # Check if dependency is complete
            dep_complete = self._context.is_node_complete(edge.source_node_id)
            logger.debug(f"Node {node.id} dependency {edge.source_node_id} complete: {dep_complete}, edge.target_input={edge.target_input}")
            if not dep_complete:
                dependencies_complete = False
                break
            
            # Handle conditional dependencies
            if source_node.type == NodeType.condition:
                # Check if this edge was the chosen branch
                if not self._is_conditional_edge_active(edge, source_node):
                    # This path wasn't taken, so this node isn't reachable
                    logger.debug(f"Node {node.id} conditional dependency {edge.source_node_id} branch not active")
                    dependencies_complete = False
                    break
        
        logger.debug(f"Node {node.id} ready: {dependencies_complete}")
        return dependencies_complete
    
    def _is_node_reachable(self, node: ExecutableNode) -> bool:
        # Check if a node is reachable given the current execution state.
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
        # Check if a conditional edge is the active branch.
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