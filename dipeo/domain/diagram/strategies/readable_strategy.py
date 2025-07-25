from __future__ import annotations

import logging
import re
from typing import Any

from dipeo.models import (
    DomainDiagram,
    HandleDirection,
    HandleLabel,
    NodeID,
    create_handle_id,
    parse_handle_id,
)

from dipeo.domain.diagram.utils import (
    _node_id_map, 
    _YamlMixin, 
    build_node,
    NodeFieldMapper,
    HandleParser,
    PersonExtractor,
    ArrowDataProcessor,
    process_dotted_keys,
)
from .base_strategy import BaseConversionStrategy

log = logging.getLogger(__name__)



class ReadableYamlStrategy(_YamlMixin, BaseConversionStrategy):
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
    def _get_raw_nodes(self, data: dict[str, Any]) -> list[Any]:
        """Get nodes from readable format."""
        return data.get("nodes", [])
    
    def _process_node(self, node_data: Any, index: int) -> dict[str, Any] | None:
        """Process readable format workflow step."""
        if not isinstance(node_data, dict):
            return None
        
        step = node_data
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

        node_type = cfg.get("type") or ("start" if index == 0 else "job")
        
        # Build node data for processing
        node_dict = {
            "id": self._create_node_id(index),
            "type": node_type,
            "position": position,
            "label": clean_name,
            **{k: v for k, v in cfg.items() if k not in {"position", "type"}}
        }
        
        # Use common prop extraction
        props = self._extract_node_props(node_dict)
        
        return build_node(
            id=node_dict["id"],
            type_=node_type,
            pos=position,
            label=clean_name,
            **props,
        )
    
    def _get_node_base_props(self, node_data: dict[str, Any]) -> dict[str, Any]:
        """Get base properties for readable format."""
        # Exclude standard fields
        exclude_fields = {"id", "type", "position", "label"}
        return {k: v for k, v in node_data.items() if k not in exclude_fields}

    def extract_arrows(
            self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        arrow_counter = 0

        for flow_item in data.get("flow", []):
            if isinstance(flow_item, str):
                # Handle string format: "Start -> Ask Assistant"
                if " -> " in flow_item:
                    parts = flow_item.split(" -> ")
                    if len(parts) == 2:
                        src_label, dst_label = parts[0].strip(), parts[1].strip()
                        arrows.extend(self._parse_single_flow(src_label, dst_label, label2id, arrow_counter))
                        arrow_counter += 1
            elif isinstance(flow_item, dict):
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
                    elif isinstance(dst_data, list):
                        # Array format: {source: [dest1, dest2, ...]}
                        for dst in dst_data:
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

        # Extract content type (type)
        # Check for new format (type) or old format [type]
        if "(" in clean_dst:
            # Extract all parentheses content
            paren_matches = re.findall(r'\(([^)]+)\)', clean_dst)
            if paren_matches:
                # First parenthesis is content type if not a label
                # Check if it's a known content type
                known_types = ["raw_text", "conversation_state", "variable", "json", "object"]
                for match in paren_matches:
                    if match in known_types:
                        content_type = match
                        # Remove this specific parenthesis from clean_dst
                        clean_dst = clean_dst.replace(f"({match})", "").strip()
                        break

        # Extract label (label)
        if "(" in clean_dst and ")" in clean_dst:
            start = clean_dst.find("(")
            end = clean_dst.find(")", start)
            if start != -1 and end != -1:
                label = clean_dst[start + 1:end]
                clean_dst = clean_dst[:start].strip() + clean_dst[end + 1:].strip()

        # Parse source and target handles using shared utility
        src_id, src_handle_from_split, src_label = HandleParser.parse_label_with_handle(src.strip(), label2id)
        dst_id, dst_handle_from_split, dst_label = HandleParser.parse_label_with_handle(clean_dst.strip(), label2id)
        
        # Use parsed handles or default
        src_handle = src_handle_from_split if src_handle_from_split else "default"
        dst_handle = dst_handle_from_split if dst_handle_from_split else "default"

        if src_id and dst_id:
            # Create proper handle IDs
            source_handle_id, target_handle_id = HandleParser.create_handle_ids(
                src_id, dst_id, src_handle, dst_handle
            )
            
            # Build arrow using shared processor
            arrow_dict = ArrowDataProcessor.build_arrow_dict(
                f"arrow_{idx}",
                source_handle_id,
                target_handle_id,
                None,  # No data for readable format
                content_type,
                label
            )

            arrows.append(arrow_dict)
        else:
            log.warning(f"Could not find nodes for flow: {src_label} -> {dst_label}")

        return arrows

    # ---- export ----------------------------------------------------------- #
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:
        # Build a mapping from node ID to label (or ID if no label)
        id_to_label: dict[str, str] = {}
        for n in diagram.nodes:
            id_to_label[n.id] = n.data.get("label") or n.id

        # Build nodes section with positions
        nodes = []
        for n in diagram.nodes:
            label = id_to_label[n.id]

            # Add position to label if present
            if n.position and (n.position.x != 0 or n.position.y != 0):
                label_with_pos = f"{label} @({int(n.position.x)},{int(n.position.y)})"
            else:
                label_with_pos = label

            # Filter and map node data for export
            node_type_str = str(n.type).split(".")[-1]
            node_data = NodeFieldMapper.map_export_fields(node_type_str, n.data.copy())
            # Filter out position, label, and memory-related fields
            node_data = {
                k: v for k, v in node_data.items()
                if k not in {"label", "position", "memory_config", "memory_settings", "memory_profile"} and v not in (None, "", {}, [])
            }

            nodes.append({label_with_pos: node_data})

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

        out: dict[str, Any] = {"version": "readable"}
        if persons:
            out["persons"] = persons
        out["nodes"] = nodes
        if flow:
            out["flow"] = flow
        return out

    def _build_enhanced_flow(self, diagram: DomainDiagram, id_to_label: dict[str, str]) -> list[str]:
        """Build flow section using enhanced syntax with parallel flows and content types"""
        # Group arrows by source to detect parallel flows
        source_groups: dict[str, list] = {}

        for a in diagram.arrows:
            # Parse handle IDs using the new format
            source_id, source_handle, _ = parse_handle_id(a.source)
            
            # Use node label instead of ID for source key
            source_label = id_to_label.get(source_id, source_id)
            # Add handle suffix for non-default handles
            if source_handle.value not in ("output", "default"):
                source_key = f"{source_label}_{source_handle.value}"
            else:
                source_key = source_label

            if source_key not in source_groups:
                source_groups[source_key] = []

            target_id, target_handle, _ = parse_handle_id(a.target)

            # Build target string with handle, content type, and label
            target_str = id_to_label.get(target_id, target_id)
            if target_handle.value not in ("input", "default"):
                target_str += f"_{target_handle.value}"

            # Add content type and label annotations
            annotations = []
            if a.content_type:
                content_type_str = a.content_type.value if hasattr(a.content_type, "value") else str(a.content_type)
                annotations.append(f"({content_type_str})")
            if a.label:
                annotations.append(f"({a.label})")

            if annotations:
                target_str += " " + "".join(annotations)

            source_groups[source_key].append(target_str)

        # Generate flow dictionaries
        flow = []
        for source_key, targets in source_groups.items():
            if len(targets) == 1:
                # Single target: {source: "target"}
                flow.append({source_key: targets[0]})
            else:
                # Multiple targets: {source: [target1, target2, ...]}
                flow.append({source_key: targets})

        return flow

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:
        # Check for readable format indicators
        if data.get("format") == "readable" or data.get("version") == "readable":
            return 0.95
        # Check for readable-specific structure
        if "nodes" in data and "flow" in data:
            # Additional checks for readable format characteristics
            nodes = data.get("nodes", [])
            if isinstance(nodes, list) and nodes:
                # Check if nodes use readable format (dict with single key)
                first_node = nodes[0]
                if isinstance(first_node, dict) and len(first_node) == 1:
                    return 0.85
            return 0.7
        return 0.1

    def quick_match(self, content: str) -> bool:
        # Quick check for readable format indicators
        if "version: readable" in content or "format: readable" in content:
            return True
        # Check for readable-specific patterns
        return "nodes:" in content and "flow:" in content and "persons:" in content
    
    # ---- Domain Conversion Overrides -------------------------------------- #
    
    def _apply_format_transformations(
        self, diagram_dict: dict[str, Any], original_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply readable format specific transformations."""
        # Ensure person references in nodes match the generated person IDs
        for node_id, node_data in diagram_dict.get("nodes", {}).items():
            if "person" in node_data.get("data", {}):
                person_ref = node_data["data"]["person"]
                # If it's already in the correct format, keep it
                if not person_ref.startswith("person_"):
                    # Transform simple name to person_id format
                    node_data["data"]["person"] = f"person_{person_ref}"
        
        return diagram_dict
    
    def _extract_persons_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract persons for readable format with list structure."""
        persons_data = data.get("persons", [])
        if isinstance(persons_data, list):
            return PersonExtractor.extract_from_list(persons_data)
        return {}
