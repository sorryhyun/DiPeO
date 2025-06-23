"""Shared components for diagram format converters."""

from typing import Any, ClassVar, Dict, List, Optional, Union

from dipeo_domain import (
    DataType,
    DomainDiagram,
    DomainHandle,
    HandleDirection,
    NodeType,
    Vec2,
)

from dipeo_server.domains.diagram.services.models import BackendDiagram


class HandleGenerator:
    """Generates handles for nodes in a consistent way across all formats."""

    def generate_for_node(
        self,
        diagram: Union[DomainDiagram, BackendDiagram],
        node_id: str,
        node_type: str,
    ) -> None:
        """Generate default handles for a node based on its type."""
        # Input handle (except for start nodes)
        if node_type != "start":
            input_handle_id = f"{node_id}:input"
            handle = DomainHandle(
                id=input_handle_id,
                nodeId=node_id,
                label="input",
                direction=HandleDirection.input,
                dataType=DataType.any,
                position="left",
            )
            if isinstance(diagram, BackendDiagram):
                diagram.handles[input_handle_id] = handle
            else:
                diagram.handles.append(handle)

        # Output handle (except for endpoint nodes)
        if node_type != "endpoint":
            output_handle_id = f"{node_id}:output"
            handle = DomainHandle(
                id=output_handle_id,
                nodeId=node_id,
                label="output",
                direction=HandleDirection.output,
                dataType=DataType.any,
                position="right",
            )
            if isinstance(diagram, BackendDiagram):
                diagram.handles[output_handle_id] = handle
            else:
                diagram.handles.append(handle)

        # Additional handles for condition nodes
        if node_type == "condition":
            true_handle_id = f"{node_id}:true"
            false_handle_id = f"{node_id}:false"

            true_handle = DomainHandle(
                id=true_handle_id,
                nodeId=node_id,
                label="true",
                direction=HandleDirection.output,
                dataType=DataType.boolean,
                position="right",
            )

            false_handle = DomainHandle(
                id=false_handle_id,
                nodeId=node_id,
                label="false",
                direction=HandleDirection.output,
                dataType=DataType.boolean,
                position="right",
            )

            if isinstance(diagram, BackendDiagram):
                diagram.handles[true_handle_id] = true_handle
                diagram.handles[false_handle_id] = false_handle
            else:
                diagram.handles.append(true_handle)
                diagram.handles.append(false_handle)

    def add_custom_handle(
        self,
        diagram: Union[DomainDiagram, BackendDiagram],
        node_id: str,
        handle_id: str,
        label: str,
        direction: HandleDirection,
        data_type: DataType = DataType.any,
        position: Optional[str] = None,
    ) -> None:
        """Add a custom handle to a node."""
        if position is None:
            position = "left" if direction == HandleDirection.input else "right"

        handle = DomainHandle(
            id=handle_id,
            nodeId=node_id,
            label=label,
            direction=direction,
            dataType=data_type,
            position=position,
        )

        if isinstance(diagram, BackendDiagram):
            diagram.handles[handle_id] = handle
        else:
            diagram.handles.append(handle)


class PositionCalculator:
    """Calculates node positions in a consistent way."""

    def __init__(
        self,
        columns: int = 4,
        x_spacing: int = 250,
        y_spacing: int = 150,
        x_offset: int = 100,
        y_offset: int = 100,
    ):
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
            y=self.y_offset + row * self.y_spacing,
        )

    def calculate_vertical_position(self, index: int, x: int = 300) -> Vec2:
        """Calculate node position in a vertical layout."""
        return Vec2(x=x, y=self.y_offset + index * self.y_spacing)

    def calculate_horizontal_position(self, index: int, y: int = 300) -> Vec2:
        """Calculate node position in a horizontal layout."""
        return Vec2(x=self.x_offset + index * self.x_spacing, y=y)


