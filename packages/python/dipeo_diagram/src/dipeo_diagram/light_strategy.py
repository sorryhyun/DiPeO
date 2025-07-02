from __future__ import annotations

import logging
from typing import Any, Callable
from dipeo_domain import DomainDiagram
from .shared_components import (
    build_node,
    coerce_to_dict,
    ensure_position,
)

log = logging.getLogger(__name__)

from .conversion_utils import _YamlMixin, _BaseStrategy, _node_id_map



class LightYamlStrategy(_YamlMixin, _BaseStrategy):
    """Simplified YAML that uses labels instead of IDs."""

    format_id = "light"
    format_info = {
        "name": "Light YAML",
        "description": "Simplified format using labels instead of IDs",
        "extension": ".light.yaml",
        "supports_import": True,
        "supports_export": True,
    }

    # ---- extraction ------------------------------------------------------- #
    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:  # noqa: D401
        nodes: list[dict[str, Any]] = []
        for idx, n in enumerate(data.get("nodes", [])):
            if not isinstance(n, dict):
                continue
            props = {
                **n.get("props", {}),
                **{
                    k: v
                    for k, v in n.items()
                    if k not in {"label", "type", "position", "props"}
                },
            }

            # Convert legacy forgetting_mode to proper memory_config structure
            if "forgetting_mode" in props:
                props["memory_config"] = {
                    "forget_mode": props.pop("forgetting_mode")
                }

            # Add required fields for specific node types
            node_type = n.get("type", "job")
            if node_type == "start":
                # Add default values for required fields
                props.setdefault("custom_data", {})
                props.setdefault("output_data_structure", {})
            elif node_type == "endpoint":
                # Map filePath to fileName for endpoint nodes
                if "filePath" in props and "file_name" not in props:
                    props["file_name"] = props.pop("filePath")

            node = build_node(
                id=f"node_{idx}",
                type_=node_type,
                pos=n.get("position", {}),
                label=n.get("label"),
                **props,
            )
            ensure_position(node, idx)
            nodes.append(node)
        return nodes

    def extract_arrows(
            self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # noqa: D401
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        for idx, c in enumerate(data.get("connections", [])):
            if not isinstance(c, dict):
                continue
            src_raw, dst_raw = c.get("from", ""), c.get("to", "")
            src_label, *_ = src_raw.split(":", 1)
            dst_label, *_ = dst_raw.split(":", 1)
            sid, tid = label2id.get(src_label), label2id.get(dst_label)
            if not (sid and tid):
                log.warning(
                    f"Skipping connection: could not find nodes for '{src_label}' -> '{dst_label}'"
                )
                continue

            # Handle source handle
            if ":" in src_raw:
                src_handle = src_raw.split(":", 1)[1]
            elif "branch" in c.get("data", {}):
                # For condition nodes, use branch data
                branch_value = c.get("data", {}).get("branch")
                src_handle = (
                    "True"
                    if branch_value == "true"
                    else "False"
                    if branch_value == "false"
                    else "default"
                )
            else:
                src_handle = "default"

            # Handle target handle
            dst_handle = dst_raw.split(":", 1)[1] if ":" in dst_raw else "default"

            # Create arrow with data (light format doesn't include controlPointOffset)
            arrow_data = c.get("data", {})

            # Extract contentType and label from connection level
            arrow_dict = {
                "id": c.get("data", {}).get("id", f"arrow_{idx}"),
                "source": f"{sid}:{src_handle}",
                "target": f"{tid}:{dst_handle}",
                "data": arrow_data,
            }

            # Add contentType and label as direct fields if present
            if "content_type" in c:
                arrow_dict["content_type"] = c["content_type"]
            if "label" in c:
                arrow_dict["label"] = c["label"]

            arrows.append(arrow_dict)
        return arrows

    # ---- export ----------------------------------------------------------- #
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:  # noqa: D401
        id_to_label: dict[str, str] = {}
        label_counts: dict[str, int] = {}

        def _unique(base: str) -> str:
            cnt = label_counts.get(base, 0)
            label_counts[base] = cnt + 1
            return f"{base}~{cnt}" if cnt else base

        nodes_out = []
        for n in diagram.nodes:
            base = n.data.get("label") or str(n.type).split(".")[-1].title()
            label = _unique(base)
            id_to_label[n.id] = label
            node_type = str(n.type).split(".")[-1]
            node_dict = {
                "label": label,
                "type": node_type,
                "position": {"x": round(n.position.x), "y": round(n.position.y)},
            }
            props = {
                k: v
                for k, v in (n.data or {}).items()
                if k not in {"label", "position"} and v not in (None, "", {}, [])
            }
            # Map fileName back to filePath for endpoint nodes
            if node_type == "endpoint" and "file_name" in props:
                props["file_path"] = props.pop("file_name")
            if props:
                node_dict["props"] = props
            nodes_out.append(node_dict)

        connections = []
        for a in diagram.arrows:
            s_id, s_handle = (a.source.split(":") + ["default"])[:2]
            t_id, t_handle = (a.target.split(":") + ["default"])[:2]
            conn = {
                "from": f"{id_to_label[s_id]}{':' + s_handle if s_handle != 'default' else ''}",
                "to": f"{id_to_label[t_id]}{':' + t_handle if t_handle != 'default' else ''}",
            }
            # Add contentType and label from direct fields
            if a.content_type:
                conn["content_type"] = a.content_type.value
            if a.label:
                conn["label"] = a.label

            if a.data:
                # Only include essential arrow data for light format
                filtered_data = {}
                # Include arrow metadata but exclude UI-specific fields and ID
                # ID will be auto-generated during loading, just like node IDs
                for key in [
                    "type",
                    "_sourceNodeType",
                    "_isFromConditionBranch",
                    "branch",
                ]:
                    if key in a.data:
                        filtered_data[key] = a.data[key]
                # Explicitly exclude controlPointOffset fields from light format
                # These are UI presentation details that don't belong in simplified format
                if filtered_data:
                    conn["data"] = filtered_data
            connections.append(conn)

        # Add persons to the light format export
        persons_out = {}
        for p in diagram.persons:
            person_data = {
                "label": p.label,
                "service": p.llm_config.service.value
                if hasattr(p.llm_config.service, "value")
                else str(p.llm_config.service),
                "model": p.llm_config.model,
            }
            # Only include optional fields if they have values
            if p.llm_config.system_prompt:
                person_data["system_prompt"] = p.llm_config.system_prompt
            if p.llm_config.api_key_id:
                person_data["api_key_id"] = p.llm_config.api_key_id
            persons_out[p.id] = person_data

        out: dict[str, Any] = {"version": "light", "nodes": nodes_out}
        if connections:
            out["connections"] = connections
        if persons_out:
            out["persons"] = persons_out
        return out

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:  # noqa: D401
        return 0.8 if isinstance(data.get("nodes"), list) else 0.1

    def quick_match(self, content: str) -> bool:  # noqa: D401
        return "nodes:" in content and not content.lstrip().startswith(("{", "["))
