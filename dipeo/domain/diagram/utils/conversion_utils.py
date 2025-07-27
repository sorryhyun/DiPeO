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
        DomainDiagram with map-based structure
    """
    # Check if the input is already in map format (keys are IDs)
    nodes = diagram_dict.get("nodes", {})
    if isinstance(nodes, list):
        # Convert from array to map format
        maps_dict = diagram_arrays_to_maps(diagram_dict)
        nodes = maps_dict.get("nodes", {})
        arrows = maps_dict.get("arrows", {})
        handles = maps_dict.get("handles", {})
        persons = maps_dict.get("persons", {})
    else:
        # Already in map format
        arrows = diagram_dict.get("arrows", {})
        handles = diagram_dict.get("handles", {})
        persons = diagram_dict.get("persons", {})

    # Convert node dicts to DomainNode objects if needed
    from dipeo.diagram_generated import DomainNode, DomainArrow, DomainHandle, DomainPerson
    
    nodes_map = {}
    for node_id, node in nodes.items():
        if isinstance(node, dict) and not hasattr(node, 'type'):
            # Convert dict to DomainNode
            nodes_map[node_id] = DomainNode(**node)
        else:
            nodes_map[node_id] = node
    
    # Convert arrow dicts to DomainArrow objects if needed
    arrows_map = {}
    for arrow_id, arrow in arrows.items():
        if isinstance(arrow, dict) and not hasattr(arrow, 'source'):
            arrows_map[arrow_id] = DomainArrow(**arrow)
        else:
            arrows_map[arrow_id] = arrow
    
    # Convert handle dicts to DomainHandle objects if needed
    handles_map = {}
    for handle_id, handle in handles.items():
        if isinstance(handle, dict) and handle:  # Ensure non-empty
            if not hasattr(handle, 'node_id'):
                handles_map[handle_id] = DomainHandle(**handle)
            else:
                handles_map[handle_id] = handle
    
    # Convert person dicts to DomainPerson objects if needed
    persons_map = {}
    for person_id, person in persons.items():
        if isinstance(person, dict) and not hasattr(person, 'name'):
            persons_map[person_id] = DomainPerson(**person)
        else:
            persons_map[person_id] = person

    result_dict = {
        "nodes": list(nodes_map.values()),
        "arrows": list(arrows_map.values()),
        "handles": list(handles_map.values()),
        "persons": list(persons_map.values()),
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

