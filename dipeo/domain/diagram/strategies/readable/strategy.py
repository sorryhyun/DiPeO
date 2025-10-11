"""Readable YAML strategy - main orchestrator for human-friendly workflow format."""

from __future__ import annotations

from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.utils import _YamlMixin
from dipeo.domain.diagram.utils.conversion import diagram_maps_to_arrays

from ..base_strategy import BaseConversionStrategy
from .parser import ReadableParser
from .serializer import ReadableSerializer
from .transformer import ReadableTransformer


class ReadableYamlStrategy(_YamlMixin, BaseConversionStrategy):
    """Human-friendly workflow YAML strategy.

    This strategy orchestrates the parsing, transformation, and serialization
    of readable format diagrams using specialized modules:
    - parser: Parses raw YAML into ReadableDiagram
    - transformer: Transforms between ReadableDiagram and DomainDiagram
    - serializer: Serializes ReadableDiagram to export format
    """

    format_id = "readable"
    format_info = {
        "name": "Readable Workflow",
        "description": "Human-friendly workflow format",
        "extension": ".readable.yaml",
        "supports_import": True,
        "supports_export": True,
    }

    def __init__(self):
        super().__init__()
        self.parser = ReadableParser()
        self.transformer = ReadableTransformer()
        self.serializer = ReadableSerializer()

    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        """Deserialize readable YAML content to DomainDiagram."""
        # Parse YAML content
        data = self.parse(content)
        data = self._clean_graphql_fields(data)

        # Parse to intermediate ReadableDiagram
        readable_diagram = self.parser.parse_to_readable_diagram(data)

        # Transform to DomainDiagram dictionary
        diagram_dict = self.transformer.readable_diagram_to_dict(readable_diagram, data)
        diagram_dict = self.transformer.apply_format_transformations(diagram_dict, data)

        # Convert to array-based format and validate
        array_based_dict = diagram_maps_to_arrays(diagram_dict)

        if "metadata" in diagram_dict:
            array_based_dict["metadata"] = diagram_dict["metadata"]

        return DomainDiagram.model_validate(array_based_dict)

    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Serialize DomainDiagram to readable YAML format."""
        # Transform DomainDiagram to ReadableDiagram
        readable_diagram = self.transformer.domain_to_readable_diagram(diagram)

        # Serialize to export dictionary
        data = self.serializer.readable_diagram_to_export_dict(readable_diagram)

        # Format as YAML
        return self.format(data)

    def detect_confidence(self, data: dict[str, Any]) -> float:
        """Detect if data matches readable format and return confidence score."""
        if data.get("format") == "readable" or data.get("version") == "readable":
            return 0.95
        if "nodes" in data and "flow" in data:
            nodes = data.get("nodes", [])
            if isinstance(nodes, list) and nodes:
                first_node = nodes[0]
                if isinstance(first_node, dict) and len(first_node) == 1:
                    return 0.85
            return 0.7
        return 0.1

    def quick_match(self, content: str) -> bool:
        """Quick check if content matches readable format."""
        if "version: readable" in content or "format: readable" in content:
            return True
        return "nodes:" in content and "flow:" in content and "persons:" in content

    def parse(self, content: str) -> dict[str, Any]:
        """Parse YAML content to dictionary."""
        return super().parse(content)

    def format(self, data: dict[str, Any]) -> str:
        """Format dictionary to YAML string."""
        return super().format(data)
