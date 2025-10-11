from __future__ import annotations

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import HandleDirection, NodeType
from dipeo.diagram_generated.conversions import node_kind_to_domain_type
from dipeo.domain.diagram.models.format_models import LightDiagram
from dipeo.domain.diagram.utils import (
    HandleIdOperations,
    HandleLabelParser,
    HandleValidator,
    _node_id_map,
    create_arrow_dict,
)

logger = get_module_logger(__name__)


class LightConnectionProcessor:
    """Processes connections and handles for light diagrams."""

    @staticmethod
    def process_light_connections(
        light_diagram: LightDiagram, nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process light diagram connections into arrow dictionaries.

        Args:
            light_diagram: The light diagram with connections to process
            nodes: List of node dictionaries for label-to-ID mapping

        Returns:
            List of arrow dictionaries ready for diagram compilation
        """
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)

        for idx, conn in enumerate(light_diagram.connections):
            arrow = LightConnectionProcessor._process_single_connection(conn, idx, label2id)
            if arrow:
                arrows.append(arrow)
        return arrows

    @staticmethod
    def _process_single_connection(
        conn: Any, idx: int, label2id: dict[str, str]
    ) -> dict[str, Any] | None:
        """Process a single connection into an arrow dictionary.

        Args:
            conn: Connection object from light diagram
            idx: Connection index for generating arrow IDs
            label2id: Mapping from node labels to node IDs

        Returns:
            Arrow dictionary or None if connection is invalid
        """
        # Parse source and target endpoints
        source_endpoint = LightConnectionProcessor._parse_connection_endpoint(
            conn.from_, label2id, is_source=True
        )
        target_endpoint = LightConnectionProcessor._parse_connection_endpoint(
            conn.to, label2id, is_source=False
        )

        if not source_endpoint or not target_endpoint:
            logger.warning(
                f"Skipping connection: could not find nodes for "
                f"'{source_endpoint[3] if source_endpoint else conn.from_}' -> "
                f"'{target_endpoint[3] if target_endpoint else conn.to}'"
            )
            return None

        src_id, src_handle, _, _ = source_endpoint
        dst_id, dst_handle, dst_handle_from_split, _ = target_endpoint

        # Extract connection data
        conn_dict = conn.model_dump(by_alias=True, exclude={"from", "to", "label", "type"})
        arrow_data = conn_dict.get("data", {})

        # Build arrow data with special handling
        arrow_data_processed = LightConnectionProcessor._build_arrow_data(
            arrow_data, src_handle, dst_handle_from_split
        )

        # Create handle IDs
        source_handle_id, target_handle_id = HandleIdOperations.create_handle_ids(
            src_id, dst_id, src_handle, dst_handle
        )

        # Create arrow dictionary
        return create_arrow_dict(
            arrow_data.get("id", f"arrow_{idx}"),
            source_handle_id,
            target_handle_id,
            arrow_data_processed,
            conn.type,
            conn.label,
        )

    @staticmethod
    def _parse_connection_endpoint(
        endpoint_raw: str, label2id: dict[str, str], is_source: bool
    ) -> tuple[str, str, str, str] | None:
        """Parse a connection endpoint (source or target).

        Args:
            endpoint_raw: Raw endpoint string (e.g., "NodeLabel_handle")
            label2id: Mapping from node labels to node IDs
            is_source: True if parsing source endpoint, False for target

        Returns:
            Tuple of (node_id, handle_name, handle_from_split, node_label) or None if invalid
        """
        node_id, handle_from_split, node_label = HandleLabelParser.parse_label_with_handle(
            endpoint_raw, label2id
        )

        if not node_id:
            return None

        # Determine the actual handle name (may differ from split value)
        handle_name = HandleLabelParser.determine_handle_name(
            handle_from_split, {}, is_source=is_source
        )

        return (node_id, handle_name, handle_from_split, node_label)

    @staticmethod
    def _build_arrow_data(
        arrow_data: dict[str, Any] | None, src_handle: str, dst_handle_from_split: str
    ) -> dict[str, Any]:
        """Build arrow data with special handling for first execution and conditionals.

        Args:
            arrow_data: Original arrow data from connection
            src_handle: Source handle name
            dst_handle_from_split: Target handle name from label split

        Returns:
            Processed arrow data dictionary
        """
        arrow_data_copy = arrow_data.copy() if arrow_data else {}

        # Handle first execution requirement
        if dst_handle_from_split == "_first":
            arrow_data_copy["requires_first_execution"] = True

        # Handle conditional branches
        if src_handle in ["condtrue", "condfalse"]:
            if "branch" not in arrow_data_copy:
                arrow_data_copy["branch"] = "true" if src_handle == "condtrue" else "false"
            arrow_data_copy["is_conditional"] = True

        return arrow_data_copy

    @staticmethod
    def generate_missing_handles(diagram_dict: dict[str, Any]) -> None:
        from dipeo.domain.diagram.utils.shared_components import HandleGenerator

        handle_generator = HandleGenerator()

        for node_id, node in diagram_dict["nodes"].items():
            node_has_handles = any(
                handle.get("nodeId") == node_id or handle.get("node_id") == node_id
                for handle in diagram_dict["handles"].values()
            )
            if not node_has_handles:
                node_type_str = node.get("type", "code_job")
                try:
                    node_type = node_kind_to_domain_type(node_type_str)
                except ValueError:
                    node_type = NodeType.CODE_JOB

                handle_generator.generate_for_node(diagram_dict, node_id, node_type)

    @staticmethod
    def create_arrow_handles(diagram_dict: dict[str, Any]) -> None:
        nodes_dict = diagram_dict["nodes"]

        for _arrow_id, arrow in diagram_dict["arrows"].items():
            if "_" in arrow.get("source", ""):
                LightConnectionProcessor._ensure_handle_exists(
                    arrow["source"],
                    HandleDirection.OUTPUT,
                    nodes_dict,
                    diagram_dict["handles"],
                    arrow,
                )

            if "_" in arrow.get("target", ""):
                LightConnectionProcessor._ensure_handle_exists(
                    arrow["target"],
                    HandleDirection.INPUT,
                    nodes_dict,
                    diagram_dict["handles"],
                    arrow,
                )

    @staticmethod
    def _ensure_handle_exists(
        handle_ref: str,
        direction: HandleDirection,
        nodes_dict: dict[str, Any],
        handles_dict: dict[str, Any],
        arrow: dict[str, Any],
    ) -> None:
        HandleValidator.ensure_handle_exists(handle_ref, direction, nodes_dict, handles_dict, arrow)

    @staticmethod
    def preserve_condition_content_types(diagram_dict: dict[str, Any]) -> None:
        nodes_dict = diagram_dict["nodes"]
        arrows_dict = diagram_dict["arrows"]

        for _arrow_id, arrow in arrows_dict.items():
            if arrow.get("source"):
                try:
                    node_id, handle_label, _ = HandleIdOperations.parse_handle_id(arrow["source"])
                    source_node = nodes_dict.get(node_id)

                    if (
                        source_node
                        and source_node.get("type") == "condition"
                        and handle_label in ["condtrue", "condfalse"]
                    ):
                        input_content_types = []
                        for other_arrow in arrows_dict.values():
                            if (
                                other_arrow.get("target")
                                and node_id in other_arrow["target"]
                                and other_arrow.get("content_type")
                            ):
                                input_content_types.append(other_arrow["content_type"])

                        if input_content_types and all(
                            ct == input_content_types[0] for ct in input_content_types
                        ):
                            arrow["content_type"] = input_content_types[0]
                except Exception:
                    pass
