from __future__ import annotations

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.models.format_models import NativeDiagram
from dipeo.domain.diagram.utils import _JsonMixin

from .base_strategy import BaseConversionStrategy

logger = get_module_logger(__name__)


class NativeJsonStrategy(_JsonMixin, BaseConversionStrategy):
    """Canonical domain JSON."""

    format_id = "native"
    format_info = {
        "name": "Domain JSON",
        "description": "Canonical format for diagram structure and execution",
        "extension": ".json",
        "supports_import": True,
        "supports_export": True,
    }

    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        data = self.parse(content)
        data = self._clean_graphql_fields(data)
        if "nodes" in data and isinstance(data["nodes"], dict):
            nodes_list = []
            for node_id, node_data in data["nodes"].items():
                if isinstance(node_data, dict):
                    node_data["id"] = node_id
                    nodes_list.append(node_data)
            data["nodes"] = nodes_list

        if "arrows" in data and isinstance(data["arrows"], dict):
            arrows_list = []
            for arrow_id, arrow_data in data["arrows"].items():
                if isinstance(arrow_data, dict):
                    arrow_data["id"] = arrow_id
                    arrows_list.append(arrow_data)
            data["arrows"] = arrows_list

        if "handles" in data and isinstance(data["handles"], dict):
            handles_list = []
            for handle_id, handle_data in data["handles"].items():
                if isinstance(handle_data, dict):
                    handle_data["id"] = handle_id
                    handles_list.append(handle_data)
            data["handles"] = handles_list

        if "persons" in data and isinstance(data["persons"], dict):
            persons_list = []
            for person_id, person_data in data["persons"].items():
                if isinstance(person_data, dict):
                    person_data["id"] = person_id
                    persons_list.append(person_data)
            data["persons"] = persons_list

        try:
            native_diagram = NativeDiagram(**data)
            return native_diagram
        except Exception as e:
            logger.error(f"Failed to parse native diagram: {e}")
            raise ValueError(f"Invalid native diagram format: {e}") from e

    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        native_diagram = NativeDiagram(**diagram.model_dump())

        data = native_diagram.model_dump(by_alias=True, exclude_none=True)

        if "nodes" in data and isinstance(data["nodes"], list):
            nodes_dict = {}
            for node in data["nodes"]:
                node_id = node.pop("id")
                nodes_dict[node_id] = node
            data["nodes"] = nodes_dict

        if "arrows" in data and isinstance(data["arrows"], list):
            arrows_dict = {}
            for arrow in data["arrows"]:
                arrow_id = arrow.pop("id")
                arrows_dict[arrow_id] = arrow
            data["arrows"] = arrows_dict

        if "handles" in data and isinstance(data["handles"], list):
            handles_dict = {}
            for handle in data["handles"]:
                handle_id = handle.pop("id")
                handles_dict[handle_id] = handle
            data["handles"] = handles_dict

        if "persons" in data and isinstance(data["persons"], list):
            persons_dict = {}
            for person in data["persons"]:
                person_id = person.pop("id")
                persons_dict[person_id] = person
            data["persons"] = persons_dict

        return self.format(data)

    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.95 if {"nodes", "arrows"}.issubset(data) else 0.1

    def quick_match(self, content: str) -> bool:
        return content.lstrip().startswith("{") and '"nodes"' in content
