from __future__ import annotations

from typing import Any

from dipeo.domain.diagram.models.format_models import LightConnection, LightDiagram, LightNode
from dipeo.domain.diagram.utils import (
    DiagramDataExtractor,
    NodeFieldMapper,
    create_node_id,
    process_dotted_keys,
)


class LightDiagramParser:
    """Parses light YAML format into LightDiagram models."""

    @staticmethod
    def parse_to_light_diagram(data: dict[str, Any]) -> LightDiagram:
        nodes = []
        for node_data in data.get("nodes", []):
            if isinstance(node_data, dict):
                props = node_data.get("props", {})
                for k, v in node_data.items():
                    if k not in {"type", "label", "position", "props"}:
                        props[k] = v

                node = LightNode(
                    type=node_data.get("type", "job"),
                    label=node_data.get("label"),
                    position=node_data.get("position"),
                    **props,
                )
                nodes.append(node)

        connections = []
        for conn_data in data.get("connections", []):
            if isinstance(conn_data, dict):
                conn_dict = {
                    "from": conn_data.get("from", ""),
                    "to": conn_data.get("to", ""),
                }
                if "label" in conn_data:
                    conn_dict["label"] = conn_data["label"]
                if "content_type" in conn_data or "type" in conn_data:
                    conn_dict["type"] = conn_data.get("content_type") or conn_data.get("type")

                for k, v in conn_data.items():
                    if k not in {"from", "to", "label", "type", "content_type"}:
                        conn_dict[k] = v

                conn = LightConnection(**conn_dict)
                connections.append(conn)

        persons = data.get("persons")
        if persons and isinstance(persons, dict):
            persons = list(persons.values())

        api_keys = data.get("api_keys")
        if api_keys and isinstance(api_keys, dict):
            api_keys = list(api_keys.values())

        return LightDiagram(
            nodes=nodes,
            connections=connections,
            persons=persons,
            api_keys=api_keys,
            metadata=data.get("metadata"),
        )

    @staticmethod
    def extract_node_props_from_light(node_data: dict[str, Any]) -> dict[str, Any]:
        props = {}
        for k, v in node_data.items():
            if k not in {"type", "label", "position"}:
                props[k] = v

        props = process_dotted_keys(props)

        node_type = node_data.get("type", "job")
        props = NodeFieldMapper.map_import_fields(node_type, props)

        return props

    @staticmethod
    def extract_handles_dict(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return DiagramDataExtractor.extract_handles(data, format_type="light")

    @staticmethod
    def extract_persons_dict(data: dict[str, Any]) -> dict[str, Any]:
        return DiagramDataExtractor.extract_persons(data, format_type="light")
