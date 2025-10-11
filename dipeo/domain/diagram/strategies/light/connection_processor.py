from __future__ import annotations

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import HandleDirection, NodeType
from dipeo.diagram_generated.conversions import node_kind_to_domain_type
from dipeo.domain.diagram.models.format_models import LightDiagram
from dipeo.domain.diagram.utils import (
    ArrowDataProcessor,
    HandleParser,
    _node_id_map,
    parse_handle_id,
)

logger = get_module_logger(__name__)


class LightConnectionProcessor:
    """Processes connections and handles for light diagrams."""

    @staticmethod
    def process_light_connections(
        light_diagram: LightDiagram, nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)

        for idx, conn in enumerate(light_diagram.connections):
            src_raw = conn.from_
            dst_raw = conn.to

            src_id, src_handle_from_split, src_label = HandleParser.parse_label_with_handle(
                src_raw, label2id
            )
            dst_id, dst_handle_from_split, dst_label = HandleParser.parse_label_with_handle(
                dst_raw, label2id
            )

            if not (src_id and dst_id):
                logger.warning(
                    f"Skipping connection: could not find nodes for '{src_label}' -> '{dst_label}'"
                )
                continue

            conn_dict = conn.model_dump(by_alias=True, exclude={"from", "to", "label", "type"})
            arrow_data = conn_dict.get("data", {})

            src_handle = HandleParser.determine_handle_name(
                src_handle_from_split, arrow_data, is_source=True
            )
            dst_handle = HandleParser.determine_handle_name(
                dst_handle_from_split, arrow_data, is_source=False
            )

            arrow_data_copy = arrow_data.copy() if arrow_data else {}

            if dst_handle_from_split == "_first":
                arrow_data_copy["requires_first_execution"] = True

            if src_handle in ["condtrue", "condfalse"]:
                if "branch" not in arrow_data_copy:
                    arrow_data_copy["branch"] = "true" if src_handle == "condtrue" else "false"
                arrow_data_copy["is_conditional"] = True

            source_handle_id, target_handle_id = HandleParser.create_handle_ids(
                src_id, dst_id, src_handle, dst_handle
            )

            arrow_dict = ArrowDataProcessor.build_arrow_dict(
                arrow_data.get("id", f"arrow_{idx}"),
                source_handle_id,
                target_handle_id,
                arrow_data_copy,
                conn.type,
                conn.label,
            )

            arrows.append(arrow_dict)
        return arrows

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
        HandleParser.ensure_handle_exists(handle_ref, direction, nodes_dict, handles_dict, arrow)

    @staticmethod
    def preserve_condition_content_types(diagram_dict: dict[str, Any]) -> None:
        nodes_dict = diagram_dict["nodes"]
        arrows_dict = diagram_dict["arrows"]

        for _arrow_id, arrow in arrows_dict.items():
            if arrow.get("source"):
                try:
                    node_id, handle_label, _ = parse_handle_id(arrow["source"])
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
