"""Arrow transformation for converting domain arrows to executable edges."""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from dipeo.models import (
    DomainArrow,
    DomainNode,
    NodeID,
    NodeType,
    ContentType,
    ForgettingMode
)
from dipeo.core.static import ExecutableEdge
from dipeo.application.resolution.handle_resolver import ResolvedConnection


@dataclass
class TransformationMetadata:
    """Metadata for arrow data transformation."""
    content_type: ContentType
    forgetting_mode: Optional[ForgettingMode] = None
    include_in_memory: bool = True
    transformation_rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.transformation_rules is None:
            self.transformation_rules = {}


class ArrowTransformer:
    """Transforms DomainArrows into ExecutableEdges with data flow rules.
    
    This class converts arrows with handle references into executable edges
    with resolved node connections and data transformation metadata.
    """
    
    def __init__(self):
        """Initialize the ArrowTransformer."""
        self._errors: List[str] = []
    
    def transform_arrows(
        self,
        arrows: List[DomainArrow],
        resolved_connections: List[ResolvedConnection],
        nodes: Dict[NodeID, DomainNode]
    ) -> Tuple[List[ExecutableEdge], List[str]]:
        """Transform arrows into executable edges.
        
        Args:
            arrows: Original domain arrows
            resolved_connections: Connections with resolved node IDs
            nodes: Node lookup dictionary
            
        Returns:
            Tuple of (executable edges, transformation errors)
        """
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
        nodes: Dict[NodeID, DomainNode]
    ) -> Optional[ExecutableEdge]:
        """Transform a single connection into an executable edge.
        
        Args:
            connection: Resolved connection with node IDs
            arrow: Original arrow with metadata
            nodes: Node lookup dictionary
            
        Returns:
            Executable edge or None if transformation fails
        """
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
        return ExecutableEdge(
            id=arrow.id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            source_output=connection.source_handle_label.value if connection.source_handle_label else None,
            target_input=connection.target_handle_label.value if connection.target_handle_label else None,
            data_transform={
                "content_type": transform_metadata.content_type.value,
                "forgetting_mode": transform_metadata.forgetting_mode.value if transform_metadata.forgetting_mode else None,
                "include_in_memory": transform_metadata.include_in_memory,
                "rules": transform_metadata.transformation_rules
            },
            metadata={
                "arrow_data": arrow.data or {},
                "source_type": source_node.type.value,
                "target_type": target_node.type.value
            }
        )
    
    def _create_transformation_metadata(
        self,
        source_node: DomainNode,
        target_node: DomainNode,
        arrow: DomainArrow,
        connection: ResolvedConnection
    ) -> TransformationMetadata:
        """Create transformation metadata based on node types and arrow data.
        
        Args:
            source_node: Source node
            target_node: Target node
            arrow: Arrow with potential metadata
            connection: Resolved connection
            
        Returns:
            Transformation metadata for the edge
        """
        # Default content type based on source node
        content_type = self._determine_content_type(source_node, arrow)
        
        # Forgetting mode from arrow data
        forgetting_mode = None
        if arrow.data and "forgettingMode" in arrow.data:
            try:
                forgetting_mode = ForgettingMode(arrow.data["forgettingMode"])
            except ValueError:
                self._errors.append(
                    f"Invalid forgetting mode in arrow {arrow.id}: {arrow.data['forgettingMode']}"
                )
        
        # Include in memory based on node types and settings
        include_in_memory = self._should_include_in_memory(
            source_node, 
            target_node,
            arrow
        )
        
        # Custom transformation rules
        rules = self._extract_transformation_rules(arrow, source_node, target_node)
        
        return TransformationMetadata(
            content_type=content_type,
            forgetting_mode=forgetting_mode,
            include_in_memory=include_in_memory,
            transformation_rules=rules
        )
    
    def _determine_content_type(
        self, 
        source_node: DomainNode,
        arrow: DomainArrow
    ) -> ContentType:
        """Determine content type based on source node and arrow data.
        
        Args:
            source_node: The source node
            arrow: The arrow with potential content type override
            
        Returns:
            The content type for data transformation
        """
        # Check for explicit content type in arrow data
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
        elif source_node.type == NodeType.job:
            return ContentType.raw_text
        elif source_node.type == NodeType.db:
            return ContentType.variable
        else:
            return ContentType.raw_text
    
    def _should_include_in_memory(
        self,
        source_node: DomainNode,
        target_node: DomainNode,
        arrow: DomainArrow
    ) -> bool:
        """Determine if arrow data should be included in conversation memory.
        
        Args:
            source_node: Source node
            target_node: Target node
            arrow: Arrow with potential override
            
        Returns:
            Whether to include in memory
        """
        # Check for explicit override in arrow data
        if arrow.data and "includeInMemory" in arrow.data:
            return bool(arrow.data["includeInMemory"])
        
        # Default rules based on node types
        # Don't include condition outputs or internal job data
        if source_node.type == NodeType.condition:
            return False
        
        # Include person outputs going to other persons
        if (source_node.type == NodeType.person_job and 
            target_node.type == NodeType.person_job):
            return True
        
        # Default to including
        return True
    
    def _extract_transformation_rules(
        self,
        arrow: DomainArrow,
        source_node: DomainNode,
        target_node: DomainNode
    ) -> Dict[str, Any]:
        """Extract custom transformation rules from arrow and nodes.
        
        Args:
            arrow: Arrow with potential rules
            source_node: Source node
            target_node: Target node
            
        Returns:
            Dictionary of transformation rules
        """
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