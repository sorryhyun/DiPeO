"""Domain logic for resolving handle references to concrete node connections.

This module focuses solely on resolving arrow handle references to node connections.
Validation logic has been moved to the shared validation utilities.
"""

from dataclasses import dataclass

from dipeo.diagram_generated import DomainArrow, DomainNode, HandleLabel, NodeID
from dipeo.domain.diagram.utils import parse_handle_id_safe


@dataclass
class ResolvedConnection:
    """Represents a resolved connection between nodes."""

    arrow_id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_handle_label: HandleLabel | None = None
    target_handle_label: HandleLabel | None = None


class ConnectionResolver:
    """Resolves handle references in arrows to concrete node connections.

    This is pure domain logic that validates and transforms arrow references
    into resolved connections, without any application dependencies.
    """

    def __init__(self):
        self._errors: list[str] = []

    def resolve_connections(
        self, arrows: list[DomainArrow], nodes: list[DomainNode]
    ) -> tuple[list[ResolvedConnection], list[str]]:
        self._errors = []

        node_ids = {node.id for node in nodes}

        resolved = []
        for arrow in arrows:
            connection = self._resolve_arrow(arrow, node_ids)
            if connection:
                resolved.append(connection)

        return resolved, self._errors

    def _resolve_arrow(
        self, arrow: DomainArrow, valid_nodes: set[NodeID]
    ) -> ResolvedConnection | None:
        source_parsed = parse_handle_id_safe(arrow.source)
        target_parsed = parse_handle_id_safe(arrow.target)

        if not source_parsed or not target_parsed:
            self._errors.append(f"Arrow {arrow.id}: Cannot resolve - invalid handle format")
            return None

        if source_parsed.node_id not in valid_nodes or target_parsed.node_id not in valid_nodes:
            self._errors.append(f"Arrow {arrow.id}: Cannot resolve - node not found")
            return None

        return ResolvedConnection(
            arrow_id=arrow.id,
            source_node_id=source_parsed.node_id,
            target_node_id=target_parsed.node_id,
            source_handle_label=source_parsed.handle_label,
            target_handle_label=target_parsed.handle_label,
        )

    def build_connection_maps(
        self, resolved: list[ResolvedConnection]
    ) -> tuple[dict[NodeID, list[ResolvedConnection]], dict[NodeID, list[ResolvedConnection]]]:
        forward_map: dict[NodeID, list[ResolvedConnection]] = {}
        reverse_map: dict[NodeID, list[ResolvedConnection]] = {}

        for connection in resolved:
            if connection.source_node_id not in forward_map:
                forward_map[connection.source_node_id] = []
            forward_map[connection.source_node_id].append(connection)

            if connection.target_node_id not in reverse_map:
                reverse_map[connection.target_node_id] = []
            reverse_map[connection.target_node_id].append(connection)

        return forward_map, reverse_map

    def find_disconnected_nodes(
        self, nodes: list[DomainNode], resolved: list[ResolvedConnection]
    ) -> set[NodeID]:
        connected_nodes = set()

        for connection in resolved:
            connected_nodes.add(connection.source_node_id)
            connected_nodes.add(connection.target_node_id)

        all_nodes = {node.id for node in nodes}
        return all_nodes - connected_nodes
