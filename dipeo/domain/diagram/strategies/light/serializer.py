from __future__ import annotations

from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.models.format_models import LightConnection, LightDiagram, LightNode
from dipeo.domain.diagram.utils import (
    ArrowDataProcessor,
    HandleIdOperations,
    NodeFieldMapper,
    PersonReferenceResolver,
)


class LightDiagramSerializer:
    """Serializes domain diagrams to light YAML format."""

    @staticmethod
    def domain_to_light_diagram(diagram: DomainDiagram) -> LightDiagram:
        id_to_label: dict[str, str] = {}
        label_counts: dict[str, int] = {}

        person_id_to_label = PersonReferenceResolver.build_id_to_label_map(diagram.persons)

        def _unique(base: str) -> str:
            cnt = label_counts.get(base, 0)
            label_counts[base] = cnt + 1
            return f"{base}~{cnt}" if cnt else base

        nodes_out = []
        for n in diagram.nodes:
            base = n.data.get("label") or str(n.type).split(".")[-1].title()
            label = _unique(base)
            id_to_label[n.id] = label
            node_type = str(n.type).split(".")[-1].lower()

            props = {
                k: v
                for k, v in (n.data or {}).items()
                if k not in {"label", "position"}
                and v not in (None, "", {})
                and not (k != "flipped" and v == [])
            }

            if node_type == "person_job" and "person" in props:
                person_id = props["person"]
                if person_id in person_id_to_label:
                    props["person"] = person_id_to_label[person_id]

            props = NodeFieldMapper.map_export_fields(node_type, props)

            node = LightNode(
                type=node_type,
                label=label,
                position={"x": round(n.position.x), "y": round(n.position.y)},
                **props,
            )
            nodes_out.append(node)

        connections = []
        for a in diagram.arrows:
            s_node_id, s_handle, _ = HandleIdOperations.parse_handle_id(a.source)
            t_node_id, t_handle, _ = HandleIdOperations.parse_handle_id(a.target)

            from_str = f"{id_to_label[s_node_id]}{'_' + s_handle if s_handle != 'default' else ''}"
            to_str = f"{id_to_label[t_node_id]}{'_' + t_handle if t_handle != 'default' else ''}"

            conn_kwargs = {
                "from": from_str,
                "to": to_str,
                "label": a.label,
                "type": a.content_type if a.content_type else None,
            }
            if a.data and ArrowDataProcessor.should_include_branch_data(s_handle, a.data):
                conn_kwargs["data"] = {"branch": a.data["branch"]}  # type: ignore[assignment]

            conn = LightConnection(**conn_kwargs)  # type: ignore[arg-type]
            connections.append(conn)

        persons_data = None
        if diagram.persons:
            persons_dict = {}
            for p in diagram.persons:
                person_data = {
                    "service": p.llm_config.service
                    if hasattr(p.llm_config.service, "value")
                    else str(p.llm_config.service),
                    "model": p.llm_config.model,
                }
                if p.llm_config.system_prompt:
                    person_data["system_prompt"] = p.llm_config.system_prompt
                if p.llm_config.api_key_id:
                    person_data["api_key_id"] = p.llm_config.api_key_id
                persons_dict[p.label] = person_data
            persons_data = persons_dict

        return LightDiagram(
            nodes=nodes_out,
            connections=connections,
            persons=persons_data,  # type: ignore[arg-type]
            metadata=diagram.metadata.model_dump(exclude_none=True) if diagram.metadata else None,
        )

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
