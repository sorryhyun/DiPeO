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

            # Parse position from name if present (@(x,y) syntax)
            position = {}
            clean_name = name
            if " @(" in name and name.endswith(")"):
                parts = name.split(" @(")
                if len(parts) == 2:
                    clean_name = parts[0]
                    pos_str = parts[1][:-1]  # Remove trailing )
                    try:
                        x, y = pos_str.split(",")
                        position = {"x": int(x.strip()), "y": int(y.strip())}
                    except (ValueError, IndexError):
                        # If parsing fails, ignore position
                        pass

            # Use position from name or fallback to cfg position
            if not position:
                position = cfg.get("position", {})

            node_type = cfg.get("type") or ("start" if idx == 0 else "job")
            node = build_node(
                id=f"node_{idx}",
                type_=node_type,
                pos=position,
                label=clean_name,
                **{k: v for k, v in cfg.items() if k not in {"position", "type"}},
            )
            ensure_position(node, idx)
            nodes.append(node)
        return nodes

    def extract_arrows(
            self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # noqa: D401
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        arrow_counter = 0

        for flow_item in data.get("flow", []):
            if isinstance(flow_item, dict):
                # Dictionary format: {source: destination} or {source: {dest1: null, dest2: null}}
                for src, dst_data in flow_item.items():
                    if isinstance(dst_data, str):
                        # Single destination: {source: "destination"}
                        arrows.extend(self._parse_single_flow(src, dst_data, label2id, arrow_counter))
                        arrow_counter += 1
                    elif isinstance(dst_data, dict):
                        # Multiple destinations: {source: {dest1: null, dest2: null}}
                        for dst in dst_data.keys():
                            arrows.extend(self._parse_single_flow(src, dst, label2id, arrow_counter))
                            arrow_counter += 1
                    elif dst_data is None:
                        # Handle case where dst_data is None (shouldn't happen in well-formed data)
                        continue
        return arrows

    def _parse_single_flow(self, src: str, dst: str | bool | int, label2id: dict[str, str], idx: int) -> list[
        dict[str, Any]]:
        """Parse a single flow connection with optional content type and label"""
        arrows = []

        # Convert non-string dst to string (handles boolean keys like True/False)
        dst_str = str(dst)

        # Parse content type [type] and label (label) from destination
        content_type = None
        label = None
        clean_dst = dst_str.strip()

        # Extract content type [type]
        if "[" in clean_dst and "]" in clean_dst:
            start = clean_dst.find("[")
            end = clean_dst.find("]", start)
            if start != -1 and end != -1:
                content_type = clean_dst[start + 1:end]
                clean_dst = clean_dst[:start].strip() + clean_dst[end + 1:].strip()

        # Extract label (label)
        if "(" in clean_dst and ")" in clean_dst:
            start = clean_dst.find("(")
            end = clean_dst.find(")", start)
            if start != -1 and end != -1:
                label = clean_dst[start + 1:end]
                clean_dst = clean_dst[:start].strip() + clean_dst[end + 1:].strip()

        # Parse source and target handles
        src_parts = src.split(":")
        dst_parts = clean_dst.split(":")

        src_label = src_parts[0].strip()
        src_handle = src_parts[1].strip() if len(src_parts) > 1 else "output"

        dst_label = dst_parts[0].strip()
        dst_handle = dst_parts[1].strip() if len(dst_parts) > 1 else "input"

        # Get node IDs
        sid = label2id.get(src_label)
        tid = label2id.get(dst_label)

        if sid and tid:
            arrow_dict = {
                "id": f"arrow_{idx}",
                "source": f"{sid}:{src_handle}",
                "target": f"{tid}:{dst_handle}",
            }

            # Add content type and label if present
            if content_type:
                arrow_dict["content_type"] = content_type
            if label:
                arrow_dict["label"] = label

            arrows.append(arrow_dict)
        else:
            log.warning(f"Could not find nodes for flow: {src_label} -> {dst_label}")

        return arrows

    # ---- export ----------------------------------------------------------- #
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:  # noqa: D401
        # Build a mapping from node ID to label (or ID if no label)
        id_to_label: dict[str, str] = {}
        for n in diagram.nodes:
            id_to_label[n.id] = n.data.get("label") or n.id

        # Build workflow section with positions
        workflow = []
        for n in diagram.nodes:
            label = id_to_label[n.id]

            # Add position to label if present
            if n.position and (n.position.x != 0 or n.position.y != 0):
                label_with_pos = f"{label} @({int(n.position.x)},{int(n.position.y)})"
            else:
                label_with_pos = label

            # Filter out position and label from data
            node_data = {
                k: v for k, v in n.data.items()
                if k not in {"label", "position"} and v not in (None, "", {}, [])
            }

            workflow.append({label_with_pos: node_data})

        # Build flow section with enhanced syntax
        flow = self._build_enhanced_flow(diagram, id_to_label)

        # Build persons section
        persons = []
        for p in diagram.persons:
            person_dict = {
                p.label: {
                    "service": p.llm_config.service.value if hasattr(p.llm_config.service, "value") else str(
                        p.llm_config.service),
                    "model": p.llm_config.model,
                }
            }
            # Only include optional fields if they have values
            if p.llm_config.system_prompt:
                person_dict[p.label]["system_prompt"] = p.llm_config.system_prompt
            if p.llm_config.api_key_id:
                person_dict[p.label]["api_key_id"] = p.llm_config.api_key_id
            persons.append(person_dict)

        out: dict[str, Any] = {}
        if persons:
            out["persons"] = persons
        out["workflow"] = workflow
        if flow:
            out["flow"] = flow
        return out

    def _build_enhanced_flow(self, diagram: DomainDiagram, id_to_label: dict[str, str]) -> list[str]:
        """Build flow section using enhanced syntax with parallel flows and content types"""
        # Group arrows by source to detect parallel flows
        source_groups: dict[str, list] = {}

        for a in diagram.arrows:
            source_id = a.source.split(':')[0]
            source_handle = a.source.split(':', 1)[1] if ':' in a.source else "output"
            source_key = f"{source_id}:{source_handle}" if source_handle not in ("output", "default") else source_id

            if source_key not in source_groups:
                source_groups[source_key] = []

            target_id = a.target.split(':')[0]
            target_handle = a.target.split(':', 1)[1] if ':' in a.target else "input"

            # Build target string with handle, content type, and label
            target_str = id_to_label.get(target_id, target_id)
            if target_handle not in ("input", "default"):
                target_str += f":{target_handle}"

            # Add content type and label annotations
            annotations = []
            if a.content_type:
                content_type_str = a.content_type.value if hasattr(a.content_type, "value") else str(a.content_type)
                annotations.append(f"[{content_type_str}]")
            if a.label:
                annotations.append(f"({a.label})")

            if annotations:
                target_str += " " + "".join(annotations)

            source_groups[source_key].append(target_str)

        # Generate flow dictionaries
        flow = []
        for source_key, targets in source_groups.items():
            source_id = source_key.split(':')[0]
            source_handle = source_key.split(':', 1)[1] if ':' in source_key else None

            source_str = id_to_label.get(source_id, source_id)
            if source_handle and source_handle not in ("output", "default"):
                source_str += f":{source_handle}"

            if len(targets) == 1:
                # Single target: {source: "target"}
                flow.append({source_str: targets[0]})
            else:
                # Multiple targets: {source: {target1: null, target2: null}}
                targets_dict = {target: None for target in targets}
                flow.append({source_str: targets_dict})

        return flow

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:  # noqa: D401
        return 0.9 if "workflow" in data else 0.1

    def quick_match(self, content: str) -> bool:  # noqa: D401
        return "workflow:" in content and "flow:" in content
