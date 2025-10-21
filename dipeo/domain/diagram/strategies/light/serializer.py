"""Serializer for light format - converts light diagram to export dictionary."""

from __future__ import annotations

from typing import Any

from dipeo.domain.diagram.models.format_models import LightDiagram


class LightDiagramSerializer:
    """Serializes light diagrams to export format."""

    @staticmethod
    def _normalize_to_bracket_syntax(endpoint: str, label_to_node: dict[str, dict]) -> str:
        """Convert underscore syntax to bracket syntax.

        Args:
            endpoint: Connection endpoint (e.g., "NodeLabel_handle" or "NodeLabel[handle]")
            label_to_node: Mapping from node labels to node dicts with 'type' field

        Returns:
            Normalized endpoint using bracket syntax (e.g., "NodeLabel[handle]")
        """
        if "[" in endpoint and "]" in endpoint:
            return endpoint

        if "_" not in endpoint:
            return endpoint

        parts = endpoint.split("_")
        for i in range(len(parts) - 1, 0, -1):
            potential_label = "_".join(parts[:i])
            if potential_label in label_to_node:
                handle = "_".join(parts[i:])
                if handle == "_first":
                    handle = "first"
                return f"{potential_label}[{handle}]"

            potential_label_with_spaces = " ".join(parts[:i])
            if potential_label_with_spaces in label_to_node:
                handle = "_".join(parts[i:])
                if handle == "_first":
                    handle = "first"
                return f"{potential_label_with_spaces}[{handle}]"

        return endpoint

    @staticmethod
    def light_diagram_to_export_dict(light_diagram: LightDiagram) -> dict[str, Any]:
        label_to_node = {node.label: {"type": node.type} for node in light_diagram.nodes}

        nodes_out = []
        for node in light_diagram.nodes:
            node_dict = {
                "label": node.label,
                "type": node.type,
                "position": node.position,
            }
            # Flatten all properties to top level (no "props" wrapper)
            extra_props = {
                k: v for k, v in node.model_dump(exclude={"type", "label", "position"}).items() if v
            }
            node_dict.update(extra_props)
            nodes_out.append(node_dict)

        connections_out = []
        for conn in light_diagram.connections:
            conn_dict = {
                "from": LightDiagramSerializer._normalize_to_bracket_syntax(
                    conn.from_, label_to_node
                ),
                "to": LightDiagramSerializer._normalize_to_bracket_syntax(conn.to, label_to_node),
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
