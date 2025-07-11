# Lightweight shared utilities for diagram converters

from __future__ import annotations

from typing import Any, Mapping, Sequence, TYPE_CHECKING
from dipeo.models import (DataType, HandleLabel, HandleDirection, NodeType,
                          create_handle_id, NodeID)


if TYPE_CHECKING:
    from .conversion_utils import BackendDiagram

__all__ = (
    "HandleGenerator",
    "PositionCalculator",
    "ArrowBuilder",
    "coerce_to_dict",
    "build_node",
    "ensure_position",
    "extract_common_arrows",
)

# Internal helpers


def _create_handle_id(node_id: str, label: str, direction: str) -> str:
    return str(create_handle_id(NodeID(node_id), HandleLabel(label), HandleDirection(direction)))


def _push_handle(
    container: dict[str, Any] | Any, handle: dict[str, Any]
) -> None:
    if isinstance(container, dict):
        handles = container.get('handles', [])
        if isinstance(handles, dict):
            handles[handle['id']] = handle
        else:
            handles.append(handle)
            container['handles'] = handles
    elif hasattr(container, 'handles'):
        if isinstance(container.handles, dict):
            container.handles[handle['id']] = handle
        else:
            container.handles.append(handle)


def _make_handle(
    node_id: str,
    label: str,
    direction: str,
    dtype: str = DataType.any,
) -> dict[str, Any]:
    hid = _create_handle_id(node_id, label, direction)
    return {
        'id': hid,
        'node_id': node_id,
        'label': label,
        'direction': direction,
        'data_type': dtype,
        'position': "left" if direction == HandleDirection.input else "right",
    }


# Public API


class HandleGenerator:

    def generate_for_node(
        self,
        diagram: dict[str, Any] | Any,
        node_id: str,
        node_type: str,
    ) -> None:
        if node_type == NodeType.start:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.output),
            )
            return
            
        if node_type == NodeType.endpoint.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.input),
            )
            return
            
        # Condition nodes have one input and two outputs (true/false)
        if node_type == NodeType.condition.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.input),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.condtrue, HandleDirection.output, DataType.boolean),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.condfalse, HandleDirection.output, DataType.boolean),
            )
            return
            
        # Database nodes have input and output
        if node_type == NodeType.db.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.input),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.output),
            )
            return

        # person_job nodes have specific handles: first input, default input, default output
        if node_type == NodeType.person_job.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.first, HandleDirection.input),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.input),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.output),
            )
            return
            
        # person_batch_job nodes have default input and output
        if node_type == NodeType.person_batch_job.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.input),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.output),
            )
            return
            
        # user_response nodes have default input and output
        if node_type == NodeType.user_response.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.input),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.default, HandleDirection.output),
            )
            return

        _push_handle(
            diagram,
            _make_handle(node_id, HandleLabel.default, HandleDirection.input),
        )
        _push_handle(
            diagram,
            _make_handle(node_id, HandleLabel.default, HandleDirection.output),
        )


class PositionCalculator:

    def __init__(
        self,
        columns: int = 4,
        x_spacing: int = 250,
        y_spacing: int = 150,
        x_offset: int = 100,
        y_offset: int = 100,
    ):
        self.columns, self.x_spacing, self.y_spacing = columns, x_spacing, y_spacing
        self.x_offset, self.y_offset = x_offset, y_offset

    def calculate_grid_position(self, index: int) -> dict[str, float]:
        row, col = divmod(index, self.columns)
        return {
            'x': self.x_offset + col * self.x_spacing,
            'y': self.y_offset + row * self.y_spacing,
        }

    def calculate_vertical_position(self, index: int, x: int = 300) -> dict[str, float]:
        return {'x': x, 'y': self.y_offset + index * self.y_spacing}

    def calculate_horizontal_position(self, index: int, y: int = 300) -> dict[str, float]:
        return {
            'x': self.x_offset + index * self.x_spacing,
            'y': y,
        }


class ArrowBuilder:

    @staticmethod
    def create_arrow_id(source_handle: str, target_handle: str) -> str:  # noqa: D401
        return f"{source_handle}->{target_handle}"

    @staticmethod
    def create_simple_arrow(
        source_node: str,
        target_node: str,
        source_label: HandleLabel = HandleLabel.default,
        target_label: HandleLabel = HandleLabel.default,
    ) -> tuple[str, str, str]:
        s = str(create_handle_id(NodeID(source_node), source_label, HandleDirection.output))
        t = str(create_handle_id(NodeID(target_node), target_label, HandleDirection.input))
        return ArrowBuilder.create_arrow_id(s, t), s, t


# Misc helpers


def coerce_to_dict(
    seq_or_map: Mapping[str, Any] | Sequence[Any] | None,
    id_key: str = "id",
    prefix: str = "obj",
) -> dict[str, Any]:
    if isinstance(seq_or_map, dict):
        return dict(seq_or_map)
    if isinstance(seq_or_map, (list, tuple)):
        return {
            (
                item.get(id_key)
                if isinstance(item, dict) and id_key in item
                else f"{prefix}_{i}"
            ): item
            for i, item in enumerate(seq_or_map)
        }
    return {}


def build_node(
    id: str, type_: str, pos: dict[str, float] | None = None, **data
) -> dict[str, Any]:
    return {"id": id, "type": type_, "position": pos or {}, **data}


def ensure_position(
    node_dict: dict[str, Any],
    index: int,
    position_calculator: PositionCalculator | None = None,
) -> None:
    if not node_dict.get("position"):
        calc = position_calculator or PositionCalculator()
        vec = calc.calculate_grid_position(index)
        node_dict["position"] = {"x": vec.x, "y": vec.y}


def extract_common_arrows(arrows: Any) -> list[dict[str, Any]]:
    if not arrows:
        return []

    pairs = (
        arrows.items()
        if isinstance(arrows, dict)
        else ((d.get("id"), d) for d in arrows if isinstance(d, dict))
    )
    result = []
    for aid, a in pairs:
        if aid and a.get("source") and a.get("target"):
            arrow_dict = {
                "id": aid,
                "source": a.get("source"),
                "target": a.get("target"),
                "data": a.get("data"),
            }
            if "content_type" in a:
                arrow_dict["content_type"] = a["content_type"]
            if "label" in a:
                arrow_dict["label"] = a["label"]
            result.append(arrow_dict)
    return result
