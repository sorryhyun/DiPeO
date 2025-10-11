"""Serializer for light format - converts light diagram to export dictionary."""

from __future__ import annotations

from typing import Any

from dipeo.domain.diagram.models.format_models import LightDiagram


class LightDiagramSerializer:
    """Serializes light diagrams to export format."""

    @staticmethod
    def light_diagram_to_export_dict(light_diagram: LightDiagram) -> dict[str, Any]:
        nodes_out = []
        for node in light_diagram.nodes:
            node_dict = {
                "label": node.label,
                "type": node.type,
                "position": node.position,
            }
            props = {
                k: v for k, v in node.model_dump(exclude={"type", "label", "position"}).items() if v
            }
            if props:
                node_dict["props"] = props
            nodes_out.append(node_dict)

        connections_out = []
        for conn in light_diagram.connections:
            conn_dict = {
                "from": conn.from_,
                "to": conn.to,
            }
            if conn.label:
                conn_dict["label"] = conn.label
            if conn.type:
                conn_dict["content_type"] = conn.type
            extra = conn.model_dump(exclude={"from_", "to", "label", "type"})
            if extra:
                conn_dict.update(extra)
            connections_out.append(conn_dict)

        out: dict[str, Any] = {"version": "light", "nodes": nodes_out}
        if connections_out:
            out["connections"] = connections_out
        if light_diagram.persons:
            out["persons"] = light_diagram.persons
        if light_diagram.metadata:
            out["metadata"] = light_diagram.metadata
        return out
