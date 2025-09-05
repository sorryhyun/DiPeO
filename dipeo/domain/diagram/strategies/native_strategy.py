from __future__ import annotations

import logging
from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.models.format_models import NativeDiagram
from dipeo.domain.diagram.utils import _JsonMixin

from .base_strategy import BaseConversionStrategy

log = logging.getLogger(__name__)


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

    # ---- Typed deserialization ------------------------------------------------ #
    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        """Deserialize native format JSON to DomainDiagram."""
        # Parse JSON
        data = self.parse(content)

        # Clean GraphQL fields
        data = self._clean_graphql_fields(data)

        # NativeDiagram is just DomainDiagram, so we can validate directly
        # First handle the case where nodes might be a dict instead of list
        if "nodes" in data and isinstance(data["nodes"], dict):
            # Convert dict format to list format
            nodes_list = []
            for node_id, node_data in data["nodes"].items():
                if isinstance(node_data, dict):
                    node_data["id"] = node_id
                    nodes_list.append(node_data)
            data["nodes"] = nodes_list

        # Similarly for arrows
        if "arrows" in data and isinstance(data["arrows"], dict):
            arrows_list = []
            for arrow_id, arrow_data in data["arrows"].items():
                if isinstance(arrow_data, dict):
                    arrow_data["id"] = arrow_id
                    arrows_list.append(arrow_data)
            data["arrows"] = arrows_list

        # Similarly for handles
        if "handles" in data and isinstance(data["handles"], dict):
            handles_list = []
            for handle_id, handle_data in data["handles"].items():
                if isinstance(handle_data, dict):
                    handle_data["id"] = handle_id
                    handles_list.append(handle_data)
            data["handles"] = handles_list

        # Similarly for persons
        if "persons" in data and isinstance(data["persons"], dict):
            persons_list = []
            for person_id, person_data in data["persons"].items():
                if isinstance(person_data, dict):
                    person_data["id"] = person_id
                    persons_list.append(person_data)
            data["persons"] = persons_list

        # Create NativeDiagram (which is just a DomainDiagram)
        try:
            native_diagram = NativeDiagram(**data)
            # NativeDiagram IS a DomainDiagram, just return it
            return native_diagram
        except Exception as e:
            log.error(f"Failed to parse native diagram: {e}")
            raise ValueError(f"Invalid native diagram format: {e}") from e

    # ---- Typed serialization -------------------------------------------------- #
    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Serialize DomainDiagram to native format JSON."""
        # NativeDiagram is just DomainDiagram, so use it directly
        native_diagram = NativeDiagram(**diagram.model_dump())

        # Convert to dict format with nodes/arrows/etc as dicts keyed by ID
        data = native_diagram.model_dump(by_alias=True, exclude_none=True)

        # Convert lists to dict format for native style
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

        # Format as JSON
        return self.format(data)

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.95 if {"nodes", "arrows"}.issubset(data) else 0.1

    def quick_match(self, content: str) -> bool:
        return content.lstrip().startswith("{") and '"nodes"' in content
