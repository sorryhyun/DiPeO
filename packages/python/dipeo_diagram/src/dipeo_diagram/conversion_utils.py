"""Conversion utilities for diagram formats."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field
from dipeo_domain import DomainDiagram
import json
import yaml

# Ensure models are rebuilt to resolve forward references
DomainDiagram.model_rebuild()


class BackendDiagram(BaseModel):
    """Backend representation of a diagram (dict of dicts).

    This is a simple wrapper around the dict format used for storage and execution.
    Fields are untyped dicts to avoid unnecessary conversions.
    """

    nodes: dict[str, Any] = Field(default_factory=dict)
    arrows: dict[str, Any] = Field(default_factory=dict)
    persons: dict[str, Any] = Field(default_factory=dict)
    handles: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] | None = None

    class Config:
        extra = "allow"  # Allow additional fields like _execution_hints


def backend_to_graphql(backend_dict: BackendDiagram) -> DomainDiagram:
    """Convert backend dict representation to GraphQL domain model.

    The backend representation uses dicts of dicts for efficient lookup.
    The GraphQL representation uses lists for easier client handling.
    """

    # Convert dict-of-dicts to lists (if necessary)
    def ensure_list(obj):
        if obj is None:
            return []
        if isinstance(obj, dict):
            return list(obj.values())
        return obj

    # Special handling for handles to ensure 'id' field exists
    def ensure_handles_list(handles_dict):
        if handles_dict is None:
            return []
        if isinstance(handles_dict, dict):
            result = []
            for key, value in handles_dict.items():
                if isinstance(value, dict) and "id" not in value:
                    # Add the key as id if missing
                    handle = value.copy()
                    handle["id"] = key
                    result.append(handle)
                else:
                    result.append(value)
            return result
        return handles_dict

    # Create a copy to avoid mutating the original
    result_dict = {
        "nodes": ensure_list(backend_dict.nodes),
        "arrows": ensure_list(backend_dict.arrows),
        "handles": ensure_handles_list(backend_dict.handles),
        "persons": ensure_list(backend_dict.persons),
        "metadata": backend_dict.metadata,
    }

    # Remove None values
    result_dict = {k: v for k, v in result_dict.items() if v is not None}

    return DomainDiagram(**result_dict)


def graphql_to_backend(graphql_diagram: DomainDiagram) -> dict[str, dict[str, Any]]:
    """Convert GraphQL domain model to backend dict representation.

    The backend representation uses dicts of dicts for efficient lookup.
    The GraphQL representation uses lists for easier client handling.
    """

    def list_to_dict(items, id_attr="id"):
        if items is None:
            return {}
        # If already a dict, return as-is
        if isinstance(items, Mapping):
            return dict(items)
        # Convert list to dict using ID
        result = {}
        for item in items:
            # Handle both dict and object representations
            if hasattr(item, "__dict__"):
                item_dict = item.__dict__
                item_id = getattr(item, id_attr)
            else:
                item_dict = item
                item_id = item.get(id_attr)

            if item_id:
                result[item_id] = item_dict

        return result

    # Build the backend dict structure
    return {
        "nodes": list_to_dict(graphql_diagram.nodes),
        "arrows": list_to_dict(graphql_diagram.arrows),
        "handles": list_to_dict(graphql_diagram.handles),
        "persons": list_to_dict(graphql_diagram.persons),
        "metadata": graphql_diagram.metadata.model_dump()
        if graphql_diagram.metadata
        else {},
    }


#  generic helpers


class _JsonMixin:
    """Minimal JSON helpers."""

    def parse(self, content: str) -> dict[str, Any]:  # type: ignore[override]
        return json.loads(content or "{}")

    def format(self, data: dict[str, Any]) -> str:  # type: ignore[override]
        return json.dumps(data, indent=2, ensure_ascii=False)


class _YamlMixin:
    """Minimal YAML helpers."""

    def parse(self, content: str) -> dict[str, Any]:  # type: ignore[override]
        return yaml.safe_load(content) or {}

    def format(self, data: dict[str, Any]) -> str:  # type: ignore[override]
        # Create a custom YAML dumper class
        class PositionDumper(yaml.SafeDumper):
            pass

        # Custom representer for position dicts to use flow style
        def position_representer(dumper, data):
            if isinstance(data, dict) and set(data.keys()) == {"x", "y"}:
                return dumper.represent_mapping(
                    "tag:yaml.org,2002:map", data, flow_style=True
                )
            return dumper.represent_dict(data)

        PositionDumper.add_representer(dict, position_representer)

        return yaml.dump(
            data, Dumper=PositionDumper, sort_keys=False, allow_unicode=True
        )


def _node_id_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    """Map `label` → `node.id` for already‑built nodes."""

    label_map = {}
    for n in nodes:
        # Try to get label from the node structure
        label = n.get("label") or n.get("data", {}).get("label") or n["id"]
        label_map[label] = n["id"]
    return label_map


def _round_pos(pos: Any) -> dict[str, int]:
    """Return a rounded position dict from Domain Vec2 or mapping."""

    if hasattr(pos, "model_dump"):
        pos = pos.model_dump()
    if hasattr(pos, "x") and hasattr(pos, "y"):
        return {"x": round(pos.x), "y": round(pos.y)}  # type: ignore[attr-defined]
    if isinstance(pos, dict):
        return {"x": round(pos.get("x", 0)), "y": round(pos.get("y", 0))}
    return {"x": 0, "y": 0}
