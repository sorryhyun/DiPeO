"""Shared components for diagram format converters."""
from typing import Dict, Any, Optional
from ..models.domain import DomainDiagram, DomainHandle, Vec2
from src.shared.domain import HandleDirection, DataType, NodeType


class HandleGenerator:
    """Generates handles for nodes in a consistent way across all formats."""
    
    def generate_for_node(self, diagram: DomainDiagram, node_id: str, node_type: str) -> None:
        """Generate default handles for a node based on its type."""
        # Input handle (except for start nodes)
        if node_type != 'start':
            input_handle_id = f"{node_id}:input"
            diagram.handles[input_handle_id] = DomainHandle(
                id=input_handle_id,
                nodeId=node_id,
                label="input",
                direction=HandleDirection.INPUT,
                dataType=DataType.ANY,
                position="left"
            )
        
        # Output handle (except for endpoint nodes)
        if node_type != 'endpoint':
            output_handle_id = f"{node_id}:output"
            diagram.handles[output_handle_id] = DomainHandle(
                id=output_handle_id,
                nodeId=node_id,
                label="output",
                direction=HandleDirection.OUTPUT,
                dataType=DataType.ANY,
                position="right"
            )
        
        # Additional handles for condition nodes
        if node_type == 'condition':
            true_handle_id = f"{node_id}:true"
            false_handle_id = f"{node_id}:false"
            
            diagram.handles[true_handle_id] = DomainHandle(
                id=true_handle_id,
                nodeId=node_id,
                label="true",
                direction=HandleDirection.OUTPUT,
                dataType=DataType.BOOLEAN,
                position="right"
            )
            
            diagram.handles[false_handle_id] = DomainHandle(
                id=false_handle_id,
                nodeId=node_id,
                label="false",
                direction=HandleDirection.OUTPUT,
                dataType=DataType.BOOLEAN,
                position="right"
            )
    
    def add_custom_handle(self, diagram: DomainDiagram, node_id: str, 
                         handle_id: str, label: str, direction: HandleDirection,
                         data_type: DataType = DataType.ANY, position: str = None) -> None:
        """Add a custom handle to a node."""
        if position is None:
            position = "left" if direction == HandleDirection.INPUT else "right"
        
        diagram.handles[handle_id] = DomainHandle(
            id=handle_id,
            nodeId=node_id,
            label=label,
            direction=direction,
            dataType=data_type,
            position=position
        )


class PositionCalculator:
    """Calculates node positions in a consistent way."""
    
    def __init__(self, columns: int = 4, x_spacing: int = 250, y_spacing: int = 150,
                 x_offset: int = 100, y_offset: int = 100):
        self.columns = columns
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing
        self.x_offset = x_offset
        self.y_offset = y_offset
    
    def calculate_grid_position(self, index: int) -> Vec2:
        """Calculate node position based on index using grid layout."""
        row = index // self.columns
        col = index % self.columns
        
        return Vec2(
            x=self.x_offset + col * self.x_spacing,
            y=self.y_offset + row * self.y_spacing
        )
    
    def calculate_vertical_position(self, index: int, x: int = 300) -> Vec2:
        """Calculate node position in a vertical layout."""
        return Vec2(
            x=x,
            y=self.y_offset + index * self.y_spacing
        )
    
    def calculate_horizontal_position(self, index: int, y: int = 300) -> Vec2:
        """Calculate node position in a horizontal layout."""
        return Vec2(
            x=self.x_offset + index * self.x_spacing,
            y=y
        )


class NodeTypeMapper:
    """Maps various node type representations to standard NodeType enum."""
    
    # Common mappings across different formats
    TYPE_MAPPINGS = {
        # Direct mappings
        'start': NodeType.START,
        'person_job': NodeType.PERSON_JOB,
        'personjob': NodeType.PERSON_JOB,
        'person': NodeType.PERSON_JOB,
        'llm': NodeType.PERSON_JOB,
        'condition': NodeType.CONDITION,
        'if': NodeType.CONDITION,
        'branch': NodeType.CONDITION,
        'endpoint': NodeType.ENDPOINT,
        'end': NodeType.ENDPOINT,
        'finish': NodeType.ENDPOINT,
    }
    
    @classmethod
    def map_type(cls, type_str: str) -> NodeType:
        """Map a string type to NodeType enum."""
        normalized = type_str.lower().replace('-', '_').replace(' ', '_')
        return cls.TYPE_MAPPINGS.get(normalized, NodeType.JOB)
    
    @classmethod
    def determine_node_type(cls, step_data: Dict[str, Any], is_first: bool = False) -> NodeType:
        """Determine node type from step data structure."""
        # Check for explicit type field
        if 'type' in step_data:
            return cls.map_type(step_data['type'])
        
        # Infer from step structure
        if is_first and 'input' in step_data:
            return NodeType.START
        elif 'condition' in step_data or 'if' in step_data:
            return NodeType.CONDITION
        elif 'person' in step_data or 'llm' in step_data:
            return NodeType.PERSON_JOB
        elif 'notion' in step_data:
            return NodeType.NOTION
        elif 'end' in step_data or 'finish' in step_data:
            return NodeType.ENDPOINT
        
        # Default to JOB for unknown types
        return NodeType.JOB


class ArrowBuilder:
    """Builds arrows between nodes with consistent ID generation."""
    
    @staticmethod
    def create_arrow_id(source_handle: str, target_handle: str) -> str:
        """Create a consistent arrow ID from handles."""
        return f"{source_handle}->{target_handle}"
    
    @staticmethod
    def create_simple_arrow(source_node: str, target_node: str,
                          source_label: str = "output", target_label: str = "input") -> tuple:
        """Create a simple arrow between two nodes."""
        source_handle = f"{source_node}:{source_label}"
        target_handle = f"{target_node}:{target_label}"
        arrow_id = ArrowBuilder.create_arrow_id(source_handle, target_handle)
        return arrow_id, source_handle, target_handle