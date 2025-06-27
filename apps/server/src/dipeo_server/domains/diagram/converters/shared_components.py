"""Shared components for diagram format converters."""

import logging
from collections.abc import Callable
from typing import Any, ClassVar

from dipeo_domain import (
    DataType,
    DomainDiagram,
    DomainHandle,
    HandleDirection,
    HandleID,
    NodeID,
    NodeType,
    Vec2,
)

from ..services.models import BackendDiagram

logger = logging.getLogger(__name__)


class HandleGenerator:
    """Generate the default and custom handles for a node."""

    def _push(
        self, diagram: DomainDiagram | BackendDiagram
    ) -> Callable[[str, DomainHandle], None]:
        """Return the correct ‘writer’ for handles (dict vs list)."""
        if isinstance(diagram, BackendDiagram):
            return diagram.handles.__setitem__  # dict-style
        # For list-style, create a wrapper that ignores the key
        def append_handle(key: str, handle: DomainHandle) -> None:
            diagram.handles.append(handle)
        return append_handle

    def generate_for_node(
        self,
        diagram: DomainDiagram | BackendDiagram,
        node_id: str,
        node_type: str,
    ) -> None:
        """Generate all default handles required by `node_type`."""
        push = self._push(diagram)

        # Special handling for database nodes - they use "default" instead of input/output
        if node_type == "db":
            # Input handle
            hid = f"{node_id}:default"
            push(
                hid,
                DomainHandle(
                    id=HandleID(hid),
                    nodeId=NodeID(node_id),
                    label="default",
                    direction=HandleDirection.input,
                    dataType=DataType.any,
                    position="left",
                ),
            )
            # Also create output handle for db nodes
            # Since both use "default", we need to differentiate by position/direction
            # The unified converter will handle creating the proper output handle
            return

        # (suffix, label, direction, dtype, condition)
        table = [
            (
                "input",
                "input",
                HandleDirection.input,
                DataType.any,
                node_type != "start",
            ),
            (
                "output",
                "output",
                HandleDirection.output,
                DataType.any,
                node_type != "endpoint",
            ),
            (
                "true",
                "true",
                HandleDirection.output,
                DataType.boolean,
                node_type == "condition",
            ),
            (
                "false",
                "false",
                HandleDirection.output,
                DataType.boolean,
                node_type == "condition",
            ),
        ]
        for suffix, label, direction, dtype, keep in table:
            if not keep:
                continue
            hid = f"{node_id}:{suffix}"
            push(
                hid,
                DomainHandle(
                    id=HandleID(hid),
                    nodeId=NodeID(node_id),
                    label=label,
                    direction=direction,
                    dataType=dtype,
                    position="left" if direction is HandleDirection.input else "right",
                ),
            )


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
    TYPE_MAPPINGS: ClassVar[dict[str, NodeType]] = {
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
        cls, step_data: dict[str, Any], is_first: bool = False
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


def coerce_to_dict(
    seq_or_map: Any, id_key: str = "id", prefix: str = "obj"
) -> dict[str, Any]:
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


def build_node(id: str, type_: str, pos: dict[str, float], **data) -> dict[str, Any]:
    return {"id": id, "type": type_, "position": pos, **data}


def ensure_position(
    node_dict: dict[str, Any],
    index: int,
    position_calculator: PositionCalculator = None,
) -> None:
    if "position" not in node_dict or not node_dict["position"]:
        if position_calculator is None:
            position_calculator = PositionCalculator()
        vec2_pos = position_calculator.calculate_grid_position(index)
        node_dict["position"] = {"x": vec2_pos.x, "y": vec2_pos.y}


def extract_common_arrows(arrows_data: Any) -> list[dict[str, Any]]:
    """Return [{id, source, target, data}, …] regardless of storage shape."""
    import logging

    logger = logging.getLogger(__name__)

    logger.debug(
        f"extract_common_arrows received: type={type(arrows_data)}, len={len(arrows_data) if hasattr(arrows_data, '__len__') else 'N/A'}"
    )

    if not arrows_data:  # short-circuit None / {} / []
        logger.debug("arrows_data is empty or None")
        return []

    # Turn both mapping and list forms into an iterable of (id, obj) pairs
    items = (
        arrows_data.items()
        if isinstance(arrows_data, dict)
        else ((d.get("id"), d) for d in arrows_data if isinstance(d, dict))
    )

    result = [
        {
            "id": aid,
            "source": ad.get("source"),
            "target": ad.get("target"),
            "data": ad.get(
                "data"
            ),  # Include data field to preserve labels and other properties
        }
        for aid, ad in items
    ]

    logger.debug(f"extract_common_arrows returning {len(result)} arrows")
    for arrow in result:
        if arrow.get("data"):
            logger.debug(f"Arrow {arrow['id']} has data: {arrow['data']}")

    return result
