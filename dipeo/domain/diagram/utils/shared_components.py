# Lightweight shared utilities for diagram converters

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import DataType, HandleDirection, HandleLabel, NodeID, NodeType

from .arrow_builder import ArrowBuilder
from .handle_operations import HandleIdOperations

logger = get_module_logger(__name__)

if TYPE_CHECKING:
    pass

__all__ = (
    "ArrowBuilder",
    "HandleGenerator",
    "HandleSpec",
    "PositionCalculator",
    "build_node",
    "coerce_to_dict",
    "ensure_position",
    "extract_common_arrows",
)


def _create_handle_id_from_enums(
    node_id: str, label: HandleLabel, direction: HandleDirection
) -> str:
    result = HandleIdOperations.create_handle_id(NodeID(node_id), label, direction)
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


@dataclass
class HandleSpec:
    label: HandleLabel
    direction: HandleDirection
    data_type: DataType = DataType.ANY


HANDLE_SPECS: dict[str, list[HandleSpec]] = {
    NodeType.START: [
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
    ],
    NodeType.ENDPOINT.value: [
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
    ],
    NodeType.CONDITION.value: [
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
        HandleSpec(HandleLabel.CONDTRUE, HandleDirection.OUTPUT, DataType.BOOLEAN),
        HandleSpec(HandleLabel.CONDFALSE, HandleDirection.OUTPUT, DataType.BOOLEAN),
    ],
    NodeType.DB.value: [
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
    ],
    NodeType.PERSON_JOB.value: [
        HandleSpec(HandleLabel.FIRST, HandleDirection.INPUT),
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
    ],
    NodeType.USER_RESPONSE.value: [
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
    ],
}

DEFAULT_HANDLES = [
    HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
    HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
]


class HandleGenerator:
    def generate_for_node(
        self,
        diagram: dict[str, Any] | Any,
        node_id: str,
        node_type: str,
    ) -> None:
        handle_specs = HANDLE_SPECS.get(node_type, DEFAULT_HANDLES)
        for spec in handle_specs:
            _push_handle(
                diagram,
                _make_handle(node_id, spec.label, spec.direction, spec.data_type),
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
