"""Conversion utilities for diagram formats."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field
from dipeo.models import DomainDiagram
from dipeo.models.conversions import diagram_arrays_to_maps, diagram_maps_to_arrays
import json
import yaml
from .base import FormatStrategy
from .shared_components import extract_common_arrows

DomainDiagram.model_rebuild()


class BackendDiagram(BaseModel):
    # Backend representation of a diagram (dict of dicts)
    # Simple wrapper around dict format for storage and execution

    nodes: dict[str, Any] = Field(default_factory=dict)
    arrows: dict[str, Any] = Field(default_factory=dict)
    persons: dict[str, Any] = Field(default_factory=dict)
    handles: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] | None = None

    class Config:
        extra = "allow"


def backend_to_graphql(backend_dict: BackendDiagram) -> DomainDiagram:
    # Convert backend dict representation to GraphQL domain model
    arrays_dict = diagram_maps_to_arrays(
        nodes=backend_dict.nodes or {},
        arrows=backend_dict.arrows or {},
        handles=backend_dict.handles or {},
        persons=backend_dict.persons or {},
        api_keys=None  # Not used in BackendDiagram
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
        "metadata": backend_dict.metadata,
    }

    result_dict = {k: v for k, v in result_dict.items() if v is not None}

    return DomainDiagram(**result_dict)


def graphql_to_backend(graphql_diagram: DomainDiagram) -> dict[str, dict[str, Any]]:
    # Convert GraphQL domain model to backend dict representation
    maps_dict = diagram_arrays_to_maps(
        nodes=graphql_diagram.nodes or [],
        arrows=graphql_diagram.arrows or [],
        handles=graphql_diagram.handles or [],
        persons=graphql_diagram.persons or [],
        api_keys=None
    )

    result = {
        "nodes": maps_dict["nodes"],
        "arrows": maps_dict["arrows"],
        "handles": maps_dict["handles"],
        "persons": maps_dict["persons"],
        "metadata": graphql_diagram.metadata.model_dump()
        if graphql_diagram.metadata
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
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        CustomDumper.add_representer(dict, position_representer)
        CustomDumper.add_representer(str, str_representer)

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

