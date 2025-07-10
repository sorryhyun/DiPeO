"""Handle resolution for converting handle references to concrete node IDs."""

from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass

from dipeo.models import (
    DomainArrow, 
    DomainNode, 
    NodeID, 
    HandleID,
    HandleDirection,
    HandleLabel
)
from dipeo.models.handle_utils import parse_handle_id_safe, ParsedHandle


@dataclass
class ResolvedConnection:
    """A connection with handles resolved to node IDs."""
    arrow_id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_handle_label: Optional[HandleLabel] = None
    target_handle_label: Optional[HandleLabel] = None


class HandleResolver:
    """Resolves handle references in arrows to concrete node IDs.
    
    This class transforms DomainArrows which use handle IDs into resolved
    connections with direct node ID references. It validates that all
    handle references exist and point to valid nodes.
    """
    
    def __init__(self):
        """Initialize the HandleResolver."""
        self._errors: List[str] = []
    
    def resolve_arrows(
        self, 
        arrows: List[DomainArrow], 
        nodes: List[DomainNode]
    ) -> Tuple[List[ResolvedConnection], List[str]]:
        """Resolve all arrows to node connections.
        
        Args:
            arrows: List of domain arrows with handle references
            nodes: List of nodes in the diagram
            
        Returns:
            Tuple of (resolved connections, validation errors)
        """
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
        valid_nodes: Set[NodeID]
    ) -> Optional[ResolvedConnection]:
        """Resolve a single arrow to a connection.
        
        Args:
            arrow: The arrow to resolve
            valid_nodes: Set of valid node IDs for validation
            
        Returns:
            Resolved connection or None if invalid
        """
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
        resolved: List[ResolvedConnection]
    ) -> Dict[NodeID, List[ResolvedConnection]]:
        """Build a map of node IDs to their outgoing connections.
        
        Args:
            resolved: List of resolved connections
            
        Returns:
            Dictionary mapping node IDs to their outgoing connections
        """
        connection_map: Dict[NodeID, List[ResolvedConnection]] = {}
        
        for connection in resolved:
            if connection.source_node_id not in connection_map:
                connection_map[connection.source_node_id] = []
            connection_map[connection.source_node_id].append(connection)
        
        return connection_map
    
    def build_reverse_connection_map(
        self, 
        resolved: List[ResolvedConnection]
    ) -> Dict[NodeID, List[ResolvedConnection]]:
        """Build a map of node IDs to their incoming connections.
        
        Args:
            resolved: List of resolved connections
            
        Returns:
            Dictionary mapping node IDs to their incoming connections
        """
        reverse_map: Dict[NodeID, List[ResolvedConnection]] = {}
        
        for connection in resolved:
            if connection.target_node_id not in reverse_map:
                reverse_map[connection.target_node_id] = []
            reverse_map[connection.target_node_id].append(connection)
        
        return reverse_map
    
    def find_disconnected_nodes(
        self,
        nodes: List[DomainNode],
        resolved: List[ResolvedConnection]
    ) -> Set[NodeID]:
        """Find nodes that have no connections.
        
        Args:
            nodes: List of all nodes
            resolved: List of resolved connections
            
        Returns:
            Set of node IDs that have no connections
        """
        connected_nodes = set()
        
        for connection in resolved:
            connected_nodes.add(connection.source_node_id)
            connected_nodes.add(connection.target_node_id)
        
        all_nodes = {node.id for node in nodes}
        return all_nodes - connected_nodes