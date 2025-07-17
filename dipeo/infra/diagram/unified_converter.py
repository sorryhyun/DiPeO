# Unified converter that uses format strategies

import logging
from typing import Any

from dipeo.models import (
    ContentType,
    DataType,
    DomainArrow,
    DomainDiagram,
    DomainHandle,
    DomainNode,
    HandleDirection,
    HandleLabel,
    NodeType,
    parse_handle_id,
)

DomainDiagram.model_rebuild()

from dipeo.models import create_handle_id
from dipeo.models.conversions import node_kind_to_domain_type

from dipeo.core.ports import DiagramConverter, FormatStrategy
from dipeo.domain.diagram.utils import dict_to_domain_diagram
from dipeo.domain.diagram.utils.shared_components import (
    ArrowBuilder,
    HandleGenerator,
    PositionCalculator,
)
from dipeo.domain.diagram.strategies import LightYamlStrategy, NativeJsonStrategy, ReadableYamlStrategy

logger = logging.getLogger(__name__)


class UnifiedDiagramConverter(DiagramConverter):
    # Universal converter using strategy pattern for different formats

    def __init__(self):
        self.strategies: dict[str, FormatStrategy] = {}
        self.handle_generator = HandleGenerator()
        self.position_calculator = PositionCalculator()
        self.arrow_builder = ArrowBuilder()

        self._register_default_strategies()

    def _register_default_strategies(self):
        self.register_strategy(NativeJsonStrategy())
        self.register_strategy(LightYamlStrategy())
        self.register_strategy(ReadableYamlStrategy())

    def register_strategy(self, strategy: FormatStrategy):
        self.strategies[strategy.format_id] = strategy

    def set_format(self, format_id: str):
        """Set the active format for conversion."""
        if format_id not in self.strategies:
            raise ValueError(f"Unknown format: {format_id}")
        self.active_format = format_id

    def get_strategy(self, format_id: str | None = None) -> FormatStrategy:
        """Get strategy for the specified format."""
        fmt = format_id or getattr(self, "active_format", None)
        if not fmt:
            raise ValueError("No format specified")

        strategy = self.strategies.get(fmt)
        if not strategy:
            raise ValueError(f"Unknown format: {fmt}")

        return strategy

    def serialize(self, diagram: DomainDiagram, format_id: str | None = None) -> str:
        """Convert domain diagram to format-specific string."""
        fmt = format_id or getattr(self, "active_format", None)
        if not fmt:
            raise ValueError("No format specified for serialization")

        strategy = self.get_strategy(fmt)

        data = strategy.build_export_data(diagram)

        return strategy.format(data)

    def deserialize(self, content: str, format_id: str | None = None) -> DomainDiagram:
        """Convert format-specific string to domain diagram."""
        fmt = format_id or getattr(self, "active_format", None)

        if not fmt:
            fmt = self.detect_format(content)
            if not fmt:
                raise ValueError("Could not detect format automatically")

        strategy = self.get_strategy(fmt)

        data = strategy.parse(content)

        nodes_dict = {}
        arrows_dict = {}

        handles_data = data.get("handles", {})
        if isinstance(handles_data, dict):
            handles_dict = handles_data
        elif isinstance(handles_data, list):
            handles_dict = {
                handle.get("id", f"handle_{i}"): handle
                for i, handle in enumerate(handles_data)
            }
        else:
            handles_dict = {}

        persons_data = data.get("persons", {})
        if isinstance(persons_data, dict):
            # For light format, transform the persons data
            if fmt == "light":
                persons_dict = {}
                for person_key, person_config in persons_data.items():
                    # Transform flat structure to nested llmConfig structure
                    llm_config = {
                        "service": person_config.get("service", "openai"),
                        "model": person_config.get("model", "gpt-4-mini"),
                        "api_key_id": person_config.get("api_key_id", "default"),
                    }
                    if "system_prompt" in person_config:
                        llm_config["system_prompt"] = person_config["system_prompt"]
                    
                    # In new format, the key is the label
                    # Check if there's an explicit ID, otherwise generate one
                    person_id = person_config.get("id", f"person_{person_key.replace(' ', '_')}")
                    
                    # Add required fields for DomainPerson
                    person_dict = {
                        "id": person_id,
                        "label": person_key,  # The key is the label in light format
                        "type": "person",
                        "llm_config": llm_config,
                    }
                    persons_dict[person_id] = person_dict
            else:
                persons_dict = persons_data
        elif isinstance(persons_data, list):
            # For readable format, persons are a list of dicts with person name as key
            if fmt == "readable":
                persons_dict = {}
                for person_item in persons_data:
                    if isinstance(person_item, dict):
                        # Each item should have one key (the person name)
                        for person_name, person_config in person_item.items():
                            llm_config = {
                                "service": person_config.get("service", "openai"),
                                "model": person_config.get("model", "gpt-4-mini"),
                                "api_key_id": person_config.get("api_key_id", "default"),
                                "system_prompt": person_config.get("system_prompt"),
                            }
                            
                            # Add required fields for DomainPerson
                            person_dict = {
                                "id": person_name,
                                "label": person_name,
                                "type": "person",
                                "llm_config": llm_config,
                            }
                            persons_dict[person_name] = person_dict
            else:
                persons_dict = {
                    person.get("id", f"person_{i}"): person
                    for i, person in enumerate(persons_data)
                }
        else:
            persons_dict = {}

        # Create person label to ID mapping for light format
        person_label_to_id: dict[str, str] = {}
        if fmt == "light" and persons_dict:
            for person_id, person_data in persons_dict.items():
                label = person_data.get("label", person_id)
                person_label_to_id[label] = person_id
        
        node_data_list = strategy.extract_nodes(data)
        
        # For light format, resolve person labels to IDs
        if fmt == "light" and person_label_to_id:
            for node_data in node_data_list:
                node_type = node_data.get("type")
                if node_type == "person_job":
                    # Check if person is in top-level or in props/data
                    person_ref = None
                    if "person" in node_data:
                        person_ref = node_data["person"]
                        # If person_ref is a label (not an ID), resolve it
                        if person_ref in person_label_to_id:
                            node_data["person"] = person_label_to_id[person_ref]
                    elif "props" in node_data and isinstance(node_data["props"], dict) and "person" in node_data["props"]:
                        person_ref = node_data["props"]["person"]
                        # If person_ref is a label (not an ID), resolve it
                        if person_ref in person_label_to_id:
                            node_data["props"]["person"] = person_label_to_id[person_ref]
                    elif "data" in node_data and isinstance(node_data["data"], dict) and "person" in node_data["data"]:
                        person_ref = node_data["data"]["person"]
                        # If person_ref is a label (not an ID), resolve it
                        if person_ref in person_label_to_id:
                            node_data["data"]["person"] = person_label_to_id[person_ref]
        
        for index, node_data in enumerate(node_data_list):
            node = self._create_node(node_data, index)
            nodes_dict[node.id] = node

        # Extract arrows using strategy (handles both "arrows" and "connections")
        # Pass the original node data list, not the DomainNode objects
        arrows_list = strategy.extract_arrows(data, node_data_list)
        arrows_dict = {}
        for _index, arrow_data in enumerate(arrows_list):
            arrow = self._create_arrow(arrow_data, nodes_dict)
            if arrow:
                arrows_dict[arrow.id] = arrow

        diagram_dict = {
            "nodes": nodes_dict,
            "handles": handles_dict,
            "arrows": arrows_dict,
            "persons": persons_dict,
            "metadata": data.get("metadata"),
        }
        
        # Second pass: Update content types for arrows from condition nodes
        # to preserve the content type from their inputs
        for arrow_id, arrow in arrows_dict.items():
            if arrow.source:
                try:
                    # Parse the source handle to get node ID and handle label
                    node_id, handle_label, direction = parse_handle_id(arrow.source)
                    source_node = nodes_dict.get(node_id)
                    
                    # If source is from a condition node's condtrue/condfalse output
                    if (source_node and 
                        source_node.type == NodeType.condition and 
                        handle_label.value in ["condtrue", "condfalse"]):
                        # Find arrows feeding into this condition node
                        input_content_types = []
                        for other_arrow in arrows_dict.values():
                            if other_arrow.target and node_id in other_arrow.target:
                                # This arrow feeds into the condition node
                                if other_arrow.content_type:
                                    input_content_types.append(other_arrow.content_type)
                        
                        # If we found input content types and they're all the same, preserve it
                        if input_content_types and all(ct == input_content_types[0] for ct in input_content_types):
                            arrow.content_type = input_content_types[0]
                            logger.debug(
                                f"Preserving content_type '{input_content_types[0].value}' from input "
                                f"for arrow from condition node {node_id} output {handle_label.value}"
                            )
                except Exception as e:
                    # If parsing fails, keep the existing content type
                    logger.debug(f"Failed to update content type for arrow from {arrow.source}: {e}")

        # Generate default handles for nodes that don't have any handles
        for node_id, node in nodes_dict.items():
            # Check if this node has any handles already
            node_has_handles = any(
                (
                    handle.get("nodeId") == node_id
                    if isinstance(handle, dict)
                    else handle.node_id == node_id
                )
                for handle in handles_dict.values()
            )
            if not node_has_handles:
                self.handle_generator.generate_for_node(
                    diagram_dict, node_id, node.type
                )

        # Create any custom handles referenced by arrows but not yet defined
        for arrow in arrows_dict.values():
            # Check source handle
            if "_" in arrow.source:
                # First check if this is a full handle ID format (nodeId_handleLabel_direction)
                parts = arrow.source.split("_")
                if len(parts) >= 3 and parts[-1] in ["input", "output"]:
                    # This is already a full handle ID, don't parse it
                    # Verify it exists in handles
                    if arrow.source in diagram_dict["handles"]:
                        continue
                    else:
                        continue
                
                # Otherwise, parse as light format (nodeLabel_handleName)
                # For light format, we need to handle node labels with spaces
                # Try to match against existing node labels first
                node_id = None
                handle_name = "default"
                
                # Check if any node label + "_handleName" matches the arrow source
                for nid, node in nodes_dict.items():
                    node_label = node.data.get("label", nid) if node.data else nid
                    # Check for exact match with handle name appended
                    for possible_handle in ["first", "default", "condtrue", "condfalse"]:
                        if arrow.source == f"{node_label}_{possible_handle}":
                            node_id = nid
                            handle_name = possible_handle
                            logger.debug(f"Matched node label '{node_label}' with handle '{possible_handle}'")
                            break
                    if node_id:
                        break
                
                # If no match found, fall back to simple split
                if not node_id:
                    parts = arrow.source.rsplit("_", 1)
                    if len(parts) == 2:
                        node_label_or_id, handle_name = parts
                        # Try to find node by label or ID
                        node_id = next(
                            (nid for nid, node in nodes_dict.items() 
                             if nid == node_label_or_id or 
                             (node.data and node.data.get("label") == node_label_or_id)),
                            node_label_or_id
                        )
                    else:
                        node_id = arrow.source
                        handle_name = "default"

                # Check if a handle with same node_id and label already exists
                handle_exists = False
                actual_node_id = next((n_id for n_id in nodes_dict if n_id.lower() == node_id.lower()), node_id)
                
                # Validate handle_name is not a direction value
                if handle_name in ["input", "output"]:
                    logger.warning(f"Invalid handle name '{handle_name}' - using 'default' instead")
                    handle_name = "default"
                
                try:
                    # Try to create handle label - this allows custom labels
                    handle_label = HandleLabel(handle_name)
                except ValueError:
                    # For custom handle labels (e.g., DB nodes)
                    handle_label = handle_name
                    
                expected_handle_id = create_handle_id(actual_node_id, handle_label, HandleDirection.output)
                
                if expected_handle_id in diagram_dict["handles"]:
                    handle = diagram_dict["handles"][expected_handle_id]
                    if handle.direction == HandleDirection.output:
                        handle_exists = True
                        # Update arrow to use the existing handle ID
                        arrow.source = expected_handle_id
                
                # Check if node exists (case-insensitive)
                node_exists = any(n_id.lower() == node_id.lower() for n_id in nodes_dict)
                if not handle_exists and node_exists:
                    # Create handle with normalized ID, including direction for new format
                    normalized_handle_id = create_handle_id(actual_node_id, HandleLabel(handle_name), HandleDirection.output)
                    # Create output handle
                    diagram_dict["handles"][normalized_handle_id] = DomainHandle(
                        id=normalized_handle_id,
                        node_id=actual_node_id,
                        label=handle_name,
                        direction=HandleDirection.output,
                        data_type=DataType.any,
                        position="right",
                    )
                    # Update arrow to use the normalized handle ID
                    arrow.source = normalized_handle_id

            # Check target handle
            if "_" in arrow.target:
                # First check if this is a full handle ID format (nodeId_handleLabel_direction)
                parts = arrow.target.split("_")
                if len(parts) >= 3 and parts[-1] in ["input", "output"]:
                    # This is already a full handle ID, don't parse it
                    # Verify it exists in handles
                    if arrow.target in diagram_dict["handles"]:
                        continue
                    else:
                        continue
                
                # Otherwise, parse as light format (nodeLabel_handleName)
                # For light format, we need to handle node labels with spaces
                # Try to match against existing node labels first
                node_id = None
                handle_name = "default"
                
                # Check if any node label + "_handleName" matches the arrow target
                for nid, node in nodes_dict.items():
                    node_label = node.data.get("label", nid) if node.data else nid
                    # Check for exact match with handle name appended
                    for possible_handle in ["first", "default", "condtrue", "condfalse"]:
                        if arrow.target == f"{node_label}_{possible_handle}":
                            node_id = nid
                            handle_name = possible_handle
                            break
                    if node_id:
                        break
                
                # If no match found, fall back to simple split
                if not node_id:
                    parts = arrow.target.rsplit("_", 1)
                    if len(parts) == 2:
                        node_label_or_id, handle_name = parts
                        # Try to find node by label or ID
                        node_id = next(
                            (nid for nid, node in nodes_dict.items() 
                             if nid == node_label_or_id or 
                             (node.data and node.data.get("label") == node_label_or_id)),
                            node_label_or_id
                        )
                    else:
                        node_id = arrow.target
                        handle_name = "default"
                

                # Check if a handle with same node_id and label already exists
                handle_exists = False
                actual_node_id = next((n_id for n_id in nodes_dict if n_id.lower() == node_id.lower()), node_id)
                
                # Validate handle_name is not a direction value
                if handle_name in ["input", "output"]:
                    logger.warning(f"Invalid handle name '{handle_name}' - using 'default' instead")
                    handle_name = "default"
                
                try:
                    # Try to create handle label - this allows custom labels
                    handle_label = HandleLabel(handle_name)
                except ValueError:
                    # For custom handle labels (e.g., DB nodes)
                    handle_label = handle_name
                    
                expected_handle_id = create_handle_id(actual_node_id, handle_label, HandleDirection.input)
                
                if expected_handle_id in diagram_dict["handles"]:
                    handle = diagram_dict["handles"][expected_handle_id]
                    if handle.direction == HandleDirection.input:
                        handle_exists = True
                        # Update arrow to use the existing handle ID
                        arrow.target = expected_handle_id
                
                # Check if node exists (case-insensitive)
                node_exists = any(n_id.lower() == node_id.lower() for n_id in nodes_dict)
                if not handle_exists and node_exists:
                    # Create handle with normalized ID, including direction for new format
                    normalized_handle_id = create_handle_id(actual_node_id, HandleLabel(handle_name), HandleDirection.input)
                    # Create input handle
                    diagram_dict["handles"][normalized_handle_id] = DomainHandle(
                        id=normalized_handle_id,
                        node_id=actual_node_id,
                        label=handle_name,
                        direction=HandleDirection.input,
                        data_type=DataType.any,
                        position="left",
                    )
                    # Update arrow to use the normalized handle ID
                    arrow.target = normalized_handle_id

        return dict_to_domain_diagram(diagram_dict)

    def _create_node(self, node_data: dict[str, Any], index: int) -> DomainNode:
        """Create a domain node from node data."""
        node_id = node_data.get("id", f"node_{index}")
        node_type_str = node_data.get("type", "job")

        # Convert node type string to domain enum
        try:
            node_type = node_kind_to_domain_type(node_type_str)
        except ValueError:
            logger.warning(f"Unknown node type '{node_type_str}', defaulting to 'job'")
            node_type = node_kind_to_domain_type("job")

        position = node_data.get("position")
        if not position:
            vec2_pos = self.position_calculator.calculate_grid_position(index)
            position = {"x": vec2_pos.x, "y": vec2_pos.y}

        exclude_fields = {"id", "type", "position", "handles", "arrows"}
        properties = {k: v for k, v in node_data.items() if k not in exclude_fields}

        return DomainNode(
            id=node_id, type=node_type, position=position, data=properties
        )

    def _create_arrow(self, arrow_data: dict[str, Any], nodes_dict: dict[str, DomainNode]) -> DomainArrow | None:
        """Create a domain arrow from arrow data."""
        source = arrow_data.get("source")
        target = arrow_data.get("target")

        if not source or not target:
            return None

        arrow_id = arrow_data.get(
            "id", self.arrow_builder.create_arrow_id(source, target)
        )

        # Extract contentType and label from arrow_data (they may be at the top level, not in data)
        content_type = arrow_data.get("content_type")
        label = arrow_data.get("label")

        # Automatically set content_type for empty arrows
        if content_type is None:
            # Default to raw_text for all empty arrows
            content_type = ContentType.raw_text

        return DomainArrow(
            id=arrow_id, 
            source=source, 
            target=target, 
            content_type=content_type,
            label=label,
            data=arrow_data.get("data")
        )

    def validate(
        self, content: str, format_id: str | None = None
    ) -> tuple[bool, list[str]]:
        """Validate content without full deserialization."""
        try:
            self.deserialize(content, format_id)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def detect_format(self, content: str) -> str | None:
        """Automatically detect format from content."""
        # First try quick match for efficiency
        for format_id, strategy in self.strategies.items():
            if strategy.quick_match(content):
                return format_id

        # Fall back to full parsing if no quick match
        confidences: list[tuple[str, float]] = []

        for format_id, strategy in self.strategies.items():
            try:
                data = strategy.parse(content)
                confidence = strategy.detect_confidence(data)
                confidences.append((format_id, confidence))
            except Exception:
                confidences.append((format_id, 0.0))

        confidences.sort(key=lambda x: x[1], reverse=True)

        if confidences and confidences[0][1] > 0.5:
            return confidences[0][0]

        return None

    def detect_format_confidence(self, content: str) -> float:
        format_id = self.detect_format(content)
        if format_id:
            return 1.0
        return 0.0

    def get_supported_formats(self) -> list[dict[str, str]]:
        return [
            {"id": format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
        ]

    def get_export_formats(self) -> list[dict[str, str]]:
        return [
            {"id": format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
            if strategy.format_info.get("supports_export", True)
        ]

    def get_import_formats(self) -> list[dict[str, str]]:
        return [
            {"id": format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
            if strategy.format_info.get("supports_import", True)
        ]

    def convert(self, content: str, from_format: str, to_format: str) -> str:
        """Convert content from one format to another."""
        diagram = self.deserialize(content, from_format)
        return self.serialize(diagram, to_format)

    def get(self, format_id: str) -> FormatStrategy:
        """Get strategy for the specified format (alias for get_strategy)."""
        return self.get_strategy(format_id)

    def get_info(self, format_id: str) -> dict[str, str]:
        """Get format information for the specified format."""
        strategy = self.get_strategy(format_id)
        return strategy.format_info


# Create a singleton instance to act as the registry
converter_registry = UnifiedDiagramConverter()
