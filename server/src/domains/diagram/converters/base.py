"""Enhanced base converter with shared components to eliminate duplication."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import yaml
import json

from ..models.domain import DomainDiagram, DomainNode, DomainArrow
from .shared_components import (
    HandleGenerator, PositionCalculator, NodeTypeMapper, ArrowBuilder
)


class DiagramConverter(ABC):
    """Abstract base class for diagram converters."""
    
    @abstractmethod
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to format-specific string."""
        pass
    
    @abstractmethod
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert format-specific string to domain diagram."""
        pass
    
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate content without full deserialization.
        Returns (is_valid, list_of_errors)
        """
        try:
            self.deserialize(content)
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    def detect_format_confidence(self, content: str) -> float:
        """
        Return confidence score (0.0-1.0) that content matches this format.
        Used for automatic format detection.
        """
        try:
            self.deserialize(content)
            return 1.0
        except:
            return 0.0


class EnhancedDiagramConverter(DiagramConverter):
    """
    Enhanced base class for diagram converters that provides common functionality
    and uses shared components to eliminate code duplication.
    """
    
    def __init__(self):
        self.handle_generator = HandleGenerator()
        self.position_calculator = PositionCalculator()
        self.node_mapper = NodeTypeMapper()
        self.arrow_builder = ArrowBuilder()
    
    def deserialize(self, content: str) -> DomainDiagram:
        """
        Template method for deserialization with common logic.
        Subclasses only need to implement the abstract methods.
        """
        # Parse content using format-specific parser
        data = self.parse_content(content)
        
        # Create diagram with all required fields
        diagram = DomainDiagram(
            nodes={},
            handles={},
            arrows={},
            persons={},
            api_keys={}
        )
        
        # Extract and process nodes
        node_data_list = self.extract_nodes(data)
        for index, node_data in enumerate(node_data_list):
            node = self.create_node_from_data(node_data, index)
            diagram.nodes[node.id] = node
            
            # Generate handles if not explicitly defined
            if self.should_generate_handles(node_data):
                self.handle_generator.generate_for_node(diagram, node.id, node.type)
        
        # Extract and process arrows
        arrow_data_list = self.extract_arrows(data, diagram)
        for arrow_data in arrow_data_list:
            arrow = self.create_arrow_from_data(arrow_data)
            if arrow:
                diagram.arrows[arrow.id] = arrow
        
        # Post-process diagram if needed
        self.post_process_diagram(diagram, data)
        
        return diagram
    
    def create_node_from_data(self, node_data: Dict[str, Any], index: int) -> DomainNode:
        """Create a domain node from format-specific node data."""
        node_id = self.extract_node_id(node_data, index)
        node_type = self.extract_node_type(node_data)
        position = self.extract_node_position(node_data, index)
        properties = self.extract_node_properties(node_data)
        
        return DomainNode(
            id=node_id,
            type=node_type,
            position=position,
            data=properties
        )
    
    def create_arrow_from_data(self, arrow_data: Dict[str, Any]) -> Optional[DomainArrow]:
        """Create a domain arrow from format-specific arrow data."""
        source_handle = arrow_data.get('source')
        target_handle = arrow_data.get('target')
        
        if not source_handle or not target_handle:
            return None
        
        arrow_id = arrow_data.get('id', self.arrow_builder.create_arrow_id(source_handle, target_handle))
        
        return DomainArrow(
            id=arrow_id,
            source=source_handle,
            target=target_handle
        )
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    def parse_content(self, content: str) -> Any:
        """Parse format-specific content into data structure."""
        pass
    
    @abstractmethod
    def extract_nodes(self, data: Any) -> List[Dict[str, Any]]:
        """Extract node data from parsed content."""
        pass
    
    @abstractmethod
    def extract_arrows(self, data: Any, diagram: DomainDiagram) -> List[Dict[str, Any]]:
        """Extract arrow data from parsed content."""
        pass
    
    # Methods that subclasses can override if needed
    def should_generate_handles(self, node_data: Dict[str, Any]) -> bool:
        """Determine if handles should be auto-generated for this node."""
        return True  # By default, generate handles for all nodes
    
    def extract_node_id(self, node_data: Dict[str, Any], index: int) -> str:
        """Extract or generate node ID."""
        return node_data.get('id', f'node_{index}')
    
    def extract_node_type(self, node_data: Dict[str, Any]) -> str:
        """Extract node type from node data."""
        if 'type' in node_data:
            return node_data['type']
        # Use NodeTypeMapper for intelligent type detection
        node_type = self.node_mapper.determine_node_type(node_data)
        return node_type.value
    
    def extract_node_position(self, node_data: Dict[str, Any], index: int) -> Dict[str, float]:
        """Extract or calculate node position."""
        if 'position' in node_data:
            pos = node_data['position']
            if isinstance(pos, dict):
                return pos
        
        # Use position calculator for default positioning
        vec2_pos = self.position_calculator.calculate_grid_position(index)
        return {"x": vec2_pos.x, "y": vec2_pos.y}
    
    def extract_node_properties(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract node properties/data."""
        # Remove structural fields and keep the rest as properties
        exclude_fields = {'id', 'type', 'position', 'handles', 'arrows'}
        return {k: v for k, v in node_data.items() if k not in exclude_fields}
    
    def post_process_diagram(self, diagram: DomainDiagram, original_data: Any) -> None:
        """Post-process the diagram after nodes and arrows are created."""
        pass  # Subclasses can override if needed
    
    # Serialization template method
    def serialize(self, diagram: DomainDiagram) -> str:
        """
        Template method for serialization with common logic.
        Subclasses only need to implement the abstract methods.
        """
        # Convert diagram to format-specific data structure
        data = self.diagram_to_data(diagram)
        
        # Format the data as string
        return self.format_data(data)
    
    @abstractmethod
    def diagram_to_data(self, diagram: DomainDiagram) -> Any:
        """Convert diagram to format-specific data structure."""
        pass
    
    @abstractmethod
    def format_data(self, data: Any) -> str:
        """Format data structure as string."""
        pass


class YamlBasedConverter(EnhancedDiagramConverter):
    """Base class for YAML-based converters with common YAML functionality."""
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """Parse YAML content."""
        return yaml.safe_load(content) or {}
    
    def format_data(self, data: Any) -> str:
        """Format data as YAML string."""
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def detect_format_confidence(self, content: str) -> float:
        """Enhanced format detection for YAML-based formats."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return 0.0
            
            # Let subclasses define their specific confidence logic
            return self._calculate_format_confidence(data)
        except:
            return 0.0
    
    @abstractmethod
    def _calculate_format_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate format-specific confidence score."""
        pass


class JsonBasedConverter(EnhancedDiagramConverter):
    """Base class for JSON-based converters with common JSON functionality."""
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """Parse JSON content."""
        return json.loads(content)
    
    def format_data(self, data: Any) -> str:
        """Format data as JSON string."""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def detect_format_confidence(self, content: str) -> float:
        """Enhanced format detection for JSON-based formats."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return 0.0
            
            # Let subclasses define their specific confidence logic
            return self._calculate_format_confidence(data)
        except:
            return 0.0
    
    @abstractmethod
    def _calculate_format_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate format-specific confidence score."""
        pass