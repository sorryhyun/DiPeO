from __future__ import annotations

import logging
import re
from typing import Any

from dipeo.diagram_generated import (
    DomainDiagram,
    HandleDirection,
    HandleLabel,
    NodeID,
)
from dipeo.diagram_generated import MemoryView
from dipeo.domain.diagram.handle import (
    create_handle_id,
    parse_handle_id
)
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
from dipeo.domain.diagram.models.format_models import ReadableDiagram, ReadableNode, ReadableArrow
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

    # ---- Typed deserialization ------------------------------------------------ #
    def deserialize_to_domain(self, content: str) -> DomainDiagram:
        """Deserialize readable format to DomainDiagram using typed models."""
        # Parse YAML
        data = self.parse(content)
        data = self._clean_graphql_fields(data)
        
        # Parse into typed ReadableDiagram model
        readable_diagram = self._parse_to_readable_diagram(data)
        
        # Convert to intermediate dict format with transformations
        diagram_dict = self._readable_diagram_to_dict(readable_diagram, data)
        
        # Apply format-specific transformations
        diagram_dict = self._apply_format_transformations(diagram_dict, data)
        
        # Convert to DomainDiagram
        return dict_to_domain_diagram(diagram_dict)
    
    def _parse_to_readable_diagram(self, data: dict[str, Any]) -> ReadableDiagram:
        """Parse dict data into typed ReadableDiagram model."""
        # Process nodes in the workflow style
        nodes = []
        for index, node_data in enumerate(data.get("nodes", [])):
            if not isinstance(node_data, dict):
                continue
            
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
            
            # Extract props
            props = {k: v for k, v in cfg.items() if k not in {"position", "type"}}
            
            # Create typed ReadableNode
            node = ReadableNode(
                id=self._create_node_id(index),
                type=node_type,
                label=clean_name,
                position=position if position else {"x": 0, "y": 0},
                props=props
            )
            nodes.append(node)
        
        # Process arrows from flow section
        arrows = self._parse_flow_to_arrows(data.get("flow", []), nodes)
        
        return ReadableDiagram(
            version="readable",
            nodes=nodes,
            arrows=arrows,
            persons=data.get("persons"),
            api_keys=data.get("api_keys"),
            metadata=data.get("metadata")
        )
    
    def _parse_flow_to_arrows(self, flow_data: list[Any], nodes: list[ReadableNode]) -> list[ReadableArrow]:
        """Parse flow section into typed ReadableArrow objects."""
        arrows = []
        # Create label to node mapping
        label_to_node = {node.label: node for node in nodes}
        arrow_counter = 0
        
        for flow_item in flow_data:
            if isinstance(flow_item, str):
                # Handle string format: "Start -> Ask Assistant"
                if " -> " in flow_item:
                    parts = flow_item.split(" -> ")
                    if len(parts) == 2:
                        src_label, dst_label = parts[0].strip(), parts[1].strip()
                        if src_label in label_to_node and dst_label in label_to_node:
                            arrow = ReadableArrow(
                                id=f"arrow_{arrow_counter}",
                                source=label_to_node[src_label].id,
                                target=label_to_node[dst_label].id
                            )
                            arrows.append(arrow)
                            arrow_counter += 1
            elif isinstance(flow_item, dict):
                # Dictionary format: {source: destination} or {source: {dest1: null, dest2: null}}
                for src, dst_data in flow_item.items():
                    if src not in label_to_node:
                        continue
                    
                    if isinstance(dst_data, str):
                        # Single destination: {source: "destination"}
                        if dst_data in label_to_node:
                            arrow = ReadableArrow(
                                id=f"arrow_{arrow_counter}",
                                source=label_to_node[src].id,
                                target=label_to_node[dst_data].id
                            )
                            arrows.append(arrow)
                            arrow_counter += 1
                    elif isinstance(dst_data, dict):
                        # Multiple destinations: {source: {dest1: null, dest2: null}}
                        for dst in dst_data.keys():
                            if str(dst) in label_to_node:
                                arrow = ReadableArrow(
                                    id=f"arrow_{arrow_counter}",
                                    source=label_to_node[src].id,
                                    target=label_to_node[str(dst)].id
                                )
                                arrows.append(arrow)
                                arrow_counter += 1
                    elif isinstance(dst_data, list):
                        # Array format: {source: [dest1, dest2, ...]}
                        for dst in dst_data:
                            if dst in label_to_node:
                                arrow = ReadableArrow(
                                    id=f"arrow_{arrow_counter}",
                                    source=label_to_node[src].id,
                                    target=label_to_node[dst].id
                                )
                                arrows.append(arrow)
                                arrow_counter += 1
        
        return arrows
    
    def _readable_diagram_to_dict(self, readable_diagram: ReadableDiagram, original_data: dict[str, Any]) -> dict[str, Any]:
        """Convert ReadableDiagram to intermediate dict format."""
        # Process nodes
        nodes_list = []
        for node in readable_diagram.nodes:
            # Process properties
            props = process_dotted_keys(node.props)
            props = NodeFieldMapper.map_import_fields(node.type, props)
            
            # Build node dict
            node_dict = build_node(
                id=node.id,
                type_=node.type,
                pos=node.position,
                label=node.label,
                **props
            )
            nodes_list.append(node_dict)
        
        # Build nodes dict
        nodes_dict = self._build_nodes_dict(nodes_list)
        
        # Process arrows - for readable format, arrows are simple without complex handle logic
        arrows_dict = {}
        for arrow in readable_diagram.arrows:
            arrows_dict[arrow.id] = {
                "id": arrow.id,
                "source": create_handle_id(arrow.source, arrow.source_handle or "default", HandleDirection.OUTPUT),
                "target": create_handle_id(arrow.target, arrow.target_handle or "default", HandleDirection.INPUT),
                "data": arrow.data or {},
                "label": arrow.label
            }
        
        # Extract handles and persons
        handles_dict = self._extract_handles_dict(original_data)
        persons_dict = self._extract_persons_dict(original_data)
        
        return {
            "nodes": nodes_dict,
            "arrows": arrows_dict,
            "handles": handles_dict,
            "persons": persons_dict,
            "metadata": readable_diagram.metadata,
        }
    
    def _create_node_id(self, index: int, prefix: str = "node") -> str:
        """Create a unique node ID."""
        return f"{prefix}_{index}"

    # ---- Helper methods for backward compatibility ------------------------ #
    def _build_nodes_dict(self, nodes_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Build nodes dict from list."""
        from dipeo.diagram_generated.conversions import node_kind_to_domain_type
        from dipeo.domain.diagram.utils.shared_components import PositionCalculator
        
        position_calculator = PositionCalculator()
        nodes_dict = {}
        
        for index, node_data in enumerate(nodes_list):
            if "id" not in node_data:
                continue
                
            node_id = node_data["id"]
            node_type_str = node_data.get("type", "person_job")
            
            try:
                node_type = node_kind_to_domain_type(node_type_str)
            except ValueError:
                log.warning(f"Unknown node type '{node_type_str}', defaulting to 'person_job'")
                node_type = node_kind_to_domain_type("person_job")
            
            position = node_data.get("position")
            if not position:
                position = position_calculator.calculate_grid_position(index)
            
            exclude_fields = {"id", "type", "position", "handles", "arrows"}
            properties = {k: v for k, v in node_data.items() if k not in exclude_fields}
            
            nodes_dict[node_id] = {
                "id": node_id,
                "type": node_type.value,
                "position": position,
                "data": properties
            }
            
        return nodes_dict

    def _parse_single_flow(self, src: str, dst: str | bool | int, label2id: dict[str, str], idx: int) -> list[dict[str, Any]]:
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

    # ---- Typed serialization -------------------------------------------------- #
    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Serialize DomainDiagram to readable format using typed models."""
        # Convert to ReadableDiagram
        readable_diagram = self._domain_to_readable_diagram(diagram)
        
        # Convert to dict for YAML serialization
        data = self._readable_diagram_to_export_dict(readable_diagram)
        
        # Format as YAML
        return self.format(data)
    
    def _domain_to_readable_diagram(self, diagram: DomainDiagram) -> ReadableDiagram:
        """Convert DomainDiagram to typed ReadableDiagram."""
        # Convert nodes
        nodes = []
        for n in diagram.nodes:
            node = ReadableNode(
                id=n.id,
                type=str(n.type).split(".")[-1].lower(),
                label=n.data.get("label") or n.id,
                position={"x": round(n.position.x), "y": round(n.position.y)},
                props={k: v for k, v in n.data.items() if k != "label" and v not in (None, "", {}, [])}
            )
            nodes.append(node)
        
        # Convert arrows
        arrows = []
        for a in diagram.arrows:
            # Parse handle IDs
            s_node_id, s_handle, _ = parse_handle_id(a.source)
            t_node_id, t_handle, _ = parse_handle_id(a.target)
            
            arrow = ReadableArrow(
                id=a.id,
                source=s_node_id,
                target=t_node_id,
                source_handle=s_handle if s_handle != "default" else None,
                target_handle=t_handle if t_handle != "default" else None,
                label=a.label,
                data=a.data if a.data else None
            )
            arrows.append(arrow)
        
        # Convert persons
        persons_data = None
        if diagram.persons:
            persons_data = []
            for p in diagram.persons:
                person_dict = {
                    "id": p.id,
                    "label": p.label,
                    "llm_config": {
                        "service": p.llm_config.service.value if hasattr(p.llm_config.service, "value") else str(p.llm_config.service),
                        "model": p.llm_config.model,
                        "api_key_id": p.llm_config.api_key_id,
                    }
                }
                if p.llm_config.system_prompt:
                    person_dict["llm_config"]["system_prompt"] = p.llm_config.system_prompt
                persons_data.append(person_dict)
        
        return ReadableDiagram(
            version="readable",
            nodes=nodes,
            arrows=arrows,
            persons=persons_data,
            metadata=diagram.metadata.model_dump(exclude_none=True) if diagram.metadata else None
        )
    
    def _readable_diagram_to_export_dict(self, readable_diagram: ReadableDiagram) -> dict[str, Any]:
        """Convert ReadableDiagram to dict for YAML export."""
        # Build a mapping from node ID to label
        id_to_label: dict[str, str] = {}
        for n in readable_diagram.nodes:
            id_to_label[n.id] = n.label
        
        # Build nodes section with positions
        nodes = []
        for n in readable_diagram.nodes:
            label = n.label

            # Add position to label if present
            if n.position and (n.position["x"] != 0 or n.position["y"] != 0):
                label_with_pos = f"{label} @({int(n.position['x'])},{int(n.position['y'])})"
            else:
                label_with_pos = label

            # Build node config
            node_config = {"type": n.type} if n.type != "job" else {}
            # Add props if any
            if n.props:
                # Map fields for export
                mapped_props = NodeFieldMapper.map_export_fields(n.type, n.props.copy())
                # Filter out empty values
                filtered_props = {
                    k: v for k, v in mapped_props.items()
                    if v not in (None, "", {}, [])
                }
                node_config.update(filtered_props)
            
            # Only add node if it has config
            if node_config:
                nodes.append({label_with_pos: node_config})
            else:
                nodes.append({label_with_pos: {}})

        # Build flow section with enhanced syntax
        flow = self._build_enhanced_flow(readable_diagram, id_to_label)

        # Build persons section
        persons = []
        if readable_diagram.persons:
            for person_data in readable_diagram.persons:
                person_dict = {}
                if "label" in person_data and "llm_config" in person_data:
                    config = person_data["llm_config"]
                    person_config = {
                        "service": config.get("service", "openai"),
                        "model": config.get("model", "gpt-4"),
                    }
                    # Only include optional fields if they have values
                    if config.get("system_prompt"):
                        person_config["system_prompt"] = config["system_prompt"]
                    if config.get("api_key_id"):
                        person_config["api_key_id"] = config["api_key_id"]
                    person_dict[person_data["label"]] = person_config
                    persons.append(person_dict)

        out: dict[str, Any] = {"version": "readable"}
        if persons:
            out["persons"] = persons
        out["nodes"] = nodes
        if flow:
            out["flow"] = flow
        return out

    def _build_enhanced_flow(self, readable_diagram: ReadableDiagram, id_to_label: dict[str, str]) -> list[str]:
        """Build flow section using enhanced syntax with parallel flows and content types"""
        # Group arrows by source to detect parallel flows
        source_groups: dict[str, list] = {}

        for a in readable_diagram.arrows:
            # Use node label instead of ID for source key
            source_label = id_to_label.get(a.source, a.source)
            # Add handle suffix for non-default handles
            if a.source_handle and a.source_handle not in ("output", "default"):
                source_key = f"{source_label}_{a.source_handle}"
            else:
                source_key = source_label

            if source_key not in source_groups:
                source_groups[source_key] = []

            # Build target string with handle
            target_str = id_to_label.get(a.target, a.target)
            if a.target_handle and a.target_handle not in ("input", "default"):
                target_str += f"_{a.target_handle}"

            # Add label annotation
            if a.label:
                target_str += f" ({a.label})"

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
    
    # ---- Helper methods --------------------------------------------------- #
    def parse(self, content: str) -> dict[str, Any]:
        """Parse YAML content."""
        return self._parse_yaml(content)
    
    def format(self, data: dict[str, Any]) -> str:
        """Format data as YAML."""
        return self._format_yaml(data)
    
    def _extract_handles_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract handles for readable format."""
        return data.get("handles", {})
    
    def _extract_persons_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract persons for readable format."""
        persons_data = data.get("persons", [])
        if isinstance(persons_data, list):
            return PersonExtractor.extract_from_list(persons_data)
        elif isinstance(persons_data, dict):
            return persons_data
        return {}
    
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
    
