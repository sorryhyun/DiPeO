from __future__ import annotations

import os
from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.compilation.prompt_compiler import PromptFileCompiler
from dipeo.domain.diagram.utils import _YamlMixin
from dipeo.domain.diagram.utils.conversion_utils import diagram_maps_to_arrays

from ..base_strategy import BaseConversionStrategy
from .connection_processor import LightConnectionProcessor
from .parser import LightDiagramParser
from .serializer import LightDiagramSerializer


class LightYamlStrategy(_YamlMixin, BaseConversionStrategy):
    """Simplified YAML that uses labels instead of IDs."""

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
        self._prompt_compiler: PromptFileCompiler | None = None
        self._enable_prompt_compilation = (
            os.getenv("DIPEO_COMPILE_PROMPTS", "true").lower() == "true"
        )
        if self._enable_prompt_compilation:
            self._prompt_compiler = PromptFileCompiler()

    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        data = self.parse(content)
        data = self._clean_graphql_fields(data)
        light_diagram = LightDiagramParser.parse_to_light_diagram(data)
        diagram_dict = self._light_diagram_to_dict(light_diagram, data, diagram_path)
        diagram_dict = self._apply_format_transformations(diagram_dict, data)
        array_based_dict = diagram_maps_to_arrays(diagram_dict)

        if "metadata" in diagram_dict:
            array_based_dict["metadata"] = diagram_dict["metadata"]

        return DomainDiagram.model_validate(array_based_dict)

    def _light_diagram_to_dict(
        self,
        light_diagram: Any,
        original_data: dict[str, Any],
        diagram_path: str | None = None,
    ) -> dict[str, Any]:
        nodes_list = []
        for index, node in enumerate(light_diagram.nodes):
            node_dict = node.model_dump(exclude_none=True)

            props = LightDiagramParser.extract_node_props_from_light(node_dict)

            if node.label:
                props["label"] = node.label

            processed_node = {
                "id": LightDiagramParser.create_node_id(index),
                "type": node.type.lower() if isinstance(node.type, str) else node.type,
                "position": node.position or {"x": 0, "y": 0},
                "data": props,
            }
            nodes_list.append(processed_node)

        if self._prompt_compiler and self._enable_prompt_compilation:
            effective_path = diagram_path or original_data.get("metadata", {}).get("diagram_id")
            nodes_list = self._prompt_compiler.resolve_prompt_files(nodes_list, effective_path)

        nodes_dict = LightDiagramParser.build_nodes_dict(nodes_list)

        arrows_list = LightConnectionProcessor.process_light_connections(light_diagram, nodes_list)
        arrows_dict = LightDiagramParser.build_arrows_dict(arrows_list)

        handles_dict = LightDiagramParser.extract_handles_dict(original_data)
        persons_dict = LightDiagramParser.extract_persons_dict(original_data)

        return {
            "nodes": nodes_dict,
            "arrows": arrows_dict,
            "handles": handles_dict,
            "persons": persons_dict,
            "metadata": light_diagram.metadata,
        }

    def _apply_format_transformations(
        self, diagram_dict: dict[str, Any], original_data: dict[str, Any]
    ) -> dict[str, Any]:
        person_label_to_id: dict[str, str] = {}
        if diagram_dict["persons"]:
            for person_id, person_data in diagram_dict["persons"].items():
                label = person_data.get("label", person_id)
                person_label_to_id[label] = person_id

        if person_label_to_id:
            for _node_id, node in diagram_dict["nodes"].items():
                if node.get("type") == "person_job":
                    person_ref = None
                    if "person" in node:
                        person_ref = node["person"]
                        if person_ref in person_label_to_id:
                            node["person"] = person_label_to_id[person_ref]
                    elif (
                        "props" in node
                        and isinstance(node["props"], dict)
                        and "person" in node["props"]
                    ):
                        person_ref = node["props"]["person"]
                        if person_ref in person_label_to_id:
                            node["props"]["person"] = person_label_to_id[person_ref]
                    elif (
                        "data" in node
                        and isinstance(node["data"], dict)
                        and "person" in node["data"]
                    ):
                        person_ref = node["data"]["person"]
                        if person_ref in person_label_to_id:
                            node["data"]["person"] = person_label_to_id[person_ref]

        LightConnectionProcessor.generate_missing_handles(diagram_dict)
        LightConnectionProcessor.create_arrow_handles(diagram_dict)
        LightConnectionProcessor.preserve_condition_content_types(diagram_dict)

        return diagram_dict

    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        light_diagram = LightDiagramSerializer.domain_to_light_diagram(diagram)
        data = LightDiagramSerializer.light_diagram_to_export_dict(light_diagram)
        return self.format(data)

    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.8 if isinstance(data.get("nodes"), list) else 0.1

    def quick_match(self, content: str) -> bool:
        return "nodes:" in content and not content.lstrip().startswith(("{", "["))
