from __future__ import annotations

import logging
from typing import Any

from dipeo.models import (
    DomainDiagram,
    HandleDirection,
    HandleLabel,
    NodeID,
    create_handle_id,
    parse_handle_id,
)

from ..conversion_utils import _node_id_map, _YamlMixin
from ..shared_components import build_node
from .base_strategy import BaseConversionStrategy

log = logging.getLogger(__name__)



class LightYamlStrategy(_YamlMixin, BaseConversionStrategy):
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
    def _get_raw_nodes(self, data: dict[str, Any]) -> list[Any]:
        """Get nodes from light format (list of dicts)."""
        return data.get("nodes", [])
    
    def _process_node(self, node_data: Any, index: int) -> dict[str, Any] | None:
        """Process light format node data."""
        if not isinstance(node_data, dict):
            return None
        
        n = node_data
        props = {
            **n.get("props", {}),
            **{
                k: v
                for k, v in n.items()
                if k not in {"label", "type", "position", "props"}
            },
        }
        
        # Handle dot notation keys (e.g., "memory_config.forget_mode")
        dotted_keys = [k for k in props if '.' in k]
        for key in dotted_keys:
            value = props.pop(key)
            parts = key.split('.')
            current = props
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value


        # Add required fields for specific node types
        node_type = n.get("type", "job")
        if node_type == "start":
            # Add default values for required fields
            props.setdefault("custom_data", {})
            props.setdefault("output_data_structure", {})
        elif node_type == "endpoint":
            # Map file_path to file_name for endpoint nodes
            if "file_path" in props and "file_name" not in props:
                props["file_name"] = props.pop("file_path")
        elif node_type == "job":
            # Legacy job node - map to code_job for backward compatibility
            if "code" in props:
                node_type = "code_job"
                # Map code_type to language
                if "code_type" in props:
                    props["language"] = props.pop("code_type")
        elif node_type == "code_job":
            # Ensure language field exists
            if "code_type" in props and "language" not in props:
                props["language"] = props.pop("code_type")
        elif node_type == "db":
            # Map source_details to file for DB nodes
            if "source_details" in props and "file" not in props:
                props["file"] = props.pop("source_details")

        return build_node(
            id=self._create_node_id(index),
            type_=node_type,
            pos=n.get("position", {}),
            label=n.get("label"),
            **props,
        )

    def extract_arrows(
            self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        for idx, c in enumerate(data.get("connections", [])):
            if not isinstance(c, dict):
                continue
            src_raw, dst_raw = c.get("from", ""), c.get("to", "")
            
            # Parse source label and handle
            src_label = src_raw
            src_handle_from_split = None
            
            # First check if the entire string is a valid node label
            if src_raw not in label2id and "_" in src_raw:
                # Try to find the node label by checking all possible splits
                # This handles cases where node labels contain spaces or underscores
                # We need to find the longest matching label in label2id
                parts = src_raw.split("_")
                
                # Also check for labels with spaces by replacing underscores
                for i in range(len(parts) - 1, 0, -1):
                    # Try with underscores
                    potential_label = "_".join(parts[:i])
                    if potential_label in label2id:
                        src_label = potential_label
                        src_handle_from_split = "_".join(parts[i:])
                        break
                    
                    # Try with spaces instead of underscores
                    potential_label_with_spaces = " ".join(parts[:i])
                    if potential_label_with_spaces in label2id:
                        src_label = potential_label_with_spaces
                        src_handle_from_split = "_".join(parts[i:])
                        break
            
            # Parse destination label and handle
            dst_label = dst_raw
            dst_handle_from_split = None
            
            # First check if the entire string is a valid node label
            if dst_raw not in label2id and "_" in dst_raw:
                # Try to find the node label by checking all possible splits
                parts = dst_raw.split("_")
                
                # Also check for labels with spaces by replacing underscores
                for i in range(len(parts) - 1, 0, -1):
                    # Try with underscores
                    potential_label = "_".join(parts[:i])
                    if potential_label in label2id:
                        dst_label = potential_label
                        dst_handle_from_split = "_".join(parts[i:])
                        break
                    
                    # Try with spaces instead of underscores
                    potential_label_with_spaces = " ".join(parts[:i])
                    if potential_label_with_spaces in label2id:
                        dst_label = potential_label_with_spaces
                        dst_handle_from_split = "_".join(parts[i:])
                        break
                    
            sid, tid = label2id.get(src_label), label2id.get(dst_label)
            if not (sid and tid):
                log.warning(
                    f"Skipping connection: could not find nodes for '{src_label}' -> '{dst_label}'"
                )
                continue

            # Handle source handle
            if src_handle_from_split:
                src_handle = src_handle_from_split
            elif "branch" in c.get("data", {}):
                # For condition nodes, use branch data
                branch_value = c.get("data", {}).get("branch")
                src_handle = (
                    "condtrue"
                    if branch_value == "true"
                    else "condfalse"
                    if branch_value == "false"
                    else "default"
                )
            else:
                src_handle = "default"

            # Handle target handle
            if dst_handle_from_split:
                # Convert "_first" to "first" for proper HandleLabel enum mapping
                if dst_handle_from_split == "_first":
                    dst_handle = "first"
                else:
                    dst_handle = dst_handle_from_split
            else:
                dst_handle = "default"

            # Create arrow with data (light format doesn't include controlPointOffset)
            arrow_data = c.get("data", {}).copy() if c.get("data") else {}
            
            # Add branch data if this is from a condition handle and not already present
            if src_handle in ["condtrue", "condfalse"] and "branch" not in arrow_data:
                arrow_data["branch"] = "true" if src_handle == "condtrue" else "false"

            # Create proper handle IDs
            # Convert string handle labels to HandleLabel enum
            try:
                src_handle_enum = HandleLabel(src_handle)
            except ValueError:
                src_handle_enum = HandleLabel.default
                
            try:
                dst_handle_enum = HandleLabel(dst_handle)
            except ValueError:
                dst_handle_enum = HandleLabel.default
                
            source_handle_id = create_handle_id(NodeID(sid), src_handle_enum, HandleDirection.output)
            target_handle_id = create_handle_id(NodeID(tid), dst_handle_enum, HandleDirection.input)

            # Extract contentType and label from connection level
            arrow_dict = {
                "id": c.get("data", {}).get("id", f"arrow_{idx}"),
                "source": source_handle_id,
                "target": target_handle_id,
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
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:
        id_to_label: dict[str, str] = {}
        label_counts: dict[str, int] = {}
        
        # Create person ID to label mapping
        person_id_to_label: dict[str, str] = {}
        for p in diagram.persons:
            person_id_to_label[p.id] = p.label

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
            
            # Replace person ID with person label for person_job nodes
            if node_type == "person_job" and "person" in props:
                person_id = props["person"]
                if person_id in person_id_to_label:
                    props["person"] = person_id_to_label[person_id]
            
            # Map fileName back to filePath for endpoint nodes
            if node_type == "endpoint" and "file_name" in props:
                props["file_path"] = props.pop("file_name")
            # Map language back to code_type for code_job nodes (for backward compatibility)
            elif node_type == "code_job" and "language" in props:
                props["code_type"] = props.pop("language")
            # Map file back to source_details for DB nodes
            elif node_type == "db" and "file" in props:
                props["source_details"] = props.pop("file")
            if props:
                node_dict["props"] = props
            nodes_out.append(node_dict)

        connections = []
        for a in diagram.arrows:
            # Parse handle IDs using the new format
            s_node_id, s_handle, _ = parse_handle_id(a.source)
            t_node_id, t_handle, _ = parse_handle_id(a.target)
            
            conn = {
                "from": f"{id_to_label[s_node_id]}{'_' + s_handle if s_handle != 'default' else ''}",
                "to": f"{id_to_label[t_node_id]}{'_' + t_handle if t_handle != 'default' else ''}",
            }
            # Add contentType and label from direct fields
            if a.content_type:
                conn["content_type"] = a.content_type.value
            if a.label:
                conn["label"] = a.label

            if a.data:
                # Only include essential arrow data for light format
                filtered_data = {}
                # Skip 'branch' if the handle name already contains the branch info (condtrue/condfalse)
                # This makes the format more dense by avoiding redundancy
                if "branch" in a.data and s_handle not in ["condtrue", "condfalse"]:
                    filtered_data["branch"] = a.data["branch"]
                # Only add data field if we have meaningful data to include
                if filtered_data:
                    conn["data"] = filtered_data
            connections.append(conn)

        # Add persons to the light format export using label as key
        persons_out = {}
        for p in diagram.persons:
            person_data = {
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
            persons_out[p.label] = person_data

        out: dict[str, Any] = {"version": "light", "nodes": nodes_out}
        if connections:
            out["connections"] = connections
        if persons_out:
            out["persons"] = persons_out
        return out

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.8 if isinstance(data.get("nodes"), list) else 0.1

    def quick_match(self, content: str) -> bool:
        return "nodes:" in content and not content.lstrip().startswith(("{", "["))
