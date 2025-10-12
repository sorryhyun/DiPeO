"""Unified node dictionary building utilities."""

from __future__ import annotations

from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.conversions import node_kind_to_domain_type
from dipeo.domain.diagram.utils.shared_components import PositionCalculator

logger = get_module_logger(__name__)

__all__ = (
    "NodeDictionaryBuilder",
    "nodes_list_to_dict",
)


class NodeDictionaryBuilder:
    """Builds node dictionaries from node lists with format-specific processing."""

    @staticmethod
    def build_simple(nodes_list: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Build a simple node dictionary indexed by node ID.

        This method creates a basic ID-based dictionary without any enrichment
        or validation. Used primarily by the light format parser.

        Args:
            nodes_list: List of node dictionaries, each with an 'id' key

        Returns:
            Dictionary mapping node IDs to node dictionaries
        """
        return {node["id"]: node for node in nodes_list}

    @staticmethod
    def build_with_enrichment(
        nodes_list: list[dict[str, Any]],
        position_calculator: PositionCalculator | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Build node dictionary with position calculation and type validation.

        This method performs enrichment including:
        - Automatic position calculation for nodes without positions
        - Node type validation with fallback to default type
        - Field exclusion (id, type, position, handles, arrows)
        - Type string normalization (lowercase, 'job' -> 'person_job')

        Used primarily by the readable format transformer.

        Args:
            nodes_list: List of node dictionaries
            position_calculator: Optional position calculator (creates default if None)

        Returns:
            Dictionary mapping node IDs to enriched node dictionaries
        """
        if position_calculator is None:
            position_calculator = PositionCalculator()

        nodes_dict = {}

        for index, node_data in enumerate(nodes_list):
            if "id" not in node_data:
                continue

            node_id = node_data["id"]
            node_type_str = node_data.get("type", "person_job")

            # Handle 'job' as alias for 'person_job'
            if node_type_str == "job":
                node_type_str = "person_job"

            # Validate node type
            try:
                node_kind_to_domain_type(node_type_str)
            except ValueError:
                logger.warning(f"Unknown node type '{node_type_str}', defaulting to 'person_job'")
                node_type_str = "person_job"
                node_kind_to_domain_type(node_type_str)

            # Calculate position if not provided
            position = node_data.get("position")
            if not position:
                position = position_calculator.calculate_grid_position(index)

            # Extract properties excluding system fields
            exclude_fields = {"id", "type", "position", "handles", "arrows"}
            properties = {k: v for k, v in node_data.items() if k not in exclude_fields}

            nodes_dict[node_id] = {
                "id": node_id,
                "type": node_type_str.lower(),
                "position": position,
                "data": properties,
            }

        return nodes_dict


def nodes_list_to_dict(nodes_list: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Convert a list of nodes to a simple dictionary indexed by node ID.

    This is a convenience function that wraps NodeDictionaryBuilder.build_simple().
    Useful for simple conversions without enrichment.

    Args:
        nodes_list: List of node dictionaries, each with an 'id' key

    Returns:
        Dictionary mapping node IDs to node dictionaries
    """
    return NodeDictionaryBuilder.build_simple(nodes_list)
