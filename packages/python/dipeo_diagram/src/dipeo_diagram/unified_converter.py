"""Unified converter that uses format strategies."""

import logging
from typing import Any

from dipeo_domain import (
    DataType,
    DomainArrow,
    DomainDiagram,
    DomainHandle,
    DomainNode,
    HandleDirection,
)

# Ensure models are rebuilt to resolve forward references
DomainDiagram.model_rebuild()

from .base import DiagramConverter, FormatStrategy
from .conversion_utils import backend_to_graphql, BackendDiagram
from dipeo_domain.conversions import node_kind_to_domain_type
from .shared_components import (
    ArrowBuilder,
    HandleGenerator,
    PositionCalculator,
)
from .strategies import (
    LightYamlStrategy,
    NativeJsonStrategy,
    ReadableYamlStrategy,
)

logger = logging.getLogger(__name__)


class UnifiedDiagramConverter(DiagramConverter):
    """
    Universal converter that uses strategy pattern for different formats.
    This replaces individual converter classes with a single converter
    that switches strategies based on format.
    """

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
                for person_id, person_config in persons_data.items():
                    # Transform flat structure to nested llmConfig structure
                    llm_config = {
                        "service": person_config.get("service", "openai"),
                        "model": person_config.get("model", "gpt-4-mini"),
                        "apiKeyId": person_config.get("apiKeyId", "default"),
                    }
                    if "systemPrompt" in person_config:
                        llm_config["systemPrompt"] = person_config["systemPrompt"]
                    
                    # Add required fields for DomainPerson
                    person_dict = {
                        "id": person_id,
                        "label": person_config.get("label", person_id),
                        "type": "person",
                        "llmConfig": llm_config,
                    }
                    persons_dict[person_id] = person_dict
            else:
                persons_dict = persons_data
        elif isinstance(persons_data, list):
            persons_dict = {
                person.get("id", f"person_{i}"): person
                for i, person in enumerate(persons_data)
            }
        else:
            persons_dict = {}

        node_data_list = strategy.extract_nodes(data)
        for index, node_data in enumerate(node_data_list):
            node = self._create_node(node_data, index)
            nodes_dict[node.id] = node

        # Extract arrows using strategy (handles both "arrows" and "connections")
        # Pass the original node data list, not the DomainNode objects
        arrows_list = strategy.extract_arrows(data, node_data_list)
        arrows_dict = {}
        for _index, arrow_data in enumerate(arrows_list):
            arrow = self._create_arrow(arrow_data)
            if arrow:
                arrows_dict[arrow.id] = arrow

        diagram_dict = BackendDiagram(
            nodes=nodes_dict,
            handles=handles_dict,
            arrows=arrows_dict,
            persons=persons_dict,
            metadata=data.get("metadata"),
        )

        # Generate default handles for nodes that don't have any handles
        for node_id, node in nodes_dict.items():
            # Check if this node has any handles already
            node_has_handles = any(
                (
                    handle.get("nodeId") == node_id
                    if isinstance(handle, dict)
                    else handle.nodeId == node_id
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
            if ":" in arrow.source:
                node_id, handle_name = arrow.source.split(":", 1)
                handle_id = f"{node_id}:{handle_name}"
                if handle_id not in diagram_dict.handles and node_id in nodes_dict:
                    # Create output handle
                    diagram_dict.handles[handle_id] = DomainHandle(
                        id=handle_id,
                        nodeId=node_id,
                        label=handle_name,
                        direction=HandleDirection.output,
                        dataType=DataType.any,
                        position="right",
                    )

            # Check target handle
            if ":" in arrow.target:
                node_id, handle_name = arrow.target.split(":", 1)
                handle_id = f"{node_id}:{handle_name}"
                if handle_id not in diagram_dict.handles and node_id in nodes_dict:
                    # Create input handle
                    diagram_dict.handles[handle_id] = DomainHandle(
                        id=handle_id,
                        nodeId=node_id,
                        label=handle_name,
                        direction=HandleDirection.input,
                        dataType=DataType.any,
                        position="left",
                    )

        return backend_to_graphql(diagram_dict)

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

    def _create_arrow(self, arrow_data: dict[str, Any]) -> DomainArrow | None:
        """Create a domain arrow from arrow data."""
        source = arrow_data.get("source")
        target = arrow_data.get("target")

        if not source or not target:
            return None

        arrow_id = arrow_data.get(
            "id", self.arrow_builder.create_arrow_id(source, target)
        )

        # Extract contentType and label from arrow_data (they may be at the top level, not in data)
        content_type = arrow_data.get("contentType")
        label = arrow_data.get("label")

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

    # Backward compatibility methods (from registry.py)
    def list_formats(self) -> list[dict[str, str]]:
        """Backward compatibility alias for get_supported_formats."""
        return self.get_supported_formats()

    def convert(self, content: str, from_format: str, to_format: str) -> str:
        """Convert content from one format to another."""
        diagram = self.deserialize(content, from_format)
        return self.serialize(diagram, to_format)

    def get(self, format_id: str) -> "UnifiedDiagramConverter | None":
        """Get converter for format (backward compatibility)."""
        if format_id in self.strategies:
            self.set_format(format_id)
            return self
        return None

    def get_info(self, format_id: str) -> dict[str, str] | None:
        """Get format info (backward compatibility)."""
        strategy = self.strategies.get(format_id)
        return strategy.format_info if strategy else None


# Create a singleton instance to act as the registry
converter_registry = UnifiedDiagramConverter()
