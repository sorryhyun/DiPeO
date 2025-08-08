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
    DataType
)
from dipeo.diagram_generated import MemoryView
from dipeo.domain.diagram.handle import (
    create_handle_id,
    parse_handle_id
)
from dipeo.diagram_generated.conversions import node_kind_to_domain_type

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
from dipeo.domain.diagram.models.format_models import LightDiagram, LightNode, LightConnection
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

    # ---- New typed deserialization ---------------------------------------- #
    def deserialize_to_domain(self, content: str) -> DomainDiagram:
        """Deserialize light format content to DomainDiagram using typed models."""
        # Parse YAML to dict
        data = self.parse(content)
        data = self._clean_graphql_fields(data)
        
        # Parse into typed LightDiagram model
        light_diagram = self._parse_to_light_diagram(data)
        
        # Convert to intermediate dict format with all transformations
        diagram_dict = self._light_diagram_to_dict(light_diagram, data)
        
        # Apply format-specific transformations
        diagram_dict = self._apply_format_transformations(diagram_dict, data)
        
        # Convert to DomainDiagram
        return dict_to_domain_diagram(diagram_dict)
    
    def _parse_to_light_diagram(self, data: dict[str, Any]) -> LightDiagram:
        """Parse dict data into typed LightDiagram model."""
        # Convert nodes to LightNode objects
        nodes = []
        for node_data in data.get("nodes", []):
            if isinstance(node_data, dict):
                # Extract props separately to handle extra fields
                props = node_data.get("props", {})
                # Also include any extra fields not in standard fields
                for k, v in node_data.items():
                    if k not in {"type", "label", "position", "props"}:
                        props[k] = v
                
                node = LightNode(
                    type=node_data.get("type", "job"),
                    label=node_data.get("label"),
                    position=node_data.get("position"),
                    **props
                )
                nodes.append(node)
        
        # Convert connections to LightConnection objects
        connections = []
        for conn_data in data.get("connections", []):
            if isinstance(conn_data, dict):
                # Build connection data with proper field names
                conn_dict = {
                    "from": conn_data.get("from", ""),
                    "to": conn_data.get("to", ""),
                }
                if "label" in conn_data:
                    conn_dict["label"] = conn_data["label"]
                if "content_type" in conn_data or "type" in conn_data:
                    conn_dict["type"] = conn_data.get("content_type") or conn_data.get("type")
                
                # Add any extra fields
                for k, v in conn_data.items():
                    if k not in {"from", "to", "label", "type", "content_type"}:
                        conn_dict[k] = v
                
                conn = LightConnection(**conn_dict)
                connections.append(conn)
        
        # Convert persons dict to list if needed
        persons = data.get("persons")
        if persons and isinstance(persons, dict):
            persons = list(persons.values())
        
        # Convert api_keys dict to list if needed
        api_keys = data.get("api_keys")
        if api_keys and isinstance(api_keys, dict):
            api_keys = list(api_keys.values())
        
        return LightDiagram(
            nodes=nodes,
            connections=connections,
            persons=persons,
            api_keys=api_keys,
            metadata=data.get("metadata")
        )
    
    def _light_diagram_to_dict(self, light_diagram: LightDiagram, original_data: dict[str, Any]) -> dict[str, Any]:
        """Convert LightDiagram to intermediate dict format with all complex logic."""
        # Process nodes
        nodes_list = []
        for index, node in enumerate(light_diagram.nodes):
            node_dict = node.model_dump(exclude_none=True)
            
            # Extract and process properties
            props = self._extract_node_props_from_light(node_dict)
            
            # Add label to props if it exists
            if node.label:
                props["label"] = node.label
            
            # Build node with proper structure for DomainNode
            processed_node = {
                "id": self._create_node_id(index),
                "type": node.type,
                "position": node.position or {"x": 0, "y": 0},
                "data": props  # All extra properties go in data field
            }
            nodes_list.append(processed_node)
        
        # Build nodes dict
        nodes_dict = self._build_nodes_dict(nodes_list)
        
        # Process arrows/connections with complex handle logic
        arrows_list = self._process_light_connections(light_diagram, nodes_list)
        arrows_dict = self._build_arrows_dict(arrows_list)
        
        # Extract handles and persons
        handles_dict = self._extract_handles_dict(original_data)
        persons_dict = self._extract_persons_dict(original_data)
        
        return {
            "nodes": nodes_dict,
            "arrows": arrows_dict,
            "handles": handles_dict,
            "persons": persons_dict,
            "metadata": light_diagram.metadata,
        }
    
    def _build_nodes_dict(self, nodes_list: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Convert nodes list to dict indexed by node ID."""
        return {node["id"]: node for node in nodes_list}
    
    def _build_arrows_dict(self, arrows_list: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Convert arrows list to dict indexed by arrow ID."""
        return {arrow["id"]: arrow for arrow in arrows_list}
    
    def _extract_handles_dict(self, data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Extract handles from data (if present)."""
        handles = data.get("handles", {})
        if isinstance(handles, list):
            return {h.get("id", f"handle_{i}"): h for i, h in enumerate(handles)}
        return handles if isinstance(handles, dict) else {}
    
    def _extract_node_props_from_light(self, node_data: dict[str, Any]) -> dict[str, Any]:
        """Extract and process node properties from light format."""
        # Get all fields except standard ones
        props = {}
        for k, v in node_data.items():
            if k not in {"type", "label", "position"}:
                props[k] = v
        
        # Process dotted keys
        props = process_dotted_keys(props)
        
        # Map import fields
        node_type = node_data.get("type", "job")
        props = NodeFieldMapper.map_import_fields(node_type, props)
        
        return props

    def _process_light_connections(
            self, light_diagram: LightDiagram, nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process LightConnection objects into arrow dicts with handle logic."""
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        
        for idx, conn in enumerate(light_diagram.connections):
            # Get source and destination from typed model
            src_raw = conn.from_
            dst_raw = conn.to
            
            # Parse source and destination using shared utility
            src_id, src_handle_from_split, src_label = HandleParser.parse_label_with_handle(src_raw, label2id)
            dst_id, dst_handle_from_split, dst_label = HandleParser.parse_label_with_handle(dst_raw, label2id)
            
            if not (src_id and dst_id):
                log.warning(
                    f"Skipping connection: could not find nodes for '{src_label}' -> '{dst_label}'"
                )
                continue
            
            # Get arrow data from connection's extra fields
            conn_dict = conn.model_dump(by_alias=True, exclude={"from", "to", "label", "type"})
            arrow_data = conn_dict.get("data", {})
            
            # Determine handles using shared utility
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
                arrow_data.get("id", f"arrow_{idx}"),
                source_handle_id,
                target_handle_id,
                arrow_data_copy,
                conn.type,  # Use the typed field
                conn.label  # Use the typed field
            )
            
            arrows.append(arrow_dict)
        return arrows

    # ---- Helper methods for backward compatibility ------------------------ #
    def _create_node_id(self, index: int, prefix: str = "node") -> str:
        """Create a unique node ID."""
        return f"{prefix}_{index}"
    
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
                    node_type = NodeType.CODE_JOB
                
                handle_generator.generate_for_node(
                    diagram_dict, node_id, node_type.value
                )
    
    def _create_arrow_handles(self, diagram_dict: dict[str, Any]):
        """Create handles referenced by arrows but not yet defined."""
        nodes_dict = diagram_dict["nodes"]
        
        for arrow_id, arrow in diagram_dict["arrows"].items():
            # Process source handle
            if "_" in arrow.get("source", ""):
                self._ensure_handle_exists(
                    arrow["source"], 
                    HandleDirection.OUTPUT,
                    nodes_dict, 
                    diagram_dict["handles"],
                    arrow
                )
            
            # Process target handle  
            if "_" in arrow.get("target", ""):
                self._ensure_handle_exists(
                    arrow["target"],
                    HandleDirection.INPUT,
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
                        handle_label in ["condtrue", "condfalse"]):
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

    # ---- New typed serialization ------------------------------------------ #
    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Serialize DomainDiagram to light format string using typed models."""
        # Convert to LightDiagram
        light_diagram = self._domain_to_light_diagram(diagram)
        
        # Convert to dict for YAML serialization
        data = self._light_diagram_to_export_dict(light_diagram)
        
        # Format as YAML
        return self.format(data)
    
    def _domain_to_light_diagram(self, diagram: DomainDiagram) -> LightDiagram:
        """Convert DomainDiagram to typed LightDiagram model."""
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

        # Convert nodes
        nodes_out = []
        for n in diagram.nodes:
            base = n.data.get("label") or str(n.type).split(".")[-1].title()
            label = _unique(base)
            id_to_label[n.id] = label
            node_type = str(n.type).split(".")[-1].lower()
            
            # Extract properties
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
            
            # Create typed LightNode
            node = LightNode(
                type=node_type,
                label=label,
                position={"x": round(n.position.x), "y": round(n.position.y)},
                **props
            )
            nodes_out.append(node)

        # Convert arrows to connections
        connections = []
        for a in diagram.arrows:
            # Parse handle IDs
            s_node_id, s_handle, _ = parse_handle_id(a.source)
            t_node_id, t_handle, _ = parse_handle_id(a.target)
            
            # Build connection strings
            from_str = f"{id_to_label[s_node_id]}{'_' + s_handle if s_handle != 'default' else ''}"
            to_str = f"{id_to_label[t_node_id]}{'_' + t_handle if t_handle != 'default' else ''}"
            
            # Create extra data dict for connection
            extra_data = {}
            if a.data:
                # Only include essential arrow data
                if ArrowDataProcessor.should_include_branch_data(s_handle, a.data):
                    extra_data["data"] = {"branch": a.data["branch"]}
            
            # Create typed LightConnection
            conn = LightConnection(
                from_=from_str,
                to=to_str,
                label=a.label,
                type=a.content_type.value if a.content_type else None,
                **extra_data
            )
            connections.append(conn)

        # Convert persons
        persons_data = None
        if diagram.persons:
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
            persons_data = persons_out
        
        # Create typed LightDiagram
        return LightDiagram(
            nodes=nodes_out,
            connections=connections,
            persons=persons_data,
            metadata=diagram.metadata.model_dump(exclude_none=True) if diagram.metadata else None
        )
    
    def _light_diagram_to_export_dict(self, light_diagram: LightDiagram) -> dict[str, Any]:
        """Convert LightDiagram to dict for YAML export."""
        # Convert nodes to dict format
        nodes_out = []
        for node in light_diagram.nodes:
            node_dict = {
                "label": node.label,
                "type": node.type,
                "position": node.position,
            }
            # Add props if any
            props = {k: v for k, v in node.model_dump(exclude={"type", "label", "position"}).items() if v}
            if props:
                node_dict["props"] = props
            nodes_out.append(node_dict)
        
        # Convert connections to dict format
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
            # Add any extra data
            extra = conn.model_dump(exclude={"from_", "to", "label", "type"})
            if extra:
                conn_dict.update(extra)
            connections_out.append(conn_dict)
        
        # Build final dict
        out: dict[str, Any] = {"version": "light", "nodes": nodes_out}
        if connections_out:
            out["connections"] = connections_out
        if light_diagram.persons:
            out["persons"] = light_diagram.persons
        if light_diagram.metadata:
            out["metadata"] = light_diagram.metadata
        return out

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.8 if isinstance(data.get("nodes"), list) else 0.1

    def quick_match(self, content: str) -> bool:
        return "nodes:" in content and not content.lstrip().startswith(("{", "["))
