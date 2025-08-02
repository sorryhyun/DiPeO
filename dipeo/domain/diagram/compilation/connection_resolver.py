"""Domain logic for resolving handle references to concrete node connections."""

from dataclasses import dataclass

from dipeo.diagram_generated import DomainArrow, DomainNode, HandleDirection, HandleLabel, NodeID
from dipeo.diagram_generated.handle_utils import parse_handle_id_safe


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
        self, 
        arrows: list[DomainArrow], 
        nodes: list[DomainNode]
    ) -> tuple[list[ResolvedConnection], list[str]]:
        """Resolve all arrow handle references to node connections."""
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
        """Resolve a single arrow to a connection."""
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
        if source_parsed.direction != HandleDirection.OUTPUT:
            self._errors.append(
                f"Arrow {arrow.id}: Source must be an output handle, got {source_parsed.direction}"
            )
            return None
        
        if target_parsed.direction != HandleDirection.INPUT:
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
    
    def build_connection_maps(
        self, 
        resolved: list[ResolvedConnection]
    ) -> tuple[dict[NodeID, list[ResolvedConnection]], dict[NodeID, list[ResolvedConnection]]]:
        """Build forward and reverse connection maps for efficient lookup."""
        # Forward map: source_node -> connections
        forward_map: dict[NodeID, list[ResolvedConnection]] = {}
        # Reverse map: target_node -> connections
        reverse_map: dict[NodeID, list[ResolvedConnection]] = {}
        
        for connection in resolved:
            # Forward map
            if connection.source_node_id not in forward_map:
                forward_map[connection.source_node_id] = []
            forward_map[connection.source_node_id].append(connection)
            
            # Reverse map
            if connection.target_node_id not in reverse_map:
                reverse_map[connection.target_node_id] = []
            reverse_map[connection.target_node_id].append(connection)
        
        return forward_map, reverse_map
    
    def find_disconnected_nodes(
        self,
        nodes: list[DomainNode],
        resolved: list[ResolvedConnection]
    ) -> set[NodeID]:
        """Find nodes that have no connections."""
        connected_nodes = set()
        
        for connection in resolved:
            connected_nodes.add(connection.source_node_id)
            connected_nodes.add(connection.target_node_id)
        
        all_nodes = {node.id for node in nodes}
        return all_nodes - connected_nodes