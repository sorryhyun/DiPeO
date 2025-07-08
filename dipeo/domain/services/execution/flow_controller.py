"""Execution flow control logic."""

from typing import List, Dict, Any, Optional, Set
import logging

from dipeo.models import DomainDiagram, NodeType, DomainNode
from dipeo.models import parse_handle_id, extract_node_id_from_handle

log = logging.getLogger(__name__)


class ExecutionFlowController:
    """Controls the flow of execution through a diagram."""
    
    def get_ready_nodes(
        self,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> List[DomainNode]:
        """Get all nodes that are ready to execute.
        
        A node is ready if all its dependencies are satisfied.
        """
        ready_nodes = []
        
        for node in diagram.nodes:
            if self.is_node_ready(node, diagram, executed_nodes, node_outputs, node_exec_counts):
                ready_nodes.append(node)
        
        return ready_nodes
    
    def is_node_ready(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Check if a specific node is ready to execute."""
        # Start nodes are always ready
        if node.type == NodeType.start:
            return True
        
        # Get dependencies
        dependencies = self.get_node_dependencies(node, diagram, node_exec_counts)
        
        # Check if all dependencies have been executed
        for dep_id in dependencies:
            if dep_id not in executed_nodes:
                return False
        
        return True
    
    def get_node_dependencies(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        """Get all nodes that this node depends on."""
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
        """Get the next nodes to execute after a given node."""
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