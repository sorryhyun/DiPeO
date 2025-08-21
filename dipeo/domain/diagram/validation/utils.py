"""Shared validation utilities for diagram compilation and validation."""

from __future__ import annotations

from dipeo.diagram_generated import (
    DomainArrow,
    DomainNode,
    HandleDirection,
    NodeID,
    NodeType,
)
from dipeo.domain.diagram.utils import parse_handle_id_safe


def validate_arrow_handles(arrow: DomainArrow, node_ids: set[NodeID]) -> list[str]:
    """Validate arrow handles and node references.
    
    Args:
        arrow: The arrow to validate
        node_ids: Set of valid node IDs in the diagram
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Parse source handle
    source_parsed = parse_handle_id_safe(arrow.source)
    if not source_parsed:
        errors.append(f"Arrow {arrow.id}: Invalid source handle format: {arrow.source}")
        return errors  # Can't continue without valid parse
    
    # Parse target handle
    target_parsed = parse_handle_id_safe(arrow.target)
    if not target_parsed:
        errors.append(f"Arrow {arrow.id}: Invalid target handle format: {arrow.target}")
        return errors  # Can't continue without valid parse
    
    # Validate node references
    if source_parsed.node_id not in node_ids:
        errors.append(f"Arrow {arrow.id}: Source node '{source_parsed.node_id}' not found")
    
    if target_parsed.node_id not in node_ids:
        errors.append(f"Arrow {arrow.id}: Target node '{target_parsed.node_id}' not found")
    
    # Validate handle directions
    if source_parsed.direction != HandleDirection.OUTPUT:
        errors.append(f"Arrow {arrow.id}: Source must be an output handle, got {source_parsed.direction}")
    
    if target_parsed.direction != HandleDirection.INPUT:
        errors.append(f"Arrow {arrow.id}: Target must be an input handle, got {target_parsed.direction}")
    
    return errors


def validate_node_type_connections(node: DomainNode, incoming_count: int, outgoing_count: int) -> list[str]:
    """Validate connection counts based on node type rules.
    
    Args:
        node: The node to validate
        incoming_count: Number of incoming connections
        outgoing_count: Number of outgoing connections
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # START nodes should not have incoming connections
    if node.type == NodeType.START and incoming_count > 0:
        errors.append(f"Start node '{node.id}' should not have incoming connections")
    
    # ENDPOINT nodes should not have outgoing connections
    if node.type == NodeType.ENDPOINT and outgoing_count > 0:
        errors.append(f"Endpoint node '{node.id}' should not have outgoing connections")
    
    return errors


def validate_condition_node_branches(
    node: DomainNode, 
    outgoing_handles: list[str | None]
) -> list[str]:
    """Validate that condition nodes have appropriate branches.
    
    Args:
        node: The condition node to validate
        outgoing_handles: List of handle values from outgoing connections
        
    Returns:
        List of warning messages (empty if valid)
    """
    warnings = []
    
    if node.type != NodeType.CONDITION:
        return warnings
    
    handle_values = [h for h in outgoing_handles if h]
    
    if "condtrue" not in handle_values:
        warnings.append(f"Condition node '{node.id}' missing true branch")
    
    if "condfalse" not in handle_values:
        warnings.append(f"Condition node '{node.id}' missing false branch")
    
    return warnings


def find_node_dependencies(
    arrows: list[DomainArrow],
    node_ids: set[NodeID]
) -> dict[NodeID, set[NodeID]]:
    """Build a dependency graph from arrows.
    
    Args:
        arrows: List of arrows in the diagram
        node_ids: Set of valid node IDs
        
    Returns:
        Dictionary mapping target_node_id -> set of source_node_ids
    """
    dependencies: dict[NodeID, set[NodeID]] = {}
    
    for arrow in arrows:
        source_parsed = parse_handle_id_safe(arrow.source)
        target_parsed = parse_handle_id_safe(arrow.target)
        
        if not source_parsed or not target_parsed:
            continue
        
        if source_parsed.node_id not in node_ids or target_parsed.node_id not in node_ids:
            continue
        
        if target_parsed.node_id not in dependencies:
            dependencies[target_parsed.node_id] = set()
        
        dependencies[target_parsed.node_id].add(source_parsed.node_id)
    
    return dependencies


def find_unreachable_nodes(
    nodes: list[DomainNode],
    arrows: list[DomainArrow]
) -> set[NodeID]:
    """Find nodes that cannot be reached from any start node.
    
    Args:
        nodes: List of nodes in the diagram
        arrows: List of arrows in the diagram
        
    Returns:
        Set of unreachable node IDs
    """
    # Build adjacency list
    graph: dict[NodeID, list[NodeID]] = {node.id: [] for node in nodes}
    
    for arrow in arrows:
        source_parsed = parse_handle_id_safe(arrow.source)
        target_parsed = parse_handle_id_safe(arrow.target)
        
        if source_parsed and target_parsed:
            if source_parsed.node_id in graph:
                graph[source_parsed.node_id].append(target_parsed.node_id)
    
    # Find all nodes reachable from start nodes
    start_nodes = [n.id for n in nodes if n.type == NodeType.START]
    reachable = set()
    
    def dfs(node_id: NodeID):
        if node_id in reachable:
            return
        reachable.add(node_id)
        for neighbor in graph.get(node_id, []):
            dfs(neighbor)
    
    for start_id in start_nodes:
        dfs(start_id)
    
    # Find unreachable nodes
    all_nodes = set(n.id for n in nodes)
    return all_nodes - reachable