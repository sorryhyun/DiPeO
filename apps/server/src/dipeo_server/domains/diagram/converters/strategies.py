"""Compact format strategies for the unified diagram converter."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Tuple

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
        nodes_data = coerce_to_dict(data.get("nodes", {}), id_key="id", prefix="node")
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
        return extract_common_arrows(data.get("arrows", {}))

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
            "persons": {p.id: p.model_dump() for p in diagram.persons},
            "api_keys": {k.id: k.model_dump() for k in diagram.api_keys},
            "metadata": diagram.metadata.model_dump() if diagram.metadata else None,
        }

    # ---- heuristics ----
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        nodes = data.get("nodes")
        if isinstance(nodes, dict) and all(
            k in data for k in ("handles", "arrows")
        ):
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
            node = build_node(
                id=ndata.get("label", f"node_{idx}"),
                type_=ndata.get("type", "unknown"),
                pos=ndata.get("position", {}),
                label=ndata.get("label"),
                **{
                    k: v
                    for k, v in ndata.items()
                    if k not in {"type", "label", "id", "position", "arrows"}
                },
            )
            ensure_position(node, idx)
            nodes.append(node)
        return nodes

    def extract_arrows(
        self, data: Dict[str, Any], nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        arrows: List[Dict[str, Any]] = []
        label2id = _node_id_map(nodes)

        for conn in data.get("connections", []):
            if not isinstance(conn, dict):
                continue
            sid, tid = label2id.get(conn.get("from")), label2id.get(conn.get("to"))
            if not (sid and tid):
                continue
            arrows.append(
                {
                    "id": conn.get("data", {}).get("id", f"arrow_{len(arrows)}"),
                    "source": f"{sid}:{conn.get('branch', 'default')}",
                    "target": f"{tid}:default",
                    "data": conn.get("data", {}),
                }
            )
        return arrows

    # ---- export ----
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        nodes_out: List[Dict[str, Any]] = []
        label_counts: Dict[str, int] = {}
        id2label: Dict[str, str] = {}

        for n in diagram.nodes:
            base = n.data.get("label", n.id)
            suffix = label_counts.get(base, 0)
            label_counts[base] = suffix + 1
            label = f"{base}~{suffix}" if suffix else base
            id2label[n.id] = label

            nodes_out.append(
                {
                    "label": label,
                    "type": n.type,
                    "position": _round_pos(getattr(n, "position", {})),
                    "props": {
                        k: v
                        for k, v in n.data.items()
                        if k not in {"label", "type", "position"}
                    },
                }
            )

        connections = []
        for a in diagram.arrows:
            sid, tid = (part.split(":")[0] for part in (a.source, a.target))
            connections.append(
                {
                    "from": id2label[sid],
                    "to": id2label[tid],
                    **({"branch": a.source.split(":")[1]} if ":" in a.source else {}),
                    **({"data": a.data} if a.data else {}),
                }
            )

        out: Dict[str, Any] = {"version": "light", "nodes": nodes_out}
        if connections:
            out["connections"] = connections
        if diagram.persons:
            out["persons"] = [p.model_dump() for p in diagram.persons]
        if getattr(diagram, "name", None):
            out["name"] = diagram.name
        return out

    # ---- heuristics ----
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        if isinstance(data.get("nodes"), list):
            return 0.8 if any("label" in n for n in data["nodes"] if isinstance(n, dict)) else 0.5
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
            (name, cfg), = step.items()  # exactly one kv-pair
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
                    arrows.append(
                        {"source": f"{src}_output", "target": f"{dst}_input"}
                    )
        return arrows

    # ---- export ----
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        workflow = [
            {
                (n.data.get("label") or n.id): self._step_from_node(n)
            }
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
            cfg["persons"] = [p.model_dump() for p in diagram.persons]
        if diagram.api_keys:
            cfg["api_keys"] = [k.model_dump() for k in diagram.api_keys]
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
