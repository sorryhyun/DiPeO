# Handle resolution for converting handle references to concrete node IDs.

from dataclasses import dataclass

from dipeo.models import DomainArrow, DomainNode, HandleDirection, HandleLabel, NodeID
from dipeo.models.handle_utils import parse_handle_id_safe


@dataclass
class ResolvedConnection:
    arrow_id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_handle_label: HandleLabel | None = None
    target_handle_label: HandleLabel | None = None


class HandleResolver:
    
    def __init__(self):
        self._errors: list[str] = []
    
    def resolve_arrows(
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> tuple[list[ResolvedConnection], list[str]]:
        self._errors = []
        
        # Create node lookup for validation
        node_ids = {node.id for node in nodes}
        
        # Process each arrow
        resolved = []
        for arrow in arrows:
            connection = self._resolve_arrow(arrow, node_ids)
            if connection:
                resolved.append(connection)
        
        return resolved, self._errors
    
    def _resolve_arrow(
        self, 
        arrow: DomainArrow, 
        valid_nodes: set[NodeID]
    ) -> ResolvedConnection | None:
        # Parse source handle
        source_parsed = parse_handle_id_safe(arrow.source)
        if not source_parsed:
            self._errors.append(
                f"Arrow {arrow.id}: Invalid source handle format: {arrow.source}"
            )
            return None
        
        # Parse target handle
        target_parsed = parse_handle_id_safe(arrow.target)
        if not target_parsed:
            self._errors.append(
                f"Arrow {arrow.id}: Invalid target handle format: {arrow.target}"
            )
            return None
        
        # Validate node references
        if source_parsed.node_id not in valid_nodes:
            self._errors.append(
                f"Arrow {arrow.id}: Source node '{source_parsed.node_id}' not found"
            )
            return None
        
        if target_parsed.node_id not in valid_nodes:
            self._errors.append(
                f"Arrow {arrow.id}: Target node '{target_parsed.node_id}' not found"
            )
            return None
        
        # Validate handle directions
        if source_parsed.direction != HandleDirection.output:
            self._errors.append(
                f"Arrow {arrow.id}: Source must be an output handle, got {source_parsed.direction}"
            )
            return None
        
        if target_parsed.direction != HandleDirection.input:
            self._errors.append(
                f"Arrow {arrow.id}: Target must be an input handle, got {target_parsed.direction}"
            )
            return None
        
        return ResolvedConnection(
            arrow_id=arrow.id,
            source_node_id=source_parsed.node_id,
            target_node_id=target_parsed.node_id,
            source_handle_label=source_parsed.handle_label,
            target_handle_label=target_parsed.handle_label
        )
    
    def build_connection_map(
        self, 
        resolved: list[ResolvedConnection]
    ) -> dict[NodeID, list[ResolvedConnection]]:
        connection_map: dict[NodeID, list[ResolvedConnection]] = {}
        
        for connection in resolved:
            if connection.source_node_id not in connection_map:
                connection_map[connection.source_node_id] = []
            connection_map[connection.source_node_id].append(connection)
        
        return connection_map
    
    def build_reverse_connection_map(
        self, 
        resolved: list[ResolvedConnection]
    ) -> dict[NodeID, list[ResolvedConnection]]:
        reverse_map: dict[NodeID, list[ResolvedConnection]] = {}
        
        for connection in resolved:
            if connection.target_node_id not in reverse_map:
                reverse_map[connection.target_node_id] = []
            reverse_map[connection.target_node_id].append(connection)
        
        return reverse_map
    
    def find_disconnected_nodes(
        self,
        nodes: list[DomainNode],
        resolved: list[ResolvedConnection]
    ) -> set[NodeID]:
        connected_nodes = set()
        
        for connection in resolved:
            connected_nodes.add(connection.source_node_id)
            connected_nodes.add(connection.target_node_id)
        
        all_nodes = {node.id for node in nodes}
        return all_nodes - connected_nodes