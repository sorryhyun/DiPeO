"""Graph utility functions for diagram traversal and analysis.

better separation of concerns and make graph operations more explicit.
"""

from typing import Any, List, Union, Dict
from dipeo.models import DomainArrow
from dipeo.models import extract_node_id_from_handle


def find_edges_from(edges: List[Union[Dict[str, Any], DomainArrow]], node_id: str) -> List[Union[Dict[str, Any], DomainArrow]]:
    """Find all edges originating from a specific node.
    
    Args:
        edges: List of edges (can be dicts or DomainArrow objects)
        node_id: The ID of the source node
        
    Returns:
        List of edges that originate from the specified node
    """
    result = []
    for edge in edges:
        # Handle both dict and DomainArrow formats
        source = edge.get('source') if isinstance(edge, dict) else edge.source
        if source:
            edge_node_id = extract_node_id_from_handle(source)
            if edge_node_id == node_id:
                result.append(edge)
    return result


def find_edges_to(edges: List[Union[Dict[str, Any], DomainArrow]], node_id: str) -> List[Union[Dict[str, Any], DomainArrow]]:
    """Find all edges targeting a specific node.
    
    Args:
        edges: List of edges (can be dicts or DomainArrow objects)
        node_id: The ID of the target node
        
    Returns:
        List of edges that target the specified node
    """
    result = []
    for edge in edges:
        # Handle both dict and DomainArrow formats
        target = edge.get('target') if isinstance(edge, dict) else edge.target
        if target:
            edge_node_id = extract_node_id_from_handle(target)
            if edge_node_id == node_id:
                result.append(edge)
    return result


def find_connected_nodes(edges: List[Union[Dict[str, Any], DomainArrow]], node_id: str) -> Dict[str, List[str]]:
    """Find all nodes connected to a specific node.
    
    Args:
        edges: List of edges (can be dicts or DomainArrow objects)
        node_id: The ID of the node to analyze
        
    Returns:
        Dict with 'incoming' and 'outgoing' lists of connected node IDs
    """
    incoming = []
    outgoing = []
    
    for edge in edges:
        # Handle both dict and DomainArrow formats
        source = edge.get('source') if isinstance(edge, dict) else edge.source
        target = edge.get('target') if isinstance(edge, dict) else edge.target
        
        if source:
            source_node_id = extract_node_id_from_handle(source)
            if source_node_id == node_id and target:
                target_node_id = extract_node_id_from_handle(target)
                outgoing.append(target_node_id)
        
        if target:
            target_node_id = extract_node_id_from_handle(target)
            if target_node_id == node_id and source:
                source_node_id = extract_node_id_from_handle(source)
                incoming.append(source_node_id)
    
    return {
        'incoming': incoming,
        'outgoing': outgoing
    }


def count_node_connections(edges: List[Union[Dict[str, Any], DomainArrow]]) -> Dict[str, Dict[str, int]]:
    """Count incoming and outgoing connections for all nodes in the graph.
    
    Args:
        edges: List of edges (can be dicts or DomainArrow objects)
        
    Returns:
        Dict mapping node IDs to their connection counts
    """
    connection_counts = {}
    
    for edge in edges:
        # Handle both dict and DomainArrow formats
        source = edge.get('source') if isinstance(edge, dict) else edge.source
        target = edge.get('target') if isinstance(edge, dict) else edge.target
        
        if source:
            source_node_id = extract_node_id_from_handle(source)
            if source_node_id not in connection_counts:
                connection_counts[source_node_id] = {'incoming': 0, 'outgoing': 0}
            connection_counts[source_node_id]['outgoing'] += 1
        
        if target:
            target_node_id = extract_node_id_from_handle(target)
            if target_node_id not in connection_counts:
                connection_counts[target_node_id] = {'incoming': 0, 'outgoing': 0}
            connection_counts[target_node_id]['incoming'] += 1
    
    return connection_counts


def find_orphan_nodes(nodes: List[Union[Dict[str, Any], Any]], edges: List[Union[Dict[str, Any], DomainArrow]]) -> List[str]:
    """Find nodes that have no connections (neither incoming nor outgoing edges).
    
    Args:
        nodes: List of nodes (can be dicts or domain objects with 'id' attribute)
        edges: List of edges
        
    Returns:
        List of orphan node IDs
    """
    # Get all node IDs
    node_ids = set()
    for node in nodes:
        if isinstance(node, dict):
            node_ids.add(node.get('id'))
        elif hasattr(node, 'id'):
            node_ids.add(node.id)
    
    # Get connection counts
    connection_counts = count_node_connections(edges)
    
    # Find orphans (nodes with no connections)
    orphans = []
    for node_id in node_ids:
        if node_id and node_id not in connection_counts:
            orphans.append(node_id)
    
    return orphans


def is_dag(nodes: List[Union[Dict[str, Any], Any]], edges: List[Union[Dict[str, Any], DomainArrow]]) -> bool:
    """Check if the graph is a Directed Acyclic Graph (DAG).
    
    Uses depth-first search to detect cycles.
    
    Args:
        nodes: List of nodes
        edges: List of edges
        
    Returns:
        True if the graph is a DAG (no cycles), False otherwise
    """
    # Build adjacency list
    adjacency = {}
    for edge in edges:
        source = edge.get('source') if isinstance(edge, dict) else edge.source
        target = edge.get('target') if isinstance(edge, dict) else edge.target
        
        if source and target:
            source_node_id = extract_node_id_from_handle(source)
            target_node_id = extract_node_id_from_handle(target)
            
            if source_node_id not in adjacency:
                adjacency[source_node_id] = []
            adjacency[source_node_id].append(target_node_id)
    
    # Track visited nodes and recursion stack
    visited = set()
    rec_stack = set()
    
    def has_cycle(node_id: str) -> bool:
        """DFS helper to detect cycles."""
        visited.add(node_id)
        rec_stack.add(node_id)
        
        # Check all neighbors
        for neighbor in adjacency.get(node_id, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                # Back edge found - cycle detected
                return True
        
        rec_stack.remove(node_id)
        return False
    
    # Check each unvisited node
    for node_id in adjacency:
        if node_id not in visited:
            if has_cycle(node_id):
                return False
    
    return True