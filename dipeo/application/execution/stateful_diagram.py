# Stateful wrapper around ExecutableDiagram that maintains execution context

from typing import Any, Dict, List, Optional, Set

from dipeo.core.dynamic.execution_context import ExecutionContext
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.models import NodeExecutionStatus, NodeID, NodeState, NodeType


class StatefulExecutableDiagram:
    
    def __init__(self, diagram: ExecutableDiagram, context: ExecutionContext):
        self._diagram = diagram
        self._context = context
        
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
        return self._diagram
    
    @property
    def context(self) -> ExecutionContext:
        return self._context
    
    def get_ready_nodes(self) -> List[ExecutableNode]:
        ready_nodes = []
        
        for node in self._diagram.nodes:
            if self._is_node_ready(node):
                ready_nodes.append(node)
        
        return ready_nodes
    
    def next(self) -> List[ExecutableNode]:
        return self.get_ready_nodes()
    
    def advance(self, node_id: NodeID, result: Optional[Dict[str, Any]] = None) -> None:
        # Update node state to completed
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.COMPLETED
            self._context.set_node_state(node_id, state)
        
        if result is not None:
            self._context.set_node_result(node_id, result)
        
        completed = self._context.get_completed_nodes()
        if node_id not in completed:
            pass
    
    def mark_node_running(self, node_id: NodeID) -> None:
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.RUNNING
            self._context.set_node_state(node_id, state)
            self._context.set_current_node(node_id)
    
    def mark_node_failed(self, node_id: NodeID, error: Optional[Exception] = None) -> None:
        state = self._context.get_node_state(node_id)
        if state:
            state.status = NodeExecutionStatus.FAILED
            if error:
                state.error = str(error)
            self._context.set_node_state(node_id, state)
    
    def is_complete(self) -> bool:
        import logging
        logger = logging.getLogger(__name__)
        
        end_nodes = self._diagram.get_end_nodes()
        if end_nodes:
            all_ends_complete = all(
                self._context.is_node_complete(node.id) 
                for node in end_nodes
            )
            if all_ends_complete:
                logger.debug("All end nodes are complete, execution is finished")
                return True
        
        has_pending_reachable = False
        for node in self._diagram.nodes:
            state = self._context.get_node_state(node.id)
            if state and state.status in (NodeExecutionStatus.PENDING, NodeExecutionStatus.RUNNING):
                is_reachable = self._is_node_reachable(node)
                logger.debug(f"Node {node.id} status={state.status}, reachable={is_reachable}")
                if is_reachable:
                    has_pending_reachable = True
        
        if has_pending_reachable:
            logger.debug("Found pending/running reachable nodes, execution continues")
            return False
        
        logger.debug("No pending/running reachable nodes found, execution is complete")
        return True
    
    def get_execution_path(self) -> List[NodeID]:
        # Get completed nodes and sort by completion order
        return self._context.get_completed_nodes()
    
    def _is_node_ready(self, node: ExecutableNode) -> bool:
        import logging
        logger = logging.getLogger(__name__)
        
        state = self._context.get_node_state(node.id)
        if not state or state.status != NodeExecutionStatus.PENDING:
            logger.debug(f"Node {node.id} not ready: status={state.status if state else 'None'}")
            return False
        
        if node.type == NodeType.start:
            logger.debug(f"Node {node.id} is start node and pending, marking as ready")
            return True
        
        incoming_edges = self._diagram.get_incoming_edges(node.id)
        if not incoming_edges:
            logger.debug(f"Node {node.id} has no dependencies, marking as ready")
            return True
        
        if node.type == NodeType.person_job:
            exec_count = 0
            completed_nodes = self._context.get_completed_nodes()
            if node.id in completed_nodes:
                exec_count = 1  # For now, assume 1 if in completed list
            
            logger.debug(f"Node {node.id} is person_job, exec_count={exec_count}")
            
            if exec_count == 0:
                first_edges = [e for e in incoming_edges if e.target_input == "first"]
                if first_edges:
                    logger.debug(f"Node {node.id} has {len(first_edges)} first handle dependencies")
                    # Only check first handle dependencies
                    incoming_edges = first_edges
                else:
                    logger.debug(f"Node {node.id} has no first handle, checking all dependencies")
            else:
                non_first_edges = [e for e in incoming_edges if e.target_input != "first"]
                logger.debug(f"Node {node.id} subsequent execution, checking {len(non_first_edges)} non-first dependencies")
                incoming_edges = non_first_edges
        
        dependencies_complete = True
        for edge in incoming_edges:
            source_node = self._diagram.get_node(edge.source_node_id)
            if not source_node:
                continue
            
            dep_complete = self._context.is_node_complete(edge.source_node_id)
            logger.debug(f"Node {node.id} dependency {edge.source_node_id} complete: {dep_complete}, edge.target_input={edge.target_input}")
            if not dep_complete:
                dependencies_complete = False
                break
            
            if source_node.type == NodeType.condition:
                if not self._is_conditional_edge_active(edge, source_node):
                    logger.debug(f"Node {node.id} conditional dependency {edge.source_node_id} branch not active")
                    dependencies_complete = False
                    break
        
        logger.debug(f"Node {node.id} ready: {dependencies_complete}")
        return dependencies_complete
    
    def _is_node_reachable(self, node: ExecutableNode) -> bool:
        # Start nodes are always reachable
        if node.type == NodeType.start:
            return True
        
        visited: Set[NodeID] = set()
        queue: List[NodeID] = []
        
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
            
            current_node = self._diagram.get_node(current_id)
            if current_node:
                for next_node in self._diagram.get_next_nodes(current_id):
                    if current_node.type == NodeType.condition:
                        edge = next((e for e in self._diagram.get_outgoing_edges(current_id) 
                                   if e.target_node_id == next_node.id), None)
                        if edge and not self._is_conditional_edge_active(edge, current_node):
                            continue
                    
                    if next_node.id not in visited:
                        queue.append(next_node.id)
        
        return False
    
    def _is_conditional_edge_active(self, edge, condition_node: ExecutableNode) -> bool:
        # Get the condition result
        result = self._context.get_node_result(condition_node.id)
        if not result:
            return False
        
        condition_value = result.get("value", False)
        edge_metadata = edge.metadata or {}
        
        # Check if this edge matches the condition result
        is_true_branch = edge_metadata.get("branch") == "true"
        is_false_branch = edge_metadata.get("branch") == "false"
        
        if is_true_branch and condition_value:
            return True
        if is_false_branch and not condition_value:
            return True
        
        if edge.source_output:
            if edge.source_output == "true" and condition_value:
                return True
            if edge.source_output == "false" and not condition_value:
                return True
        
        return True