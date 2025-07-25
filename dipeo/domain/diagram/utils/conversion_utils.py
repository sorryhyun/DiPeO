"""Conversion utilities for diagram formats."""

import json
from typing import Any

import yaml

from dipeo.diagram_generated import DomainDiagram
from dipeo.diagram_generated.conversions import diagram_arrays_to_maps, diagram_maps_to_arrays

DomainDiagram.model_rebuild()


def dict_to_domain_diagram(diagram_dict: dict[str, Any]) -> DomainDiagram:
    """Convert dict-based diagram representation to DomainDiagram.
    
    Args:
        diagram_dict: Dict with keys as IDs (e.g. {"nodes": {"node_0": {...}}})
        
    Returns:
        DomainDiagram with array-based structure
    """
    arrays_dict = diagram_maps_to_arrays(
        nodes=diagram_dict.get("nodes", {}),
        arrows=diagram_dict.get("arrows", {}),
        handles=diagram_dict.get("handles", {}),
        persons=diagram_dict.get("persons", {})
    )

    handles_list = []
    for handle in arrays_dict.get("handles", []):
        if isinstance(handle, dict) and "id" not in handle:
            continue
        handles_list.append(handle)

    result_dict = {
        "nodes": arrays_dict["nodes"],
        "arrows": arrays_dict["arrows"],
        "handles": handles_list,
        "persons": arrays_dict["persons"],
        "metadata": diagram_dict.get("metadata"),
    }

    result_dict = {k: v for k, v in result_dict.items() if v is not None}

    return DomainDiagram(**result_dict)


def domain_diagram_to_dict(domain_diagram: DomainDiagram) -> dict[str, Any]:
    """Convert DomainDiagram to dict-based representation.
    
    Args:
        domain_diagram: DomainDiagram with array-based structure
        
    Returns:
        Dict with keys as IDs for efficient lookups
    """
    maps_dict = diagram_arrays_to_maps(
        nodes=domain_diagram.nodes or [],
        arrows=domain_diagram.arrows or [],
        handles=domain_diagram.handles or [],
        persons=domain_diagram.persons or []
    )

    result = {
        "nodes": maps_dict["nodes"],
        "arrows": maps_dict["arrows"],
        "handles": maps_dict["handles"],
        "persons": maps_dict["persons"],
        "metadata": domain_diagram.metadata.model_dump()
        if domain_diagram.metadata
        else {},
    }

    for key in ["nodes", "arrows", "handles", "persons"]:
        result[key] = {
            k: v.model_dump() if hasattr(v, "model_dump") else v
            for k, v in result[key].items()
        }

    return result


# Generic helpers


class _JsonMixin:
    # Minimal JSON helpers

    def parse(self, content: str) -> dict[str, Any]:  # type: ignore[override]
        return json.loads(content or "{}")

    def format(self, data: dict[str, Any]) -> str:  # type: ignore[override]
        return json.dumps(data, indent=2, ensure_ascii=False)


class _YamlMixin:
    # Minimal YAML helpers

    def parse(self, content: str) -> dict[str, Any]:  # type: ignore[override]
        return yaml.safe_load(content) or {}

    def format(self, data: dict[str, Any]) -> str:  # type: ignore[override]
        class CustomDumper(yaml.SafeDumper):
            pass

        def position_representer(dumper, data):
            if isinstance(data, dict) and set(data.keys()) == {"x", "y"}:
                return dumper.represent_mapping(
                    "tag:yaml.org,2002:map", data, flow_style=True
                )
            return dumper.represent_dict(data)

        def str_representer(dumper, data):
            if '\n' in data:
                # Use literal (block) style for multiline strings
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)
        
        def list_representer(dumper, data):
            # Use inline flow style for boolean arrays (flipped property)
            # Check if it's a 2-element boolean array
            if len(data) == 2 and all(isinstance(x, bool) for x in data):
                return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
            return dumper.represent_list(data)

        CustomDumper.add_representer(dict, position_representer)
        CustomDumper.add_representer(str, str_representer)
        CustomDumper.add_representer(list, list_representer)

        return yaml.dump(
            data, Dumper=CustomDumper, sort_keys=False, allow_unicode=True, default_flow_style=False
        )


def _node_id_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    # Map label → node.id for already-built nodes

    label_map = {}
    for n in nodes:
        label = n.get("label") or n.get("data", {}).get("label") or n["id"]
        label_map[label] = n["id"]
    return label_map

