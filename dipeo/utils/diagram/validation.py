"""Pure validation logic for diagrams."""

from typing import List, Dict, Any, Optional, Set
from dipeo.models import DomainDiagram, DomainNode, DomainArrow, NodeType
from dipeo.models import parse_handle_id, extract_node_id_from_handle


class DiagramValidator:
    """Pure functions for diagram validation."""
    
    @staticmethod
    def validate_diagram_structure(diagram: DomainDiagram) -> List[str]:
        """Validate the structural integrity of a diagram.
        
        Returns list of validation errors.
        """
        errors = []
        
        # Validate node IDs are unique
        node_ids = [node.id for node in diagram.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Duplicate node IDs found in diagram")
        
        # Validate arrow connections
        node_id_set = set(node_ids)
        for arrow in diagram.arrows:
            source_node_id = extract_node_id_from_handle(arrow.source)
            target_node_id = extract_node_id_from_handle(arrow.target)
            
            if source_node_id not in node_id_set:
                errors.append(f"Arrow {arrow.id} references non-existent source node {source_node_id}")
            if target_node_id not in node_id_set:
                errors.append(f"Arrow {arrow.id} references non-existent target node {target_node_id}")
        
        # Validate start and endpoint nodes
        start_nodes = [n for n in diagram.nodes if n.type == NodeType.start]
        endpoint_nodes = [n for n in diagram.nodes if n.type == NodeType.endpoint]
        
        if not start_nodes:
            errors.append("Diagram must have at least one start node")
        if not endpoint_nodes:
            errors.append("Diagram must have at least one endpoint node")
        
        return errors
    
    @staticmethod
    def validate_node_connections(node: DomainNode, diagram: DomainDiagram) -> List[str]:
        """Validate connections for a specific node."""
        errors = []
        
        # Get incoming and outgoing arrows
        incoming = []
        outgoing = []
        
        for arrow in diagram.arrows:
            if extract_node_id_from_handle(arrow.target) == node.id:
                incoming.append(arrow)
            if extract_node_id_from_handle(arrow.source) == node.id:
                outgoing.append(arrow)
        
        # Validate based on node type
        if node.type == NodeType.start and incoming:
            errors.append(f"Start node {node.id} should not have incoming connections")
        
        if node.type == NodeType.endpoint and outgoing:
            errors.append(f"Endpoint node {node.id} should not have outgoing connections")
        
        if node.type == NodeType.condition:
            # Condition nodes should have true/false branches
            handles = [parse_handle_id(arrow.source)[1] for arrow in outgoing]
            if "condtrue" not in [h.value for h in handles if h]:
                errors.append(f"Condition node {node.id} missing true branch")
            if "condfalse" not in [h.value for h in handles if h]:
                errors.append(f"Condition node {node.id} missing false branch")
        
        return errors
    
    @staticmethod
    def find_unreachable_nodes(diagram: DomainDiagram) -> Set[str]:
        """Find nodes that cannot be reached from any start node."""
        # Build adjacency list
        graph = {}
        for node in diagram.nodes:
            graph[node.id] = []
        
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            if source_id in graph:
                graph[source_id].append(target_id)
        
        # Find all nodes reachable from start nodes
        start_nodes = [n.id for n in diagram.nodes if n.type == NodeType.start]
        reachable = set()
        
        def dfs(node_id: str):
            if node_id in reachable:
                return
            reachable.add(node_id)
            for neighbor in graph.get(node_id, []):
                dfs(neighbor)
        
        for start_id in start_nodes:
            dfs(start_id)
        
        # Find unreachable nodes
        all_nodes = set(n.id for n in diagram.nodes)
        return all_nodes - reachable