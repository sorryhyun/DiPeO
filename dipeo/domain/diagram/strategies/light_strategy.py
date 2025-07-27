from __future__ import annotations

import logging
from typing import Any

from dipeo.diagram_generated import (
    DomainDiagram,
    DomainNode,
    DomainArrow,
    DomainHandle,
    HandleDirection,
    HandleLabel,
    NodeID,
    NodeType,
    ContentType,
    DataType,
    create_handle_id,
    parse_handle_id,
)
from dipeo.models import MemoryView
from dipeo.diagram_generated import node_kind_to_domain_type

from dipeo.domain.diagram.utils import (
    _node_id_map, 
    _YamlMixin, 
    build_node, 
    dict_to_domain_diagram,
    NodeFieldMapper,
    HandleParser,
    PersonExtractor,
    ArrowDataProcessor,
    process_dotted_keys,
)
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
        node_type = n.get("type", "job")
        
        # Use the common prop extraction
        props = self._extract_node_props(n)
        
        return build_node(
            id=self._create_node_id(index),
            type_=node_type,
            pos=n.get("position", {}),
            label=n.get("label"),
            **props,
        )
    
    def _get_node_base_props(self, node_data: dict[str, Any]) -> dict[str, Any]:
        """Get base properties for light format."""
        n = node_data
        return {
            **n.get("props", {}),
            **{
                k: v
                for k, v in n.items()
                if k not in {"label", "type", "position", "props"}
            },
        }

    def extract_arrows(
            self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        
        for idx, c in enumerate(data.get("connections", [])):
            if not isinstance(c, dict):
                continue
            
            src_raw, dst_raw = c.get("from", ""), c.get("to", "")
            
            # Parse source and destination using shared utility
            src_id, src_handle_from_split, src_label = HandleParser.parse_label_with_handle(src_raw, label2id)
            dst_id, dst_handle_from_split, dst_label = HandleParser.parse_label_with_handle(dst_raw, label2id)
            
            if not (src_id and dst_id):
                log.warning(
                    f"Skipping connection: could not find nodes for '{src_label}' -> '{dst_label}'"
                )
                continue
            
            # Determine handles using shared utility
            arrow_data = c.get("data", {})
            src_handle = HandleParser.determine_handle_name(src_handle_from_split, arrow_data, is_source=True)
            dst_handle = HandleParser.determine_handle_name(dst_handle_from_split, arrow_data, is_source=False)
            
            # Create arrow with data
            arrow_data_copy = arrow_data.copy() if arrow_data else {}
            
            # Add branch data if this is from a condition handle and not already present
            if src_handle in ["condtrue", "condfalse"] and "branch" not in arrow_data_copy:
                arrow_data_copy["branch"] = "true" if src_handle == "condtrue" else "false"
            
            # Create proper handle IDs
            source_handle_id, target_handle_id = HandleParser.create_handle_ids(
                src_id, dst_id, src_handle, dst_handle
            )
            
            # Build arrow using shared processor
            arrow_dict = ArrowDataProcessor.build_arrow_dict(
                c.get("data", {}).get("id", f"arrow_{idx}"),
                source_handle_id,
                target_handle_id,
                arrow_data_copy,
                c.get("content_type"),
                c.get("label")
            )
            
            arrows.append(arrow_dict)
        return arrows

    # ---- Domain Conversion Overrides -------------------------------------- #
    
    def _extract_persons_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract persons for light format with label-based structure."""
        persons_data = data.get("persons", {})
        if isinstance(persons_data, dict):
            return PersonExtractor.extract_from_dict(persons_data, is_light_format=True)
        return {}
    
    def _apply_format_transformations(
        self, diagram_dict: dict[str, Any], original_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply light format specific transformations."""
        # Create person label to ID mapping
        person_label_to_id: dict[str, str] = {}
        if diagram_dict["persons"]:
            for person_id, person_data in diagram_dict["persons"].items():
                label = person_data.get("label", person_id)
                person_label_to_id[label] = person_id
        
        # Resolve person labels to IDs in nodes
        if person_label_to_id:
            for node_id, node in diagram_dict["nodes"].items():
                if node.get("type") == "person_job":
                    person_ref = None
                    if "person" in node:
                        person_ref = node["person"]
                        if person_ref in person_label_to_id:
                            node["person"] = person_label_to_id[person_ref]
                    elif "props" in node and isinstance(node["props"], dict) and "person" in node["props"]:
                        person_ref = node["props"]["person"]
                        if person_ref in person_label_to_id:
                            node["props"]["person"] = person_label_to_id[person_ref]
                    elif "data" in node and isinstance(node["data"], dict) and "person" in node["data"]:
                        person_ref = node["data"]["person"]
                        if person_ref in person_label_to_id:
                            node["data"]["person"] = person_label_to_id[person_ref]
        
        # Generate handles for nodes without them
        self._generate_missing_handles(diagram_dict)
        
        # Create handles referenced by arrows
        self._create_arrow_handles(diagram_dict)
        
        # Preserve content types for condition outputs
        self._preserve_condition_content_types(diagram_dict)
        
        return diagram_dict
    
    def _generate_missing_handles(self, diagram_dict: dict[str, Any]):
        """Generate default handles for nodes that don't have any."""
        from dipeo.domain.diagram.utils.shared_components import HandleGenerator
        handle_generator = HandleGenerator()
        
        for node_id, node in diagram_dict["nodes"].items():
            # Check if this node has any handles
            node_has_handles = any(
                handle.get("nodeId") == node_id or handle.get("node_id") == node_id
                for handle in diagram_dict["handles"].values()
            )
            if not node_has_handles:
                # Convert node type string to enum
                node_type_str = node.get("type", "code_job")
                try:
                    node_type = node_kind_to_domain_type(node_type_str)
                except ValueError:
                    node_type = NodeType.code_job
                
                handle_generator.generate_for_node(
                    diagram_dict, node_id, node_type
                )
    
    def _create_arrow_handles(self, diagram_dict: dict[str, Any]):
        """Create handles referenced by arrows but not yet defined."""
        nodes_dict = diagram_dict["nodes"]
        
        for arrow_id, arrow in diagram_dict["arrows"].items():
            # Process source handle
            if "_" in arrow.get("source", ""):
                self._ensure_handle_exists(
                    arrow["source"], 
                    HandleDirection.output, 
                    nodes_dict, 
                    diagram_dict["handles"],
                    arrow
                )
            
            # Process target handle  
            if "_" in arrow.get("target", ""):
                self._ensure_handle_exists(
                    arrow["target"],
                    HandleDirection.input,
                    nodes_dict,
                    diagram_dict["handles"],
                    arrow
                )
    
    def _ensure_handle_exists(
        self, 
        handle_ref: str,
        direction: HandleDirection,
        nodes_dict: dict[str, Any],
        handles_dict: dict[str, Any],
        arrow: dict[str, Any]
    ):
        """Ensure a handle exists, creating it if necessary."""
        HandleParser.ensure_handle_exists(handle_ref, direction, nodes_dict, handles_dict, arrow)
    
    def _preserve_condition_content_types(self, diagram_dict: dict[str, Any]):
        """Preserve content types for arrows from condition nodes."""
        nodes_dict = diagram_dict["nodes"]
        arrows_dict = diagram_dict["arrows"]
        
        for arrow_id, arrow in arrows_dict.items():
            if arrow.get("source"):
                try:
                    # Parse source handle
                    node_id, handle_label, direction = parse_handle_id(arrow["source"])
                    source_node = nodes_dict.get(node_id)
                    
                    # If source is from condition node's condtrue/condfalse
                    if (source_node and 
                        source_node.get("type") == "condition" and 
                        handle_label.value in ["condtrue", "condfalse"]):
                        # Find input content types
                        input_content_types = []
                        for other_arrow in arrows_dict.values():
                            if other_arrow.get("target") and node_id in other_arrow["target"]:
                                if other_arrow.get("content_type"):
                                    input_content_types.append(other_arrow["content_type"])
                        
                        # Preserve if all inputs have same type
                        if input_content_types and all(ct == input_content_types[0] for ct in input_content_types):
                            arrow["content_type"] = input_content_types[0]
                except Exception:
                    pass

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
                if k not in {"label", "position"} and v not in (None, "", {})
                # Don't filter out empty arrays for 'flipped' property
                and not (k != "flipped" and v == [])
            }
            
            # Replace person ID with person label for person_job nodes
            if node_type == "person_job" and "person" in props:
                person_id = props["person"]
                if person_id in person_id_to_label:
                    props["person"] = person_id_to_label[person_id]
            
            # Map fields for export
            props = NodeFieldMapper.map_export_fields(node_type, props)
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
                # Check if branch data should be included
                if ArrowDataProcessor.should_include_branch_data(s_handle, a.data):
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
