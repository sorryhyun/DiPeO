"""Unified converter that uses format strategies."""

from typing import Dict, List, Optional, Tuple, Any
import logging

from src.__generated__.models import DomainDiagram, DomainNode, DomainArrow
from .base import DiagramConverter
from .shared_components import (
    HandleGenerator, PositionCalculator, NodeTypeMapper, ArrowBuilder
)
from .strategies import (
    FormatStrategy, NativeJsonStrategy, LightYamlStrategy, ReadableYamlStrategy
)

logger = logging.getLogger(__name__)


class UnifiedDiagramConverter(DiagramConverter):
    """
    Universal converter that uses strategy pattern for different formats.
    This replaces individual converter classes with a single converter
    that switches strategies based on format.
    """
    
    def __init__(self):
        self.strategies: Dict[str, FormatStrategy] = {}
        self.handle_generator = HandleGenerator()
        self.position_calculator = PositionCalculator()
        self.node_mapper = NodeTypeMapper()
        self.arrow_builder = ArrowBuilder()
        
        # Register default strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register built-in format strategies."""
        self.register_strategy(NativeJsonStrategy())
        self.register_strategy(LightYamlStrategy())
        self.register_strategy(ReadableYamlStrategy())
    
    def register_strategy(self, strategy: FormatStrategy):
        """Register a format strategy."""
        self.strategies[strategy.format_id] = strategy
        logger.info(f"Registered format strategy: {strategy.format_id}")
    
    def set_format(self, format_id: str):
        """Set the active format for conversion."""
        if format_id not in self.strategies:
            raise ValueError(f"Unknown format: {format_id}")
        self.active_format = format_id
    
    def get_strategy(self, format_id: Optional[str] = None) -> FormatStrategy:
        """Get strategy for the specified format."""
        fmt = format_id or getattr(self, 'active_format', None)
        if not fmt:
            raise ValueError("No format specified")
        
        strategy = self.strategies.get(fmt)
        if not strategy:
            raise ValueError(f"Unknown format: {fmt}")
        
        return strategy
    
    def serialize(self, diagram: DomainDiagram, format_id: Optional[str] = None) -> str:
        """Convert domain diagram to format-specific string."""
        # Use format_id if provided, otherwise use active format
        fmt = format_id or getattr(self, 'active_format', None)
        if not fmt:
            raise ValueError("No format specified for serialization")
            
        strategy = self.get_strategy(fmt)
        
        # Build export data using strategy
        data = strategy.build_export_data(diagram)
        
        # Format to string
        return strategy.format(data)
    
    def deserialize(self, content: str, format_id: Optional[str] = None) -> DomainDiagram:
        """Convert format-specific string to domain diagram."""
        # Use format_id if provided, otherwise try active format or auto-detect
        fmt = format_id or getattr(self, 'active_format', None)
        
        # Auto-detect format if not specified
        if not fmt:
            fmt = self.detect_format(content)
            if not fmt:
                raise ValueError("Could not detect format automatically")
        
        strategy = self.get_strategy(fmt)
        
        # Parse content
        data = strategy.parse(content)
        
        # Create base diagram
        diagram = DomainDiagram(
            nodes={},
            handles={},
            arrows={},
            persons=data.get('persons', {}),
            api_keys=data.get('api_keys', {})
        )
        
        # Extract and process nodes
        node_data_list = strategy.extract_nodes(data)
        for index, node_data in enumerate(node_data_list):
            node = self._create_node(node_data, index)
            diagram.nodes[node.id] = node
            
            # Generate handles
            self.handle_generator.generate_for_node(diagram, node.id, node.type)
        
        # Extract and process arrows
        arrow_data_list = strategy.extract_arrows(data, node_data_list)
        for arrow_data in arrow_data_list:
            arrow = self._create_arrow(arrow_data)
            if arrow:
                diagram.arrows[arrow.id] = arrow
        
        return diagram
    
    def _create_node(self, node_data: Dict[str, Any], index: int) -> DomainNode:
        """Create a domain node from node data."""
        node_id = node_data.get('id', f'node_{index}')
        node_type = node_data.get('type', 'unknown')
        
        # Extract position
        position = node_data.get('position')
        if not position:
            vec2_pos = self.position_calculator.calculate_grid_position(index)
            position = {"x": vec2_pos.x, "y": vec2_pos.y}
        
        # Extract properties (everything except structural fields)
        exclude_fields = {'id', 'type', 'position', 'handles', 'arrows'}
        properties = {k: v for k, v in node_data.items() if k not in exclude_fields}
        
        return DomainNode(
            id=node_id,
            type=node_type,
            position=position,
            data=properties
        )
    
    def _create_arrow(self, arrow_data: Dict[str, Any]) -> Optional[DomainArrow]:
        """Create a domain arrow from arrow data."""
        source = arrow_data.get('source')
        target = arrow_data.get('target')
        
        if not source or not target:
            return None
        
        arrow_id = arrow_data.get('id', self.arrow_builder.create_arrow_id(source, target))
        
        return DomainArrow(
            id=arrow_id,
            source=source,
            target=target
        )
    
    def validate(self, content: str, format_id: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Validate content without full deserialization."""
        try:
            self.deserialize(content, format_id)
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    def detect_format(self, content: str) -> Optional[str]:
        """Automatically detect format from content."""
        confidences: List[Tuple[str, float]] = []
        
        for format_id, strategy in self.strategies.items():
            try:
                # Try to parse with each strategy
                data = strategy.parse(content)
                confidence = strategy.detect_confidence(data)
                confidences.append((format_id, confidence))
            except:
                confidences.append((format_id, 0.0))
        
        # Sort by confidence
        confidences.sort(key=lambda x: x[1], reverse=True)
        
        # Return format with highest confidence if > 0.5
        if confidences and confidences[0][1] > 0.5:
            return confidences[0][0]
        
        return None
    
    def detect_format_confidence(self, content: str) -> float:
        """Return confidence score for current format."""
        format_id = self.detect_format(content)
        if format_id:
            return 1.0
        return 0.0
    
    def get_supported_formats(self) -> List[Dict[str, str]]:
        """Get information about all supported formats."""
        return [
            {'id': format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
        ]
    
    def get_export_formats(self) -> List[Dict[str, str]]:
        """Get formats that support export."""
        return [
            {'id': format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
            if strategy.format_info.get('supports_export', True)
        ]
    
    def get_import_formats(self) -> List[Dict[str, str]]:
        """Get formats that support import."""
        return [
            {'id': format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
            if strategy.format_info.get('supports_import', True)
        ]