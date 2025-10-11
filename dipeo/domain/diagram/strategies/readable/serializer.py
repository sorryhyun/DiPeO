"""Serializer for readable format - handles diagram export and serialization."""

from __future__ import annotations

from typing import Any

from dipeo.domain.diagram.models.format_models import ReadableDiagram
from dipeo.domain.diagram.utils import NodeFieldMapper


class ReadableSerializer:
    """Serializes ReadableDiagram to export format."""

    def readable_diagram_to_export_dict(self, readable_diagram: ReadableDiagram) -> dict[str, Any]:
        """Convert ReadableDiagram to export dictionary format."""
        id_to_label: dict[str, str] = {}
        for n in readable_diagram.nodes:
            id_to_label[n.id] = n.label

        nodes = []
        for n in readable_diagram.nodes:
            label = n.label

            if n.position and (n.position["x"] != 0 or n.position["y"] != 0):
                label_with_pos = f"{label} @({int(n.position['x'])},{int(n.position['y'])})"
            else:
                label_with_pos = label

            node_config = {"type": n.type} if n.type != "job" else {}
            if n.props:
                mapped_props = NodeFieldMapper.map_export_fields(n.type, n.props.copy())
                filtered_props = {
                    k: v for k, v in mapped_props.items() if v not in (None, "", {}, [])
                }
                node_config.update(filtered_props)

            if node_config:
                nodes.append({label_with_pos: node_config})
            else:
                nodes.append({label_with_pos: {}})

        flow = self._build_enhanced_flow(readable_diagram, id_to_label)

        persons = []
        if readable_diagram.persons:
            for person_data in readable_diagram.persons:
                person_dict = {}
                if "label" in person_data and "llm_config" in person_data:
                    config = person_data["llm_config"]
                    person_config = {
                        "service": config.get("service", "openai"),
                        "model": config.get("model", "gpt-4"),
                    }
                    if config.get("system_prompt"):
                        person_config["system_prompt"] = config["system_prompt"]
                    if config.get("api_key_id"):
                        person_config["api_key_id"] = config["api_key_id"]
                    person_dict[person_data["label"]] = person_config
                    persons.append(person_dict)

        out: dict[str, Any] = {"version": "readable"}
        if persons:
            out["persons"] = persons
        out["nodes"] = nodes
        if flow:
            out["flow"] = flow
        return out

    def _build_enhanced_flow(
        self, readable_diagram: ReadableDiagram, id_to_label: dict[str, str]
    ) -> list[str]:
        """Build enhanced flow array for export."""
        source_groups: dict[str, list] = {}

        for a in readable_diagram.arrows:
            source_label = id_to_label.get(a.source, a.source)

            if a.source_handle and a.source_handle not in ("output", "default"):
                if a.source_handle in ["condtrue", "condfalse"]:
                    source_key = source_label
                else:
                    source_key = f"{source_label}_{a.source_handle}"
            else:
                source_key = source_label

            if source_key not in source_groups:
                source_groups[source_key] = []

            target_str = self._build_flow_target_string(
                id_to_label.get(a.target, a.target),
                a.target_handle,
                a.source_handle,
                a.data.get("content_type") if a.data else None,
                a.label,
            )

            source_groups[source_key].append(target_str)

        flow = []
        for source_key, targets in source_groups.items():
            if len(targets) == 1:
                flow.append({source_key: targets[0]})
            else:
                flow.append({source_key: targets})

        return flow

    def _build_flow_target_string(
        self,
        target_label: str,
        target_handle: str | None,
        source_handle: str | None,
        content_type: str | None,
        label: str | None,
    ) -> str:
        """Build flow target string with proper formatting."""
        parts = []

        if source_handle and source_handle in ["condtrue", "condfalse"]:
            parts.append(f'from "_{source_handle}"')

        parts.append(f'to "{target_label}"')

        if target_handle and target_handle not in ("input", "default", "_first"):
            parts.append(f'in "{target_handle}"')
        elif target_handle == "_first":
            parts.append('in "_first"')

        if content_type:
            parts.append(f'as "{content_type}"')

        if label:
            parts.append(f'naming "{label}"')

        return " ".join(parts)
