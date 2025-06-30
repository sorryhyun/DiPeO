"""Lightweight shared utilities for diagram converters."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from dipeo_domain import (
    DataType,
    DomainDiagram,
    DomainHandle,
    HandleDirection,
    HandleID,
    NodeID,
    Vec2,
)

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

# internal helpers


def _push_handle(
    container: DomainDiagram | BackendDiagram, handle: DomainHandle
) -> None:
    """Add *handle* to *container*, regardless of list / mapping storage."""
    if isinstance(container, BackendDiagram):
        container.handles[handle.id] = handle  # type: ignore[index]
    else:
        container.handles.append(handle)


def _make_handle(
    node_id: str,
    suffix: str,
    label: str,
    direction: HandleDirection,
    dtype: DataType = DataType.any,
) -> DomainHandle:
    hid = f"{node_id}:{suffix}"
    return DomainHandle(
        id=HandleID(hid),
        nodeId=NodeID(node_id),
        label=label,
        direction=direction,
        dataType=dtype,
        position="left" if direction is HandleDirection.input else "right",
    )


# public API


class HandleGenerator:
    """Generate default / conditional handles for a node."""

    def generate_for_node(
        self,
        diagram: DomainDiagram | BackendDiagram,
        node_id: str,
        node_type: str,
    ) -> None:
        # database nodes use a single *default* input
        if node_type == "db":
            _push_handle(
                diagram,
                _make_handle(node_id, "default", "default", HandleDirection.input),
            )
            return

        table = [
            ("input", "input", HandleDirection.input, node_type != "start"),
            ("output", "output", HandleDirection.output, node_type != "endpoint"),
            ("true", "true", HandleDirection.output, node_type == "condition"),
            ("false", "false", HandleDirection.output, node_type == "condition"),
        ]
        for suffix, label, direction, keep in table:
            if keep:
                _push_handle(
                    diagram,
                    _make_handle(
                        node_id,
                        suffix,
                        label,
                        direction,
                        DataType.boolean
                        if suffix in {"true", "false"}
                        else DataType.any,
                    ),
                )


class PositionCalculator:
    """Simple grid / line layouts with sensible defaults."""

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

    # grid
    def calculate_grid_position(self, index: int) -> Vec2:
        row, col = divmod(index, self.columns)
        return Vec2(
            x=self.x_offset + col * self.x_spacing,
            y=self.y_offset + row * self.y_spacing,
        )

    # vertical / horizontal
    def calculate_vertical_position(self, index: int, x: int = 300) -> Vec2:
        return Vec2(x=x, y=self.y_offset + index * self.y_spacing)

    def calculate_horizontal_position(self, index: int, y: int = 300) -> Vec2:
        return Vec2(
            x=self.x_offset + index * self.x_spacing,
            y=y,
        )


class ArrowBuilder:
    """Utility helpers for creating consistent arrow IDs."""

    @staticmethod
    def create_arrow_id(source_handle: str, target_handle: str) -> str:  # noqa: D401
        return f"{source_handle}->{target_handle}"

    @staticmethod
    def create_simple_arrow(
        source_node: str,
        target_node: str,
        source_label: str = "output",
        target_label: str = "input",
    ) -> tuple[str, str, str]:
        s = f"{source_node}:{source_label}"
        t = f"{target_node}:{target_label}"
        return ArrowBuilder.create_arrow_id(s, t), s, t


# misc helpers


def coerce_to_dict(
    seq_or_map: Mapping[str, Any] | Sequence[Any] | None,
    id_key: str = "id",
    prefix: str = "obj",
) -> dict[str, Any]:
    """Return mapping no matter the input shape, fabricating keys where needed."""
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
    """Return a normalised list of arrows `[{id, source, target, data}, …]`."""
    if not arrows:
        return []

    pairs = (
        arrows.items()
        if isinstance(arrows, dict)
        else ((d.get("id"), d) for d in arrows if isinstance(d, dict))
    )
    return [
        {
            "id": aid,
            "source": a.get("source"),
            "target": a.get("target"),
            "data": a.get("data"),
        }
        for aid, a in pairs
        if aid and a.get("source") and a.get("target")
    ]
