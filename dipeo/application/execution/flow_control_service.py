"""Unified flow control service for execution management.

This service combines the responsibilities of ExecutionFlowService and ExecutionFlowController,
providing a single source of truth for flow control logic.
"""

from typing import List, Dict, Any, Optional, Set
import logging

from dipeo.models import DomainDiagram, NodeType, DomainNode
from dipeo.models import parse_handle_id, extract_node_id_from_handle

log = logging.getLogger(__name__)


class FlowControlService:
    """Unified service for managing execution flow control.
    
    Responsibilities:
    - Determine node readiness (pure business logic)
    - Calculate dependencies
    - Evaluate flow decisions
    - Navigate execution paths
    - Control execution lifecycle
    """
    
    def is_node_ready(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Determine if a node is ready to execute.
        
        A node is ready if:
        - It hasn't exceeded its max iterations
        - All its dependencies are satisfied
        - For nodes that have already executed: they have new inputs
        """
        # Check if node can still execute
        if not self.can_node_execute(node, node_exec_counts):
            log.debug(f"Node {node.id} cannot execute - exceeded max iterations")
            return False
        
        # Check if node has already executed
        exec_count = node_exec_counts.get(node.id, 0) if node_exec_counts else 0
        if exec_count > 0:
            # Check if node has reached its max iterations
            if node.type == NodeType.person_job and node.data:
                max_iter = node.data.get("max_iteration", 1)
                if exec_count >= max_iter:
                    # Node has reached its max iterations
                    log.debug(f"Node {node.id} has reached max iterations: exec_count={exec_count}, max_iter={max_iter}")
                    return False
                
                # For nodes that support multiple iterations and haven't reached max,
                # always allow re-execution if dependencies are satisfied
                # This enables iteration loops to work properly
                log.debug(f"Node {node.id} can iterate: exec_count={exec_count}, max_iter={max_iter}")
        
        # Check dependencies
        deps_satisfied = self._are_dependencies_satisfied(
            node, diagram, executed_nodes, node_outputs, node_exec_counts
        )
        log.debug(f"Node {node.id} deps_satisfied={deps_satisfied}")
        return deps_satisfied
    
    def get_ready_nodes(
        self,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> List[DomainNode]:
        """Get all nodes that are ready to execute."""
        ready_nodes = []
        
        for node in diagram.nodes:
            if self.is_node_ready(node, diagram, executed_nodes, node_outputs, node_exec_counts):
                ready_nodes.append(node)
        
        # Sort ready nodes to ensure deterministic execution order
        # Nodes that other ready nodes depend on should execute first
        return self._order_ready_nodes(ready_nodes, diagram)
    
    def should_execution_continue(
        self,
        ready_nodes: List[DomainNode],
        executed_nodes: Set[str],
        diagram: DomainDiagram,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Determine if execution should continue.
        
        Business rules:
        - Stop if all endpoints have been executed
        - Stop if only unexecutable nodes remain
        - Stop if nodes have reached max iterations
        """
        # Check if all endpoints have been executed
        endpoint_nodes = [
            node for node in diagram.nodes 
            if node.type == NodeType.endpoint
        ]
        
        if endpoint_nodes:
            all_endpoints_executed = all(
                endpoint.id in executed_nodes 
                for endpoint in endpoint_nodes
            )
            if all_endpoints_executed:
                return False
        
        # Check if we have any nodes that can still execute
        if not ready_nodes:
            return False
        
        # Check if nodes have reached their max iterations
        can_execute = False
        for node in ready_nodes:
            if self.can_node_execute(node, node_exec_counts):
                can_execute = True
                break
        
        return can_execute
    
    def can_node_execute(
        self,
        node: DomainNode,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Check if a node can execute based on its max iterations.
        
        Business rules:
        - Nodes without max_iteration can always execute
        - Nodes with max_iteration stop after reaching the limit
        """
        if not node_exec_counts:
            return True
        
        exec_count = node_exec_counts.get(node.id, 0)
        
        # Check max iterations for person_job nodes
        if node.type == NodeType.person_job and node.data:
            max_iter = node.data.get("max_iteration", 1)
            if exec_count >= max_iter:
                return False
        
        # Check max iterations for person_batch_job nodes
        if node.type == NodeType.person_batch_job and node.data:
            max_iter = node.data.get("max_iteration", 1)
            if exec_count >= max_iter:
                return False
        
        return True
    
    def get_node_dependencies(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        """Get all nodes that this node depends on.
        
        Handles special cases like person_job nodes with "first" handles.
        """
        dependency_ids = []
        
        # Find all arrows pointing to this node
        incoming_arrows = []
        for arrow in diagram.arrows:
            target_node_id = extract_node_id_from_handle(arrow.target)
            if target_node_id == node.id:
                incoming_arrows.append(arrow)
        
        # Special handling for person_job nodes
        if node.type == NodeType.person_job and node_exec_counts:
            exec_count = node_exec_counts.get(node.id, 0)
            
            if exec_count > 0:
                # For subsequent executions, only check non-"first" dependencies
                for arrow in incoming_arrows:
                    _, target_handle, _ = parse_handle_id(arrow.target)
                    if target_handle.value != "first":
                        source_node_id = extract_node_id_from_handle(arrow.source)
                        dependency_ids.append(source_node_id)
            else:
                # On first execution, check if node has any "first" handle connections
                first_handle_arrows = [
                    arrow for arrow in incoming_arrows
                    if parse_handle_id(arrow.target)[1].value == "first"
                ]
                
                if first_handle_arrows:
                    # Only check dependencies from first handle arrows
                    for arrow in first_handle_arrows:
                        source_node_id = extract_node_id_from_handle(arrow.source)
                        dependency_ids.append(source_node_id)
                else:
                    # No first handle, use all dependencies
                    for arrow in incoming_arrows:
                        source_node_id = extract_node_id_from_handle(arrow.source)
                        dependency_ids.append(source_node_id)
        else:
            # For all other nodes, check all dependencies
            for arrow in incoming_arrows:
                source_node_id = extract_node_id_from_handle(arrow.source)
                dependency_ids.append(source_node_id)
        
        return dependency_ids
    
    def get_next_nodes(
        self,
        node_id: str,
        diagram: DomainDiagram,
        condition_result: Optional[bool] = None
    ) -> List[str]:
        """Get the next nodes to execute after a given node.
        
        Handles condition branches based on the result.
        """
        next_nodes = []
        
        # Find all arrows from this node
        for arrow in diagram.arrows:
            source_node_id, source_handle, _ = parse_handle_id(arrow.source)
            if source_node_id == node_id:
                target_node_id = extract_node_id_from_handle(arrow.target)
                
                # Handle condition branches
                if condition_result is not None:
                    if source_handle.value == "condtrue" and condition_result:
                        next_nodes.append(target_node_id)
                    elif source_handle.value == "condfalse" and not condition_result:
                        next_nodes.append(target_node_id)
                else:
                    # Non-condition node or condition result unknown
                    next_nodes.append(target_node_id)
        
        return next_nodes
    
    def find_execution_path(
        self,
        diagram: DomainDiagram,
        start_node_id: Optional[str] = None,
        end_node_id: Optional[str] = None
    ) -> List[str]:
        """Find a valid execution path through the diagram."""
        # If no start specified, find a start node
        if not start_node_id:
            start_nodes = [n for n in diagram.nodes if n.type == NodeType.start]
            if not start_nodes:
                return []
            start_node_id = start_nodes[0].id
        
        # If no end specified, find an endpoint
        if not end_node_id:
            end_nodes = [n for n in diagram.nodes if n.type == NodeType.endpoint]
            if not end_nodes:
                return []
            end_node_id = end_nodes[0].id
        
        # Build adjacency list
        graph = {}
        for node in diagram.nodes:
            graph[node.id] = []
        
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            if source_id in graph:
                graph[source_id].append(target_id)
        
        # DFS to find path
        def find_path(current: str, target: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if current == target:
                return path + [current]
            
            visited.add(current)
            
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    result = find_path(neighbor, target, visited.copy(), path + [current])
                    if result:
                        return result
            
            return None
        
        return find_path(start_node_id, end_node_id, set(), []) or []
    
    def _is_node_in_iteration_loop(self, node: DomainNode, diagram: DomainDiagram) -> bool:
        """Check if a node is part of an iteration loop controlled by a condition node.
        
        A node is in an iteration loop if there's a path:
        node -> ... -> condition node -> ... -> node
        """
        # Find all condition nodes in the diagram
        condition_nodes = [n for n in diagram.nodes if n.type == NodeType.condition]
        if not condition_nodes:
            return False
        
        # Check if there's a path from this node through a condition node back to itself
        for condition_node in condition_nodes:
            # Check if there's a path from node to condition
            if self._has_path(node.id, condition_node.id, diagram):
                # Check if there's a path from condition back to node
                # (via condfalse output for detect_max_iterations)
                for arrow in diagram.arrows:
                    source_parts = arrow.source.split('_')
                    if len(source_parts) >= 2 and source_parts[0] == condition_node.id and source_parts[1] == 'condfalse':
                        # This arrow comes from condition's false output
                        target_node_id = extract_node_id_from_handle(arrow.target)
                        if target_node_id == node.id or self._has_path(target_node_id, node.id, diagram):
                            return True
        
        return False
    
    def _has_path(self, from_node_id: str, to_node_id: str, diagram: DomainDiagram) -> bool:
        """Check if there's a path from one node to another."""
        if from_node_id == to_node_id:
            return True
        
        visited = set()
        queue = [from_node_id]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Find all nodes reachable from current
            for arrow in diagram.arrows:
                source_node_id = extract_node_id_from_handle(arrow.source)
                if source_node_id == current:
                    target_node_id = extract_node_id_from_handle(arrow.target)
                    if target_node_id == to_node_id:
                        return True
                    if target_node_id not in visited:
                        queue.append(target_node_id)
        
        return False
    
    def _has_new_inputs_since_last_execution(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        last_exec_count: int
    ) -> bool:
        """Check if a node has received new inputs since its last execution.
        
        For nodes with multiple iterations (like person_job with max_iteration > 1),
        they should only execute again if there's a feedback loop from downstream nodes.
        
        This prevents nodes from executing all their iterations immediately,
        and ensures proper flow through the diagram.
        """
        # For nodes that support multiple iterations, check if there's a feedback path
        # A feedback path exists if:
        # 1. There's a path from this node to another node and back, OR
        # 2. The node has a self-loop
        
        log.debug(f"Checking new inputs for {node.id}, executed_nodes: {executed_nodes}")
        
        # First, check for self-loops
        for arrow in diagram.arrows:
            source_node_id = extract_node_id_from_handle(arrow.source)
            target_node_id = extract_node_id_from_handle(arrow.target)
            if source_node_id == node.id and target_node_id == node.id:
                log.debug(f"Node {node.id} has self-loop")
                return True
        
        # For person_job nodes, check if there's a feedback loop through downstream nodes
        if node.type == NodeType.person_job:
            # Check if any downstream nodes have executed and have paths back to this node
            downstream_nodes = self.get_next_nodes(node.id, diagram)
            log.debug(f"Node {node.id} downstream nodes: {downstream_nodes}")
            
            for downstream_id in downstream_nodes:
                if downstream_id in executed_nodes:
                    # Check if this downstream node has a path back to our node
                    # This would indicate a feedback loop
                    has_path_back = self._has_path_from_to(diagram, downstream_id, node.id)
                    log.debug(f"Path from {downstream_id} to {node.id}: {has_path_back}")
                    if has_path_back:
                        return True
        
        # No feedback loop found - node should not execute again
        log.debug(f"No feedback loop found for {node.id}")
        return False
    
    def _has_path_from_to(self, diagram: DomainDiagram, from_id: str, to_id: str) -> bool:
        """Check if there's a path from one node to another."""
        visited = set()
        
        def dfs(current_id: str) -> bool:
            if current_id == to_id:
                return True
            if current_id in visited:
                return False
            
            visited.add(current_id)
            
            # Find all outgoing arrows from current node
            for arrow in diagram.arrows:
                source_node_id = extract_node_id_from_handle(arrow.source)
                if source_node_id == current_id:
                    target_node_id = extract_node_id_from_handle(arrow.target)
                    if dfs(target_node_id):
                        return True
            
            return False
        
        return dfs(from_id)
    
    def should_skip_arrow(
        self,
        arrow_id: str,
        source_handle: str,
        source_node_type: str,
        target_handle: str,
        target_node_type: str,
        condition_result: Optional[bool] = None,
        node_exec_count: int = 0
    ) -> bool:
        """Determine if an arrow should be skipped during execution."""
        # Skip condition branches based on result
        if source_node_type == NodeType.condition and condition_result is not None:
            if source_handle == "condtrue" and not condition_result:
                return True
            if source_handle == "condfalse" and condition_result:
                return True
        
        # Skip "first" handle for person_job nodes after first execution
        if target_node_type == NodeType.person_job:
            if target_handle == "first" and node_exec_count > 0:
                return True
        
        return False
    
    def _are_dependencies_satisfied(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Check if all node dependencies are satisfied.
        
        Business rules:
        - Start nodes have no dependencies
        - Person job nodes with "first" handle only need inputs on first execution
        - All other nodes need all their dependencies executed
        - Nodes depending on condition outputs need the correct branch
        """
        # Start nodes have no dependencies
        if node.type == NodeType.start:
            return True
        
        # Check condition branch dependencies
        for arrow in diagram.arrows:
            target_node_id = extract_node_id_from_handle(arrow.target)
            if target_node_id == node.id:
                source_node_id, source_handle, _ = parse_handle_id(arrow.source)
                
                # Check if this is from a condition node
                source_node = next((n for n in diagram.nodes if n.id == source_node_id), None)
                if source_node and source_node.type == NodeType.condition:
                    # This node depends on a condition output
                    if source_node_id not in executed_nodes:
                        log.debug(f"Node {node.id} depends on unexecuted condition {source_node_id}")
                        return False
                    
                    # Check if the condition output matches the required branch
                    condition_output = node_outputs.get(source_node_id)
                    if condition_output and hasattr(condition_output, 'value'):
                        # Check if the condition outputted to the correct branch
                        if source_handle.value == "condtrue" and "condtrue" not in condition_output.value:
                            log.debug(f"Node {node.id} requires condtrue but condition outputted false")
                            return False
                        elif source_handle.value == "condfalse" and "condfalse" not in condition_output.value:
                            log.debug(f"Node {node.id} requires condfalse but condition outputted true")
                            return False
        
        # Get dependencies for this node
        dependency_nodes = self.get_node_dependencies(node, diagram, node_exec_counts)
        
        # Check if all dependencies have been executed
        for dep_id in dependency_nodes:
            if dep_id not in executed_nodes:
                return False
        
        return True
    
    def _order_ready_nodes(
        self,
        ready_nodes: List[DomainNode],
        diagram: DomainDiagram
    ) -> List[DomainNode]:
        """Order ready nodes to ensure deterministic execution.
        
        Nodes that provide inputs to other ready nodes should execute first.
        This prevents race conditions where dependent nodes might execute
        before their dependencies when both are ready.
        """
        if len(ready_nodes) <= 1:
            return ready_nodes
        
        # Build a dependency graph among ready nodes
        ready_node_ids = {node.id for node in ready_nodes}
        dependencies = {}  # node_id -> set of ready nodes it depends on
        
        for node in ready_nodes:
            dependencies[node.id] = set()
            
            # Find all arrows pointing to this node from other ready nodes
            for arrow in diagram.arrows:
                target_node_id = extract_node_id_from_handle(arrow.target)
                if target_node_id == node.id:
                    source_node_id = extract_node_id_from_handle(arrow.source)
                    if source_node_id in ready_node_ids:
                        dependencies[node.id].add(source_node_id)
        
        # Topological sort to determine execution order
        ordered = []
        visited = set()
        
        def visit(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            
            # Visit dependencies first
            for dep_id in dependencies.get(node_id, set()):
                visit(dep_id)
            
            # Find the node object
            for node in ready_nodes:
                if node.id == node_id:
                    ordered.append(node)
                    break
        
        # Visit all nodes
        for node in ready_nodes:
            visit(node.id)
        
        return ordered