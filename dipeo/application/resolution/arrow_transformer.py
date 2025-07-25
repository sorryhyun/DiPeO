# Arrow transformation for converting domain arrows to executable edges.

from dataclasses import dataclass
from typing import Any

from dipeo.application.resolution.handle_resolver import ResolvedConnection
from dipeo.core.static import ExecutableEdge
from dipeo.models import ContentType, DomainArrow, DomainNode, NodeID, NodeType


@dataclass
class TransformationMetadata:
    content_type: ContentType
    transformation_rules: dict[str, Any] = None
    
    def __post_init__(self):
        if self.transformation_rules is None:
            self.transformation_rules = {}


class ArrowTransformer:
    """Transforms DomainArrows into ExecutableEdges with data flow rules.
    
    This class converts arrows with handle references into executable edges
    with resolved node connections and data transformation metadata.
    """
    
    def __init__(self):
        self._errors: list[str] = []
    
    def transform_arrows(
        self,
        arrows: list[DomainArrow],
        resolved_connections: list[ResolvedConnection],
        nodes: dict[NodeID, DomainNode]
    ) -> tuple[list[ExecutableEdge], list[str]]:
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
            
            edge = self._transform_connection(connection, arrow, nodes)
            if edge:
                edges.append(edge)
        
        return edges, self._errors
    
    def _transform_connection(
        self,
        connection: ResolvedConnection,
        arrow: DomainArrow,
        nodes: dict[NodeID, DomainNode]
    ) -> ExecutableEdge | None:
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
        
        return ExecutableEdge(
            id=arrow.id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            source_output=connection.source_handle_label.value if connection.source_handle_label else None,
            target_input=connection.target_handle_label.value if connection.target_handle_label else None,
            data_transform={
                "content_type": transform_metadata.content_type.value,
                "rules": transform_metadata.transformation_rules
            },
            metadata=edge_metadata
        )
    
    def _create_transformation_metadata(
        self,
        source_node: DomainNode,
        target_node: DomainNode,
        arrow: DomainArrow,
        connection: ResolvedConnection
    ) -> TransformationMetadata:
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
        if source_node.type == NodeType.person_job:
            return ContentType.conversation_state
        elif source_node.type == NodeType.db:
            # Use object type by default for DB nodes to preserve structure
            return ContentType.object
        elif source_node.type in [NodeType.code_job, NodeType.api_job]:
            # Code and API jobs typically return structured data
            return ContentType.object
        else:
            return ContentType.raw_text
    
    def _extract_transformation_rules(
        self,
        arrow: DomainArrow,
        source_node: DomainNode,
        target_node: DomainNode
    ) -> dict[str, Any]:
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
        if source_node.type == NodeType.db and target_node.type == NodeType.person_job:
            # Database to person needs formatting
            rules["format_for_conversation"] = True
        
        return rules

