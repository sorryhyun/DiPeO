"""Conversion utilities for diagram formats."""

import json
from typing import Any

import yaml

from dipeo.diagram_generated import DomainDiagram

DomainDiagram.model_rebuild()


class _JsonMixin:
    def parse(self, content: str) -> dict[str, Any]:  # type: ignore[override]
        try:
            result = json.loads(content or "{}")
            if not isinstance(result, dict):
                raise ValueError(f"Expected dict from JSON parse, got {type(result).__name__}")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}") from e

    def format(self, data: dict[str, Any]) -> str:  # type: ignore[override]
        return json.dumps(data, indent=2, ensure_ascii=False)


class _YamlMixin:
    def parse(self, content: str) -> dict[str, Any]:  # type: ignore[override]
        return yaml.safe_load(content) or {}

    def format(self, data: dict[str, Any]) -> str:  # type: ignore[override]
        class CustomDumper(yaml.SafeDumper):
            pass

        def position_representer(dumper, data):
            if isinstance(data, dict) and set(data.keys()) == {"x", "y"}:
                return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)
            return dumper.represent_dict(data)

        def str_representer(dumper, data):
            if "\n" in data:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        def list_representer(dumper, data):
            # Use inline flow style for 2-element boolean arrays
            if len(data) == 2 and all(isinstance(x, bool) for x in data):
                return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
            return dumper.represent_list(data)

        CustomDumper.add_representer(dict, position_representer)
        CustomDumper.add_representer(str, str_representer)
        CustomDumper.add_representer(list, list_representer)

        return yaml.dump(
            data, Dumper=CustomDumper, sort_keys=False, allow_unicode=True, default_flow_style=False
        )


def _node_id_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    label_map = {}
    for n in nodes:
        label = n.get("label") or n.get("data", {}).get("label") or n["id"]
        label_map[label] = n["id"]
    return label_map


def diagram_maps_to_arrays(diagram: dict[str, Any]) -> dict[str, Any]:
    """Convert map-based diagram to array-based structure."""
    return {
        "nodes": list(diagram.get("nodes", {}).values()),
        "arrows": list(diagram.get("arrows", {}).values()),
        "handles": list(diagram.get("handles", {}).values()),
        "persons": list(diagram.get("persons", {}).values()),
    }
