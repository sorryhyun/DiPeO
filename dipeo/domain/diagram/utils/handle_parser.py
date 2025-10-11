"""Parses and creates handle references."""

from __future__ import annotations

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import (
    DataType,
    HandleDirection,
    HandleLabel,
    NodeID,
)

from .handle_utils import create_handle_id

logger = get_module_logger(__name__)


class HandleParser:
    """Parses and creates handle references."""

    @staticmethod
    def parse_label_with_handle(
        label_raw: str, label2id: dict[str, str]
    ) -> tuple[str | None, str | None, str]:
        """Parse a label that may contain a handle suffix.

        Returns: (node_id, handle_name, node_label)
        """
        label = label_raw
        handle_from_split = None

        if label_raw not in label2id and "_" in label_raw:
            parts = label_raw.split("_")

            for i in range(len(parts) - 1, 0, -1):
                potential_label = "_".join(parts[:i])
                if potential_label in label2id:
                    label = potential_label
                    handle_from_split = "_".join(parts[i:])
                    break

                potential_label_with_spaces = " ".join(parts[:i])
                if potential_label_with_spaces in label2id:
                    label = potential_label_with_spaces
                    handle_from_split = "_".join(parts[i:])
                    break

        node_id = label2id.get(label)
        return node_id, handle_from_split, label

    @staticmethod
    def determine_handle_name(
        handle_from_split: str | None,
        arrow_data: dict[str, Any] | None = None,
        is_source: bool = True,
        default: str = "default",
    ) -> str:
        """Determine the handle name from split or arrow data."""
        if handle_from_split:
            # _first becomes first to distinguish from default inputs
            if handle_from_split == "_first":
                return "first"
            return handle_from_split
        elif is_source and arrow_data and "branch" in arrow_data:
            branch_value = arrow_data.get("branch")
            return (
                "condtrue"
                if branch_value == "true"
                else "condfalse"
                if branch_value == "false"
                else default
            )
        else:
            return default

    @staticmethod
    def create_handle_ids(
        source_node_id: str,
        target_node_id: str,
        source_handle: str = "default",
        target_handle: str = "default",
    ) -> tuple[str, str]:
        """Create handle IDs for source and target."""
        try:
            src_handle_enum = HandleLabel(source_handle)
        except ValueError:
            src_handle_enum = HandleLabel.DEFAULT

        try:
            dst_handle_enum = HandleLabel(target_handle)
        except ValueError:
            dst_handle_enum = HandleLabel.DEFAULT

        source_handle_id = create_handle_id(
            NodeID(source_node_id), src_handle_enum, HandleDirection.OUTPUT
        )
        target_handle_id = create_handle_id(
            NodeID(target_node_id), dst_handle_enum, HandleDirection.INPUT
        )

        return source_handle_id, target_handle_id

    @staticmethod
    def ensure_handle_exists(
        handle_ref: str,
        direction: HandleDirection,
        nodes_dict: dict[str, Any],
        handles_dict: dict[str, Any],
        arrow: dict[str, Any],
    ) -> None:
        """Ensure handle exists, creating if needed."""
        parts = handle_ref.split("_")
        if len(parts) >= 3 and parts[-1] in ["input", "output"]:
            return

        node_id = None
        handle_name = "default"

        for nid, node in nodes_dict.items():
            node_label = node.get("data", {}).get("label", nid) if "data" in node else nid
            for possible_handle in ["first", "default", "condtrue", "condfalse"]:
                if handle_ref == f"{node_label}_{possible_handle}":
                    node_id = nid
                    handle_name = possible_handle
                    break
            if node_id:
                break

        if not node_id:
            parts = handle_ref.rsplit("_", 1)
            if len(parts) == 2:
                node_label_or_id, handle_name = parts
                node_id = next(
                    (
                        nid
                        for nid, node in nodes_dict.items()
                        if nid == node_label_or_id
                        or ("data" in node and node["data"].get("label") == node_label_or_id)
                    ),
                    node_label_or_id,
                )
            else:
                node_id = handle_ref
                handle_name = "default"

        if handle_name in ["input", "output"]:
            handle_name = "default"

        try:
            handle_label = HandleLabel(handle_name)
        except ValueError:
            handle_label = handle_name

        actual_node_id = next(
            (n_id for n_id in nodes_dict if n_id.lower() == node_id.lower()), node_id
        )

        if not isinstance(handle_label, HandleLabel):
            try:
                handle_label = HandleLabel(str(handle_label))
            except ValueError:
                handle_label = HandleLabel.DEFAULT
        expected_handle_id = create_handle_id(NodeID(actual_node_id), handle_label, direction)

        if expected_handle_id not in handles_dict:
            logger.debug(
                f"Creating handle: handle_ref={handle_ref}, handle_name={handle_name}, handle_label={handle_label}, type={type(handle_label)}"
            )
            handles_dict[expected_handle_id] = {
                "id": expected_handle_id,
                "node_id": actual_node_id,
                "label": handle_label.value,
                "direction": direction.value,
                "data_type": DataType.ANY.value,
                "position": "right" if direction == HandleDirection.OUTPUT else "left",
            }

        if direction == HandleDirection.OUTPUT:
            arrow["source"] = expected_handle_id
        else:
            arrow["target"] = expected_handle_id
