"""Rich domain entity for Diagram with business behavior."""

from typing import Any, Optional, Set

from dipeo.core import ValidationError
from dipeo.domain.diagram.services import DiagramValidator
from dipeo.domain.models.value_objects import ValidationResult, TransformationResult
from dipeo.models import (
    DomainDiagram,
    DomainNode,
    DomainArrow,
    NodeID,
    DiagramFormat,
    NodeType,
)


class Diagram:
    """Rich domain entity for Diagram with business behavior."""
    
    def __init__(self, domain_diagram: DomainDiagram):
        """Initialize with a domain diagram model."""
        self._data = domain_diagram
        self._validator = DiagramValidator()
    
    @property
    def id(self) -> str:
        """Get diagram ID."""
        return self._data.id or ""
    
    @property
    def nodes(self) -> list[DomainNode]:
        """Get nodes."""
        return self._data.nodes
    
    @property
    def arrows(self) -> list[DomainArrow]:
        """Get arrows."""
        return self._data.arrows
    
    @property
    def metadata(self) -> dict[str, Any]:
        """Get metadata."""
        return self._data.metadata or {}
    
    def validate(self) -> ValidationResult:
        """Validate the diagram structure and connections."""
        return self._validator.validate(self._data)
    
    def validate_or_raise(self) -> None:
        """Validate and raise exception if invalid."""
        result = self.validate()
        if not result.is_valid:
            errors = [e.message for e in result.errors]
            raise ValidationError(f"Diagram validation failed: {'; '.join(errors)}")
    
    def add_node(self, node: DomainNode) -> None:
        """Add a node to the diagram."""
        # Check for duplicate node ID
        if any(n.id == node.id for n in self._data.nodes):
            raise ValidationError(f"Node with ID '{node.id}' already exists")
        
        self._data.nodes.append(node)
    
    def remove_node(self, node_id: NodeID) -> None:
        """Remove a node and its connections."""
        # Remove the node
        self._data.nodes = [n for n in self._data.nodes if n.id != node_id]
        
        # Remove arrows connected to this node
        self._data.arrows = [
            arrow for arrow in self._data.arrows
            if not (self._node_id_from_handle(arrow.source) == node_id or
                   self._node_id_from_handle(arrow.target) == node_id)
        ]
    
    def add_arrow(self, arrow: DomainArrow) -> None:
        """Add an arrow connection."""
        # Validate that source and target nodes exist
        source_node_id = self._node_id_from_handle(arrow.source)
        target_node_id = self._node_id_from_handle(arrow.target)
        
        node_ids = {node.id for node in self._data.nodes}
        if source_node_id not in node_ids:
            raise ValidationError(f"Source node '{source_node_id}' not found")
        if target_node_id not in node_ids:
            raise ValidationError(f"Target node '{target_node_id}' not found")
        
        self._data.arrows.append(arrow)
    
    def get_node_by_id(self, node_id: NodeID) -> Optional[DomainNode]:
        """Get a node by its ID."""
        return next((n for n in self._data.nodes if n.id == node_id), None)
    
    def get_nodes_by_type(self, node_type: NodeType) -> list[DomainNode]:
        """Get all nodes of a specific type."""
        return [n for n in self._data.nodes if n.type == node_type]
    
    def get_start_nodes(self) -> list[DomainNode]:
        """Get all start nodes."""
        return self.get_nodes_by_type(NodeType.start)
    
    def get_endpoint_nodes(self) -> list[DomainNode]:
        """Get all endpoint nodes."""
        return self.get_nodes_by_type(NodeType.endpoint)
    
    def get_connected_nodes(self, node_id: NodeID) -> Set[NodeID]:
        """Get all nodes connected to a given node (incoming and outgoing)."""
        connected = set()
        
        for arrow in self._data.arrows:
            source_node = self._node_id_from_handle(arrow.source)
            target_node = self._node_id_from_handle(arrow.target)
            
            if source_node == node_id:
                connected.add(target_node)
            elif target_node == node_id:
                connected.add(source_node)
        
        return connected
    
    def get_incoming_nodes(self, node_id: NodeID) -> Set[NodeID]:
        """Get nodes with arrows pointing to the given node."""
        incoming = set()
        
        for arrow in self._data.arrows:
            target_node = self._node_id_from_handle(arrow.target)
            if target_node == node_id:
                source_node = self._node_id_from_handle(arrow.source)
                incoming.add(source_node)
        
        return incoming
    
    def get_outgoing_nodes(self, node_id: NodeID) -> Set[NodeID]:
        """Get nodes that the given node points to."""
        outgoing = set()
        
        for arrow in self._data.arrows:
            source_node = self._node_id_from_handle(arrow.source)
            if source_node == node_id:
                target_node = self._node_id_from_handle(arrow.target)
                outgoing.add(target_node)
        
        return outgoing
    
    def has_cycles(self) -> bool:
        """Check if the diagram contains cycles."""
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle_dfs(node_id: NodeID) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in self.get_outgoing_nodes(node_id):
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in self._data.nodes:
            if node.id not in visited:
                if has_cycle_dfs(node.id):
                    return True
        
        return False
    
    def is_connected(self) -> bool:
        """Check if all nodes are reachable from start nodes."""
        start_nodes = self.get_start_nodes()
        if not start_nodes:
            return False
        
        # BFS from all start nodes
        visited = set()
        queue = [node.id for node in start_nodes]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            for neighbor in self.get_outgoing_nodes(node_id):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        # Check if all nodes were visited
        all_node_ids = {node.id for node in self._data.nodes}
        return visited == all_node_ids
    
    def transform_to_format(self, target_format: DiagramFormat) -> 'TransformationResult':
        """Transform diagram to a specific format."""
        from dipeo.domain.diagram.services import DiagramBusinessLogic
        
        business_logic = DiagramBusinessLogic()
        
        try:
            # Convert to dict for transformation
            diagram_dict = self._data.model_dump(exclude_none=True)
            
            # Transform the diagram
            transformed = business_logic.transform_diagram_for_export(
                diagram_dict,
                target_format
            )
            
            return TransformationResult(
                success=True,
                data=transformed,
                format=target_format.value
            )
        except Exception as e:
            return TransformationResult(
                success=False,
                data=None,
                format=target_format.value,
                error=str(e)
            )
    
    def _node_id_from_handle(self, handle_id: str) -> NodeID:
        """Extract node ID from handle ID."""
        # Handle format: {nodeId}_{handleLabel}
        parts = handle_id.rsplit("_", 1)
        return NodeID(parts[0] if len(parts) > 1 else handle_id)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return self._data.model_dump(exclude_none=True)