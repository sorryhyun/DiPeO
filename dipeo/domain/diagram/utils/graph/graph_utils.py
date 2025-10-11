# Graph utility functions for diagram traversal and analysis

from typing import Any

from dipeo.diagram_generated import DomainArrow

from ..core.handle_operations import HandleIdOperations


def find_edges_from(
    edges: list[dict[str, Any] | DomainArrow], node_id: str
) -> list[dict[str, Any] | DomainArrow]:
    result = []
    for edge in edges:
        source = edge.get("source") if isinstance(edge, dict) else edge.source
        if source:
            edge_node_id = HandleIdOperations.extract_node_id_from_handle(source)
            if edge_node_id == node_id:
                result.append(edge)
    return result


def find_edges_to(
    edges: list[dict[str, Any] | DomainArrow], node_id: str
) -> list[dict[str, Any] | DomainArrow]:
    result = []
    for edge in edges:
        target = edge.get("target") if isinstance(edge, dict) else edge.target
        if target:
            edge_node_id = HandleIdOperations.extract_node_id_from_handle(target)
            if edge_node_id == node_id:
                result.append(edge)
    return result


def find_connected_nodes(
    edges: list[dict[str, Any] | DomainArrow], node_id: str
) -> dict[str, list[str]]:
    incoming = []
    outgoing = []

    for edge in edges:
        source = edge.get("source") if isinstance(edge, dict) else edge.source
        target = edge.get("target") if isinstance(edge, dict) else edge.target

        if source:
            source_node_id = HandleIdOperations.extract_node_id_from_handle(source)
            if source_node_id == node_id and target:
                target_node_id = HandleIdOperations.extract_node_id_from_handle(target)
                outgoing.append(target_node_id)

        if target:
            target_node_id = HandleIdOperations.extract_node_id_from_handle(target)
            if target_node_id == node_id and source:
                source_node_id = HandleIdOperations.extract_node_id_from_handle(source)
                incoming.append(source_node_id)

    return {"incoming": incoming, "outgoing": outgoing}


def count_node_connections(edges: list[dict[str, Any] | DomainArrow]) -> dict[str, dict[str, int]]:
    connection_counts = {}

    for edge in edges:
        source = edge.get("source") if isinstance(edge, dict) else edge.source
        target = edge.get("target") if isinstance(edge, dict) else edge.target

        if source:
            source_node_id = HandleIdOperations.extract_node_id_from_handle(source)
            if source_node_id not in connection_counts:
                connection_counts[source_node_id] = {"incoming": 0, "outgoing": 0}
            connection_counts[source_node_id]["outgoing"] += 1

        if target:
            target_node_id = HandleIdOperations.extract_node_id_from_handle(target)
            if target_node_id not in connection_counts:
                connection_counts[target_node_id] = {"incoming": 0, "outgoing": 0}
            connection_counts[target_node_id]["incoming"] += 1

    return connection_counts


def find_orphan_nodes(
    nodes: list[dict[str, Any] | Any], edges: list[dict[str, Any] | DomainArrow]
) -> list[str]:
    node_ids = set()
    for node in nodes:
        if isinstance(node, dict):
            node_ids.add(node.get("id"))
        elif hasattr(node, "id"):
            node_ids.add(node.id)

    connection_counts = count_node_connections(edges)

    orphans = []
    for node_id in node_ids:
        if node_id and node_id not in connection_counts:
            orphans.append(node_id)

    return orphans


def is_dag(nodes: list[dict[str, Any] | Any], edges: list[dict[str, Any] | DomainArrow]) -> bool:
    adjacency = {}
    for edge in edges:
        source = edge.get("source") if isinstance(edge, dict) else edge.source
        target = edge.get("target") if isinstance(edge, dict) else edge.target

        if source and target:
            source_node_id = HandleIdOperations.extract_node_id_from_handle(source)
            target_node_id = HandleIdOperations.extract_node_id_from_handle(target)

            if source_node_id not in adjacency:
                adjacency[source_node_id] = []
            adjacency[source_node_id].append(target_node_id)

    visited = set()
    rec_stack = set()

    def has_cycle(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)

        for neighbor in adjacency.get(node_id, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node_id)
        return False

    return all(not (node_id not in visited and has_cycle(node_id)) for node_id in adjacency)
