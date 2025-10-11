"""Light YAML strategy - main orchestrator for simplified workflow format."""

from __future__ import annotations

import os
from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.compilation.prompt_compiler import PromptFileCompiler
from dipeo.domain.diagram.utils import _YamlMixin
from dipeo.domain.diagram.utils.conversion_utils import diagram_maps_to_arrays

from ..base_strategy import BaseConversionStrategy
from .parser import LightDiagramParser
from .serializer import LightDiagramSerializer
from .transformer import LightTransformer


class LightYamlStrategy(_YamlMixin, BaseConversionStrategy):
    """Simplified YAML strategy that uses labels instead of IDs.

    This strategy orchestrates the parsing, transformation, and serialization
    of light format diagrams using specialized modules:
    - parser: Parses raw YAML into LightDiagram
    - transformer: Transforms between LightDiagram and DomainDiagram
    - serializer: Serializes LightDiagram to export format
    """

    format_id = "light"
    format_info = {
        "name": "Light YAML",
        "description": "Simplified format using labels instead of IDs",
        "extension": ".light.yaml",
        "supports_import": "true",
        "supports_export": "true",
    }

    def __init__(self) -> None:
        super().__init__()
        self.parser = LightDiagramParser()
        self.transformer = LightTransformer()
        self.serializer = LightDiagramSerializer()

        # Initialize prompt compiler if enabled
        self._prompt_compiler: PromptFileCompiler | None = None
        self._enable_prompt_compilation = (
            os.getenv("DIPEO_COMPILE_PROMPTS", "true").lower() == "true"
        )
        if self._enable_prompt_compilation:
            self._prompt_compiler = PromptFileCompiler()

    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        """Deserialize light YAML content to DomainDiagram."""
        # Parse YAML content
        data = self.parse(content)
        data = self._clean_graphql_fields(data)

        # Parse to intermediate LightDiagram
        light_diagram = self.parser.parse_to_light_diagram(data)

        # Transform to DomainDiagram dictionary
        diagram_dict = self.transformer.light_diagram_to_dict(
            light_diagram, data, diagram_path, self._prompt_compiler
        )
        diagram_dict = self.transformer.apply_format_transformations(diagram_dict, data)

        # Convert to array-based format and validate
        array_based_dict = diagram_maps_to_arrays(diagram_dict)

        if "metadata" in diagram_dict:
            array_based_dict["metadata"] = diagram_dict["metadata"]

        return DomainDiagram.model_validate(array_based_dict)

    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Serialize DomainDiagram to light YAML format."""
        # Transform DomainDiagram to LightDiagram
        light_diagram = self.transformer.domain_to_light_diagram(diagram)

        # Serialize to export dictionary
        data = self.serializer.light_diagram_to_export_dict(light_diagram)

        # Format as YAML
        return self.format(data)

    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.8 if isinstance(data.get("nodes"), list) else 0.1

    def quick_match(self, content: str) -> bool:
        return "nodes:" in content and not content.lstrip().startswith(("{", "["))
