"""Domain logic for building executable edges from arrows."""

from dataclasses import dataclass
from typing import Any

from dipeo.core.compilation.executable_diagram import ExecutableEdgeV2
from dipeo.diagram_generated import ContentType, DomainArrow, DomainNode, NodeID, NodeType


@dataclass
class TransformationMetadata:
    """Metadata describing how data should be transformed between nodes."""
    content_type: ContentType
    transformation_rules: dict[str, Any] = None
    
    def __post_init__(self):
        if self.transformation_rules is None:
            self.transformation_rules = {}


@dataclass
class ResolvedConnection:
    """Represents a resolved connection between nodes."""
    arrow_id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_handle_label: str | None = None
    target_handle_label: str | None = None


class EdgeBuilder:
    """Builds executable edges from domain arrows with transformation rules.
    
    This is pure domain logic that transforms arrows into executable edges
    with data flow rules, without any application dependencies.
    """
    
    def __init__(self):
        self._errors: list[str] = []
    
    def build_edges(
        self,
        arrows: list[DomainArrow],
        resolved_connections: list[ResolvedConnection],
        nodes: dict[NodeID, DomainNode]
    ) -> tuple[list[ExecutableEdgeV2], list[str]]:
        """Build executable edges from arrows and resolved connections."""
        self._errors = []
        
        # Create arrow lookup
        arrow_map = {arrow.id: arrow for arrow in arrows}
        
        # Transform each resolved connection
        edges = []
        for connection in resolved_connections:
            arrow = arrow_map.get(connection.arrow_id)
            if not arrow:
                self._errors.append(f"Arrow {connection.arrow_id} not found")
                continue
            
            edge = self._build_edge(connection, arrow, nodes)
            if edge:
                edges.append(edge)
        
        return edges, self._errors
    
    def _build_edge(
        self,
        connection: ResolvedConnection,
        arrow: DomainArrow,
        nodes: dict[NodeID, DomainNode]
    ) -> ExecutableEdgeV2 | None:
        """Build a single executable edge from a connection."""
        # Get source and target nodes
        source_node = nodes.get(connection.source_node_id)
        target_node = nodes.get(connection.target_node_id)
        
        if not source_node or not target_node:
            self._errors.append(
                f"Missing nodes for arrow {arrow.id}: "
                f"source={connection.source_node_id}, target={connection.target_node_id}"
            )
            return None
        
        # Determine data transformation rules
        transform_metadata = self._create_transformation_metadata(
            source_node, 
            target_node, 
            arrow,
            connection
        )
        
        # Create the executable edge
        edge_metadata = {
            "arrow_data": arrow.data or {},
            "source_type": source_node.type.value,
            "target_type": target_node.type.value,
            "label": getattr(arrow, 'label', None)
        }
        
        # Get handle label values - handle both enum and string cases
        source_output = None
        if connection.source_handle_label:
            # If it's an enum, get its value; otherwise use it as string
            source_output = (connection.source_handle_label.value 
                           if hasattr(connection.source_handle_label, 'value') 
                           else str(connection.source_handle_label))
        
        # Arrow label can override the source_output (for labeled connections)
        if arrow.label:
            source_output = arrow.label
        
        target_input = None
        if connection.target_handle_label:
            # If it's an enum, get its value; otherwise use it as string
            target_input = (connection.target_handle_label.value 
                          if hasattr(connection.target_handle_label, 'value') 
                          else str(connection.target_handle_label))
        
        # Arrow label sets the target_input for labeled connections
        # This allows the receiving node to get the input with the label as the key
        if arrow.label:
            target_input = arrow.label
        
        
        return ExecutableEdgeV2(
            id=arrow.id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            source_output=source_output,
            target_input=target_input,
            content_type=transform_metadata.content_type,
            transform_rules=transform_metadata.transformation_rules,
            metadata=edge_metadata
        )
    
    def _create_transformation_metadata(
        self,
        source_node: DomainNode,
        target_node: DomainNode,
        arrow: DomainArrow,
        connection: ResolvedConnection
    ) -> TransformationMetadata:
        """Create transformation metadata for an edge."""
        # Default content type based on source node
        content_type = self._determine_content_type(source_node, arrow)
        
        # Custom transformation rules
        rules = self._extract_transformation_rules(arrow, source_node, target_node)
        
        return TransformationMetadata(
            content_type=content_type,
            transformation_rules=rules
        )
    
    def _determine_content_type(
        self, 
        source_node: DomainNode,
        arrow: DomainArrow
    ) -> ContentType:
        """Determine the content type for data flowing through an edge."""
        # Check for explicit content type in arrow field
        if arrow.content_type:
            return arrow.content_type
        
        # Check for explicit content type in arrow data (legacy)
        if arrow.data and "contentType" in arrow.data:
            try:
                return ContentType(arrow.data["contentType"])
            except ValueError:
                self._errors.append(
                    f"Invalid content type in arrow {arrow.id}: {arrow.data['contentType']}"
                )
        
        # Default based on node type
        if source_node.type == NodeType.PERSON_JOB:
            return ContentType.CONVERSATION_STATE
        elif source_node.type == NodeType.DB:
            # Use object type by default for DB nodes to preserve structure
            return ContentType.OBJECT
        elif source_node.type in [NodeType.CODE_JOB, NodeType.API_JOB]:
            # Code and API jobs typically return structured data
            return ContentType.OBJECT
        else:
            return ContentType.RAW_TEXT
    
    def _extract_transformation_rules(
        self,
        arrow: DomainArrow,
        source_node: DomainNode,
        target_node: DomainNode
    ) -> dict[str, Any]:
        """Extract transformation rules from arrow and node types."""
        rules = {}
        
        # Extract from arrow data
        if arrow.data:
            # Variable extraction rules
            if "extractVariable" in arrow.data:
                rules["extract_variable"] = arrow.data["extractVariable"]
            
            # Format conversion rules
            if "format" in arrow.data:
                rules["format"] = arrow.data["format"]
            
            # Custom transformations
            if "transform" in arrow.data:
                rules["custom_transform"] = arrow.data["transform"]
        
        # Add node-type specific rules
        if source_node.type == NodeType.DB and target_node.type == NodeType.PERSON_JOB:
            # Database to person needs formatting
            rules["format_for_conversation"] = True
        
        return rules