class NodeTypeMapper:
    """Maps various node type representations to standard NodeType enum."""

    # Common mappings across different formats
    TYPE_MAPPINGS: ClassVar[Dict[str, NodeType]] = {
        # Direct mappings
        "start": NodeType.start,
        "person_job": NodeType.person_job,
        "personjob": NodeType.person_job,
        "person": NodeType.person_job,
        "llm": NodeType.person_job,
        "condition": NodeType.condition,
        "if": NodeType.condition,
        "branch": NodeType.condition,
        "endpoint": NodeType.endpoint,
        "end": NodeType.endpoint,
        "finish": NodeType.endpoint,
    }

    @classmethod
    def map_type(cls, type_str: str) -> NodeType:
        """Map a string type to NodeType enum."""
        normalized = type_str
        return cls.TYPE_MAPPINGS.get(normalized, NodeType.job)

    @classmethod
    def determine_node_type(
        cls, step_data: Dict[str, Any], is_first: bool = False
    ) -> NodeType:
        """Determine node type from step data structure."""
        # Check for explicit type field
        if "type" in step_data:
            return cls.map_type(step_data["type"])

        # Infer from step structure
        if is_first and "input" in step_data:
            return NodeType.start
        if "condition" in step_data or "if" in step_data:
            return NodeType.condition
        if "person" in step_data or "llm" in step_data:
            return NodeType.person_job
        if "notion" in step_data:
            return NodeType.notion
        if "end" in step_data or "finish" in step_data:
            return NodeType.endpoint

        # Default to JOB for unknown types
        return NodeType.job


class ArrowBuilder:
    """Builds arrows between nodes with consistent ID generation."""

    @staticmethod
    def create_arrow_id(source_handle: str, target_handle: str) -> str:
        """Create a consistent arrow ID from handles."""
        return f"{source_handle}->{target_handle}"

    @staticmethod
    def create_simple_arrow(
        source_node: str,
        target_node: str,
        source_label: str = "output",
        target_label: str = "input",
    ) -> tuple:
        """Create a simple arrow between two nodes."""
        source_handle = f"{source_node}:{source_label}"
        target_handle = f"{target_node}:{target_label}"
        arrow_id = ArrowBuilder.create_arrow_id(source_handle, target_handle)
        return arrow_id, source_handle, target_handle


def coerce_to_dict(seq_or_map: Any, id_key: str = 'id', prefix: str = 'obj') -> Dict[str, Any]:
    if isinstance(seq_or_map, dict):
        return seq_or_map
    if isinstance(seq_or_map, list):
        result = {}
        for i, item in enumerate(seq_or_map):
            if isinstance(item, dict) and id_key in item:
                item_id = item[id_key]
            else:
                item_id = f"{prefix}_{i}"
            result[item_id] = item
        return result
    return {}


def build_node(id: str, type_: str, pos: Dict[str, float], **data) -> Dict[str, Any]:
    return {
        "id": id,
        "type": type_,
        "position": pos,
        **data
    }


def ensure_position(node_dict: Dict[str, Any], index: int, position_calculator: PositionCalculator = None) -> None:
    if "position" not in node_dict or not node_dict["position"]:
        if position_calculator is None:
            position_calculator = PositionCalculator()
        vec2_pos = position_calculator.calculate_grid_position(index)
        node_dict["position"] = {"x": vec2_pos.x, "y": vec2_pos.y}


def extract_common_arrows(arrows_data: Any) -> List[Dict[str, Any]]:
    arrows = []

    if isinstance(arrows_data, dict):
        for arrow_id, arrow_data in arrows_data.items():
            if isinstance(arrow_data, dict):
                arrows.append({
                    "id": arrow_id,
                    "source": arrow_data.get("source"),
                    "target": arrow_data.get("target"),
                })
    elif isinstance(arrows_data, list):
        for arrow_data in arrows_data:
            if isinstance(arrow_data, dict):
                arrows.append({
                    "id": arrow_data.get("id"),
                    "source": arrow_data.get("source"),
                    "target": arrow_data.get("target"),
                })

    return arrows
