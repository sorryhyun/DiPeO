"""Compact format strategies for the unified diagram converter.

This rewritten version trims boiler‑plate by sharing helpers and leaving only
format‑specific logic in each concrete strategy, reducing the file size and
cognitive load while preserving the public API expected by the rest of the
package (NativeJsonStrategy / LightYamlStrategy / ReadableYamlStrategy).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

import yaml
from dipeo_domain import DomainDiagram
from pydantic import BaseModel

from .base import FormatStrategy
from .shared_components import (
    build_node,
    coerce_to_dict,
    ensure_position,
    extract_common_arrows,
)

log = logging.getLogger(__name__)

from .conversion_utils import _JsonMixin, _YamlMixin, _node_id_map


class _BaseStrategy(FormatStrategy):
    """Common scaffolding – subclasses only override what they need."""

    # Concrete classes must define `format_id` and `format_info`.

    # --- stubs that *may* be overridden ------------------------------------ #
    def extract_arrows(
        self, data: dict[str, Any], _nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return extract_common_arrows(data.get("arrows", []))

    def detect_confidence(self, _data: dict[str, Any]) -> float:
        return 0.5

    def quick_match(self, _content: str) -> bool:  # noqa: D401 (one‑line doc)
        return False


# strategies


class NativeJsonStrategy(_JsonMixin, _BaseStrategy):
    """Canonical domain JSON."""

    format_id = "native"
    format_info = {
        "name": "Domain JSON",
        "description": "Canonical format for diagram structure and execution",
        "extension": ".json",
        "supports_import": True,
        "supports_export": True,
    }

    # ---- extraction ------------------------------------------------------- #
    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:  # noqa: D401
        built: list[dict[str, Any]] = []
        for idx, (nid, ndata) in enumerate(
            coerce_to_dict(data.get("nodes", {})).items()
        ):
            node = build_node(
                id=nid,
                type_=ndata.get("type", "job"),
                pos=ndata.get("position", {}),
                **ndata.get("data", {}),
            )
            ensure_position(node, idx)
            built.append(node)
        return built

    # ---- export ----------------------------------------------------------- #
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:  # noqa: D401
        return {
            "nodes": {
                n.id: {
                    "type": n.type,
                    "position": n.position.model_dump(),
                    "data": n.data,
                }
                for n in diagram.nodes
            },
            "handles": {h.id: h.model_dump(by_alias=True) for h in diagram.handles},
            "arrows": {
                a.id: {
                    "source": a.source, 
                    "target": a.target, 
                    "data": a.data,
                    **({
                        "content_type": a.content_type.value if hasattr(a.content_type, "value") else str(a.content_type)
                    } if a.content_type else {}),
                    **({
                        "label": a.label
                    } if a.label else {})
                }
                for a in diagram.arrows
            },
            "persons": {p.id: p.model_dump(by_alias=True) for p in diagram.persons},
            "metadata": diagram.metadata.model_dump(by_alias=True)
            if diagram.metadata
            else None,
        }

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:  # noqa: D401
        return 0.95 if {"nodes", "arrows"}.issubset(data) else 0.1

    def quick_match(self, content: str) -> bool:  # noqa: D401
        return content.lstrip().startswith("{") and '"nodes"' in content


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


class ReadableYamlStrategy(_YamlMixin, _BaseStrategy):
    """Human‑friendly workflow YAML."""

    format_id = "readable"
    format_info = {
        "name": "Readable Workflow",
        "description": "Human‑friendly workflow format",
        "extension": ".readable.yaml",
        "supports_import": True,
        "supports_export": True,
    }

    # ---- extraction ------------------------------------------------------- #
    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:  # noqa: D401
        nodes: list[dict[str, Any]] = []
        for idx, step in enumerate(data.get("workflow", [])):
            if not isinstance(step, dict):
                continue
            ((name, cfg),) = step.items()
            node_type = cfg.get("type") or ("start" if idx == 0 else "job")
            node = build_node(
                id=f"node_{idx}",
                type_=node_type,
                pos=cfg.get("position", {}),
                label=name,
                **{k: v for k, v in cfg.items() if k != "position"},
            )
            ensure_position(node, idx)
            nodes.append(node)
        return nodes

    def extract_arrows(
        self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # noqa: D401
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        for idx, line in enumerate(data.get("flow", [])):
            if isinstance(line, str) and "->" in line:
                src, dst = (s.strip() for s in line.split("->", 1))
                sid, tid = label2id.get(src), label2id.get(dst)
                if sid and tid:
                    arrows.append(
                        {
                            "id": f"arrow_{idx}",
                            "source": f"{sid}:output",
                            "target": f"{tid}:input",
                        }
                    )
        return arrows

    # ---- export ----------------------------------------------------------- #
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:  # noqa: D401
        # Build a mapping from node ID to label (or ID if no label)
        id_to_label: dict[str, str] = {}
        for n in diagram.nodes:
            id_to_label[n.id] = n.data.get("label") or n.id
        
        workflow = [
            {
                id_to_label[n.id]: {
                    k: v for k, v in n.data.items() if k not in {"label", "position"}
                }
            }
            for n in diagram.nodes
        ]
        
        # Use labels in flow section too
        flow = []
        for a in diagram.arrows:
            source_id = a.source.split(':')[0]
            target_id = a.target.split(':')[0]
            source_label = id_to_label.get(source_id, source_id)
            target_label = id_to_label.get(target_id, target_id)
            flow.append(f"{source_label} -> {target_label}")
        
        out: dict[str, Any] = {"workflow": workflow}
        if flow:
            out["flow"] = flow
        return out

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:  # noqa: D401
        return 0.9 if "workflow" in data else 0.1

    def quick_match(self, content: str) -> bool:  # noqa: D401
        return "workflow:" in content and "->" in content
