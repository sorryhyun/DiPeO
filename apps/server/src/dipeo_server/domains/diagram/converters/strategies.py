"""Compact format strategies for the unified diagram converter."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import yaml
from dipeo_domain import DomainDiagram, DomainNode

from .base import FormatStrategy
from .shared_components import (
    NodeTypeMapper,
    build_node,
    coerce_to_dict,
    ensure_position,
    extract_common_arrows,
)

log = logging.getLogger(__name__)


#                               helper mixins                                 #


class _JsonMixin:
    """Shared JSON helpers."""

    # NOTE: overriding instance methods via mixin
    def parse(self, content: str) -> Dict[str, Any]:  # type: ignore[override]
        try:
            return json.loads(content)
        except json.JSONDecodeError as err:
            log.error("JSON parse error: %s", err)
            raise ValueError(f"Invalid JSON: {err}") from err

    def format(self, data: Dict[str, Any]) -> str:  # type: ignore[override]
        return json.dumps(data, indent=2, ensure_ascii=False)


class _YamlMixin:
    """Shared YAML helpers."""

    def parse(self, content: str) -> Dict[str, Any]:  # type: ignore[override]
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as err:
            log.error("YAML parse error: %s", err)
            raise ValueError(f"Invalid YAML: {err}") from err

    def format(self, data: Dict[str, Any]) -> str:  # type: ignore[override]
        return yaml.dump(
            data, default_flow_style=False, sort_keys=False, allow_unicode=True
        )


#                               common helpers                                #
def _node_id_map(nodes: List[Dict[str, Any]]) -> Dict[str, str]:
    """Return mapping label → node-id from already built nodes list."""
    m: Dict[str, str] = {}
    for n in nodes:
        label = n.get("data", {}).get("label", n["id"])
        m[label] = n["id"]
    return m


def _round_pos(position: Dict[str, Any]) -> Dict[str, int]:
    return {"x": round(position.get("x", 0)), "y": round(position.get("y", 0))}


#  #
#                               JSON strategy                                 #
#  #
class NativeJsonStrategy(_JsonMixin, FormatStrategy):
    """Native / domain JSON format."""

    # ---- minimal metadata ----
    format_id = "native"
    format_info = {
        "name": "Domain JSON",
        "description": "Canonical format for diagram structure and execution",
        "extension": ".json",
        "supports_import": True,
        "supports_export": True,
    }

    # ---- extraction helpers ----
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes_data = coerce_to_dict(data.get("nodes", []), id_key="id", prefix="node")
        built: List[Dict[str, Any]] = []
        for idx, (nid, ndata) in enumerate(nodes_data.items()):
            node = build_node(
                id=nid,
                type_=ndata.get("type", "unknown"),
                pos=ndata.get("position", {}),
                **ndata.get("data", {}),
            )
            ensure_position(node, idx)
            built.append(node)
        return built

    def extract_arrows(
        self, data: Dict[str, Any], _nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return extract_common_arrows(data.get("arrows", []))

    # ---- export helpers ----
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        return {
            "nodes": {
                n.id: {
                    "type": n.type,
                    "position": getattr(n, "position", {}),
                    "data": n.data,
                }
                for n in diagram.nodes
            },
            "handles": {
                h.id: {
                    "nodeId": h.node_id,
                    "label": h.label,
                    "direction": h.direction,
                    "dataType": h.data_type,
                    "position": h.position,
                }
                for h in diagram.handles
            },
            "arrows": {
                a.id: {"source": a.source, "target": a.target, "data": a.data}
                for a in diagram.arrows
            },
            "persons": {p.id: p.model_dump(by_alias=True) for p in diagram.persons},
            "api_keys": {k.id: k.model_dump(by_alias=True) for k in diagram.api_keys},
            "metadata": diagram.metadata.model_dump(by_alias=True)
            if diagram.metadata
            else None,
        }

    # ---- heuristics ----
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        nodes = data.get("nodes")
        if isinstance(nodes, dict) and all(k in data for k in ("handles", "arrows")):
            return 0.95
        if isinstance(nodes, list):
            return 0.9
        if nodes:
            return 0.5
        return 0.1

    def quick_match(self, content: str) -> bool:
        return content.lstrip().startswith("{") and any(
            key in content for key in ('"nodes"', '"handles"', '"arrows"')
        )


#  #
#                                Light YAML                                   #
#  #
class LightYamlStrategy(_YamlMixin, FormatStrategy):
    """Light YAML format (labels instead of IDs)."""

    format_id = "light"
    format_info = {
        "name": "Light YAML",
        "description": "Simplified format using labels instead of IDs",
        "extension": ".light.yaml",
        "supports_import": True,
        "supports_export": True,
    }

    # ---- extraction helpers ----
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        for idx, ndata in enumerate(data.get("nodes", [])):
            if not isinstance(ndata, dict):
                continue

            # Extract base properties
            node_props = {
                k: v
                for k, v in ndata.items()
                if k not in {"type", "label", "id", "position", "arrows", "props"}
            }

            # Flatten props if they exist
            if "props" in ndata and isinstance(ndata["props"], dict):
                node_props.update(ndata["props"])

            node = build_node(
                id=ndata.get("label", f"node_{idx}"),
                type_=ndata.get("type", "unknown"),
                pos=ndata.get("position", {}),
                label=ndata.get("label"),
                **node_props,
            )
            ensure_position(node, idx)
            nodes.append(node)
        return nodes

    def extract_arrows(
        self, data: Dict[str, Any], nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        arrows: List[Dict[str, Any]] = []
        label2id = _node_id_map(nodes)

        for idx, conn in enumerate(data.get("connections", [])):
            if not isinstance(conn, dict):
                continue

            # Extract label and handle from "from" and "to" fields
            from_str = conn.get("from", "")
            to_str = conn.get("to", "")

            # Parse label:handle format
            from_parts = from_str.split(":", 1)
            to_parts = to_str.split(":", 1)

            from_label = from_parts[0]
            to_label = to_parts[0]

            # Get handle names (default if not specified)
            from_handle = (
                from_parts[1] if len(from_parts) > 1 else conn.get("branch", "default")
            )
            to_handle = to_parts[1] if len(to_parts) > 1 else "default"

            sid = label2id.get(from_label)
            tid = label2id.get(to_label)
            if not (sid and tid):
                continue

            # Generate a unique arrow ID based on index
            arrow_id = f"arrow_{idx}"

            # Copy data but exclude the ID field since we're generating a new one
            arrow_data = {}
            if conn.get("data"):
                arrow_data = {k: v for k, v in conn["data"].items() if k != "id"}

            arrows.append(
                {
                    "id": arrow_id,
                    "source": f"{sid}:{from_handle}",
                    "target": f"{tid}:{to_handle}",
                    "data": arrow_data,
                }
            )
        return arrows

    # ---- export ----
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        # Create person ID to label mapping
        person_id_to_label: Dict[str, str] = {}
        if diagram.persons:
            for person in diagram.persons:
                person_id_to_label[person.id] = person.label

        nodes_out: List[Dict[str, Any]] = []
        label_counts: Dict[str, int] = {}
        id2label: Dict[str, str] = {}

        for n in diagram.nodes:
            # Fix label extraction - ensure we get the actual label from data
            base = n.data.get("label") if n.data else None
            if (
                not base or base == n.type or base == str(n.type).split(".")[-1]
            ):  # Also check if label is just the type name
                # Use a better default based on node type
                type_name = str(n.type).split(".")[-1]
                if type_name == "start":
                    base = "Start"
                elif type_name == "endpoint":
                    base = "End"
                elif type_name == "db":
                    base = "Database"
                elif type_name == "condition":
                    base = "Condition"
                elif type_name == "person_job":
                    base = "Task"
                else:
                    base = type_name.replace("_", " ").title()

            suffix = label_counts.get(base, 0)
            label_counts[base] = suffix + 1
            label = f"{base}~{suffix}" if suffix else base
            id2label[n.id] = label

            # Build the node output
            node_output: Dict[str, Any] = {
                "label": label,
                "type": str(n.type).split(".")[
                    -1
                ],  # Convert enum to string, just the value
                "position": _round_pos(
                    n.position.model_dump()
                    if hasattr(n.position, "model_dump")
                    else n.position
                ),
            }

            # Add person field for person_job nodes
            if n.type == "person_job" and n.data:
                person_id = n.data.get("personId")
                if person_id and person_id in person_id_to_label:
                    node_output["person"] = person_id_to_label[person_id]

            # Filter props to exclude unnecessary fields
            if n.data:
                filtered_props = {}
                exclude_fields = {
                    "label",
                    "type",
                    "position",
                    "personId",
                    "_handles",
                    "inputs",
                    "outputs",
                    "id",
                    "nodeId",
                    "__typename",
                    "flipped",
                }

                for k, v in n.data.items():
                    if k not in exclude_fields:
                        # Only include meaningful values
                        if v is not None and v != "" and v != {} and v != []:
                            filtered_props[k] = v

                if filtered_props:
                    node_output["props"] = filtered_props

            nodes_out.append(node_output)

        connections = []
        for a in diagram.arrows:
            # Extract node IDs and handle names
            source_parts = a.source.split(":")
            target_parts = a.target.split(":")
            sid = source_parts[0]
            tid = target_parts[0]
            from_handle = source_parts[1] if len(source_parts) > 1 else "default"
            to_handle = target_parts[1] if len(target_parts) > 1 else "default"

            # Build connection data with handle notation
            from_label = id2label[sid]
            to_label = id2label[tid]

            # Append handle to label if not default
            if from_handle != "default":
                from_label = f"{from_label}:{from_handle}"
            if to_handle != "default":
                to_label = f"{to_label}:{to_handle}"

            conn_data = {
                "from": from_label,
                "to": to_label,
            }

            # For condition branches, we still keep the branch field for clarity
            if from_handle in ["True", "False"]:
                conn_data["branch"] = from_handle

            # Add data but exclude internal/UI fields
            if a.data:
                # Fields to exclude from light yaml format
                exclude_fields = {
                    "id",
                    "type",
                    "_sourceNodeType",
                    "_isFromConditionBranch",
                    "controlPointOffsetX",
                    "controlPointOffsetY",
                }
                # Only keep semantic fields like "label", "contentType", etc.
                filtered_data = {
                    k: v for k, v in a.data.items() if k not in exclude_fields
                }
                if (
                    filtered_data
                ):  # Only add data if there's something left after filtering
                    conn_data["data"] = filtered_data

            connections.append(conn_data)

        out: Dict[str, Any] = {"version": "light", "nodes": nodes_out}
        if connections:
            out["connections"] = connections
        if diagram.persons:
            # Convert persons to dict keyed by label
            persons_dict = {}
            for p in diagram.persons:
                person_dict = p.model_dump()
                # Convert enum values to strings (just the value, not the full enum name)
                if "service" in person_dict:
                    person_dict["service"] = str(person_dict["service"]).split(".")[-1]
                if "forgetting_mode" in person_dict:
                    person_dict["forgetting_mode"] = str(
                        person_dict["forgetting_mode"]
                    ).split(".")[-1]
                # Remove unnecessary fields including 'id' and 'label' (since label is the key)
                for field in ["id", "label", "type", "__typename", "masked_api_key"]:
                    person_dict.pop(field, None)
                # Use label as the key
                persons_dict[p.label] = person_dict
            out["persons"] = persons_dict
        if getattr(diagram, "name", None):
            out["name"] = diagram.name
        return out

    # ---- heuristics ----
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        if isinstance(data.get("nodes"), list):
            return (
                0.8
                if any("label" in n for n in data["nodes"] if isinstance(n, dict))
                else 0.5
            )
        return 0.1

    def quick_match(self, content: str) -> bool:
        stripped = content.lstrip()
        return not stripped.startswith(("{", "[")) and "nodes:" in content


#  #
#                              Readable YAML                                  #
#  #
class ReadableYamlStrategy(_YamlMixin, FormatStrategy):
    """Human-friendly “workflow” YAML."""

    format_id = "readable"
    format_info = {
        "name": "Readable Workflow",
        "description": "Human-friendly workflow format",
        "extension": ".readable.yaml",
        "supports_import": True,
        "supports_export": True,
    }

    def __init__(self) -> None:
        self._mapper = NodeTypeMapper()

    # ---- extraction ----
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        for idx, step in enumerate(data.get("workflow", [])):
            if not isinstance(step, dict):
                continue
            ((name, cfg),) = step.items()  # exactly one kv-pair
            node = build_node(
                id=name,
                type_=self._mapper.determine_node_type(cfg).value,
                pos=cfg.get("position", {}),
                label=name,
                **self._extract_props(cfg),
            )
            ensure_position(node, idx)
            nodes.append(node)
        return nodes

    def extract_arrows(
        self, data: Dict[str, Any], nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        node_ids = {n["id"] for n in nodes}
        arrows: List[Dict[str, Any]] = []
        for line in data.get("flow", []):
            if isinstance(line, str) and "->" in line:
                src, dst = (x.strip() for x in line.split("->", 1))
                if src in node_ids and dst in node_ids:
                    arrows.append({"source": f"{src}_output", "target": f"{dst}_input"})
        return arrows

    # ---- export ----
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        workflow = [
            {(n.data.get("label") or n.id): self._step_from_node(n)}
            for n in diagram.nodes
        ]
        flow = [
            f"{a.source.split(':')[0]} -> {a.target.split(':')[0]}"
            for a in diagram.arrows
        ]
        result: Dict[str, Any] = {"workflow": workflow}
        if flow:
            result["flow"] = flow

        cfg: Dict[str, Any] = {}
        if diagram.persons:
            persons_list = []
            for p in diagram.persons:
                person_dict = p.model_dump()
                # Convert enum values to strings
                if "service" in person_dict:
                    person_dict["service"] = str(person_dict["service"]).split(".")[-1]
                if "forgetting_mode" in person_dict:
                    person_dict["forgetting_mode"] = str(person_dict["forgetting_mode"]).split(".")[-1]
                # Remove masked_api_key from readable format
                person_dict.pop("masked_api_key", None)
                persons_list.append(person_dict)
            cfg["persons"] = persons_list
        if diagram.api_keys:
            api_keys_list = []
            for k in diagram.api_keys:
                key_dict = k.model_dump()
                # Convert service enum to string
                if "service" in key_dict:
                    key_dict["service"] = str(key_dict["service"]).split(".")[-1]
                # Remove masked_key from readable format
                key_dict.pop("masked_key", None)
                api_keys_list.append(key_dict)
            cfg["api_keys"] = api_keys_list
        if cfg:
            result["config"] = cfg
        return result

    # ---- heuristics ----
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        wk, fl = data.get("workflow"), data.get("flow")
        if isinstance(wk, list):
            return 0.9 if isinstance(fl, list) else 0.6
        return 0.1

    def quick_match(self, content: str) -> bool:
        return "workflow:" in content and (" -> " in content or "flow:" in content)

    # ---- internal helpers ----
    @staticmethod
    def _extract_props(cfg: Dict[str, Any]) -> Dict[str, Any]:
        mapping = {
            "prompt": "prompt",
            "person": "personId",
            "model": "model",
            "code": "code",
            "language": "language",
            "condition": "expression",
            "data": "data",
        }
        return {dst: cfg[src] for src, dst in mapping.items() if src in cfg}

    @staticmethod
    def _step_from_node(node: DomainNode) -> Dict[str, Any]:
        t = node.type
        d = node.data
        if t == "person_job":
            return {k: d[k] for k in ("prompt", "personId") if k in d}
        if t == "job":
            return {k: d[k] for k in ("code", "language") if k in d}
        if t == "condition":
            return {"condition": d.get("expression")}
        if t == "start":
            return {"data": d.get("data")}
        if t == "user_response":
            return {"prompt": d.get("prompt")}
        return {}
