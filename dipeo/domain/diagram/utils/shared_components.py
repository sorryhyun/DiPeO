# Lightweight shared utilities for diagram converters

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import DataType, HandleDirection, HandleLabel, NodeID, NodeType

from .handle_utils import create_handle_id

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass

__all__ = (
    "ArrowBuilder",
    "HandleGenerator",
    "PositionCalculator",
    "build_node",
    "coerce_to_dict",
    "ensure_position",
    "extract_common_arrows",
)


def _create_handle_id_from_enums(
    node_id: str, label: HandleLabel, direction: HandleDirection
) -> str:
    result = create_handle_id(NodeID(node_id), label, direction)
    return str(result)


def _push_handle(container: dict[str, Any] | Any, handle: dict[str, Any]) -> None:
    if isinstance(container, dict):
        handles = container.get("handles", [])
        if isinstance(handles, dict):
            handles[handle["id"]] = handle
        else:
            handles.append(handle)
            container["handles"] = handles
    elif hasattr(container, "handles"):
        if isinstance(container.handles, dict):
            container.handles[handle["id"]] = handle
        else:
            container.handles.append(handle)


def _make_handle(
    node_id: str,
    label: HandleLabel,
    direction: HandleDirection,
    dtype: DataType = DataType.ANY,
) -> dict[str, Any]:
    hid = _create_handle_id_from_enums(node_id, label, direction)
    return {
        "id": hid,
        "node_id": node_id,
        "label": label.value,
        "direction": direction.value,
        "data_type": dtype.value,
        "position": "left" if direction == HandleDirection.INPUT else "right",
    }


class HandleGenerator:
    def generate_for_node(
        self,
        diagram: dict[str, Any] | Any,
        node_id: str,
        node_type: str,
    ) -> None:
        if node_type == NodeType.START:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.OUTPUT),
            )
            return

        if node_type == NodeType.ENDPOINT.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.INPUT),
            )
            return

        # Condition nodes: one input, two outputs (true/false)
        if node_type == NodeType.CONDITION.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.INPUT),
            )
            _push_handle(
                diagram,
                _make_handle(
                    node_id, HandleLabel.CONDTRUE, HandleDirection.OUTPUT, DataType.BOOLEAN
                ),
            )
            _push_handle(
                diagram,
                _make_handle(
                    node_id, HandleLabel.CONDFALSE, HandleDirection.OUTPUT, DataType.BOOLEAN
                ),
            )
            return

        if node_type == NodeType.DB.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.INPUT),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.OUTPUT),
            )
            return

        # person_job nodes: first input, default input/output
        if node_type == NodeType.PERSON_JOB.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.FIRST, HandleDirection.INPUT),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.INPUT),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.OUTPUT),
            )
            return

        if node_type == NodeType.USER_RESPONSE.value:
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.INPUT),
            )
            _push_handle(
                diagram,
                _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.OUTPUT),
            )
            return

        _push_handle(
            diagram,
            _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.INPUT),
        )
        _push_handle(
            diagram,
            _make_handle(node_id, HandleLabel.DEFAULT, HandleDirection.OUTPUT),
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
            "x": self.x_offset + col * self.x_spacing,
            "y": self.y_offset + row * self.y_spacing,
        }

    def calculate_vertical_position(self, index: int, x: int = 300) -> dict[str, float]:
        return {"x": x, "y": self.y_offset + index * self.y_spacing}

    def calculate_horizontal_position(self, index: int, y: int = 300) -> dict[str, float]:
        return {
            "x": self.x_offset + index * self.x_spacing,
            "y": y,
        }


class ArrowBuilder:
    @staticmethod
    def create_arrow_id(source_handle: str, target_handle: str) -> str:
        return f"{source_handle}->{target_handle}"

    @staticmethod
    def create_simple_arrow(
        source_node: str,
        target_node: str,
        source_label: HandleLabel = HandleLabel.DEFAULT,
        target_label: HandleLabel = HandleLabel.DEFAULT,
    ) -> tuple[str, str, str]:
        s = str(create_handle_id(NodeID(source_node), source_label, HandleDirection.OUTPUT))
        t = str(create_handle_id(NodeID(target_node), target_label, HandleDirection.INPUT))
        return ArrowBuilder.create_arrow_id(s, t), s, t


def coerce_to_dict(
    seq_or_map: Mapping[str, Any] | Sequence[Any] | None,
    id_key: str = "id",
    prefix: str = "obj",
) -> dict[str, Any]:
    if isinstance(seq_or_map, dict):
        return dict(seq_or_map)
    if isinstance(seq_or_map, list | tuple):
        return {
            (
                item.get(id_key) if isinstance(item, dict) and id_key in item else f"{prefix}_{i}"
            ): item
            for i, item in enumerate(seq_or_map)
        }
    return {}


def build_node(id: str, type_: str, pos: dict[str, float] | None = None, **data) -> dict[str, Any]:
    return {"id": id, "type": type_, "position": pos or {}, **data}


def ensure_position(
    node_dict: dict[str, Any],
    index: int,
    position_calculator: PositionCalculator | None = None,
) -> None:
    if not node_dict.get("position"):
        calc = position_calculator or PositionCalculator()
        vec = calc.calculate_grid_position(index)
        node_dict["position"] = {"x": vec.get("x"), "y": vec.get("y")}


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
