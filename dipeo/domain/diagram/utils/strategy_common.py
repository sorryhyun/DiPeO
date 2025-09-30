"""Common utilities for diagram conversion strategies."""

from __future__ import annotations

import logging
from typing import Any

from dipeo.diagram_generated import (
    ContentType,
    DataType,
    HandleDirection,
    HandleLabel,
    NodeID,
    NodeType,
)

from .handle_utils import create_handle_id

logger = logging.getLogger(__name__)


class NodeFieldMapper:
    """Maps node fields between different formats and node types."""

    @staticmethod
    def map_import_fields(node_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Map fields during import based on node type."""
        if node_type == NodeType.START.value:
            props.setdefault("custom_data", {})
            props.setdefault("output_data_structure", {})
        elif node_type == NodeType.ENDPOINT.value:
            if "file_path" in props and "file_name" not in props:
                props["file_name"] = props.pop("file_path")
        elif node_type == "job":
            if "code" in props:
                node_type = NodeType.CODE_JOB.value
                if "code_type" in props:
                    props["language"] = props.pop("code_type")
        elif node_type == NodeType.CODE_JOB.value:
            if "code_type" in props and "language" not in props:
                props["language"] = props.pop("code_type")
        elif node_type == NodeType.DB.value:
            if "source_details" in props and "file" not in props:
                props["file"] = props.pop("source_details")
        elif node_type == NodeType.JSON_SCHEMA_VALIDATOR.value:
            # Map 'strict' to 'strict_mode' for backward compatibility
            if "strict" in props and "strict_mode" not in props:
                props["strict_mode"] = props.pop("strict")
        elif node_type == NodeType.PERSON_JOB.value:
            # Remove deprecated memory fields
            if "memory_config" in props:
                props.pop("memory_config")

            # Convert legacy memory_profile to memorize_to if present
            if "memory_profile" in props:
                profile_str = props.pop("memory_profile")

                # Map legacy profiles to new memorize_to values
                profile_to_memorize = {
                    "FULL": "ALL_MESSAGES",
                    "FOCUSED": "CONVERSATION_PAIRS",
                    "MINIMAL": "SYSTEM_AND_ME",
                    "GOLDFISH": "GOLDFISH",
                    "ONLY_ME": "SENT_TO_ME",
                    "ONLY_I_SENT": "SENT_BY_ME",
                }

                if profile_str in profile_to_memorize and "memorize_to" not in props:
                    props["memorize_to"] = profile_to_memorize[profile_str]

            # Remove memory_settings if present (no longer used)
            if "memory_settings" in props:
                props.pop("memory_settings")

        return props

    @staticmethod
    def map_export_fields(node_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Map fields during export based on node type."""
        if node_type == NodeType.ENDPOINT.value and "file_name" in props:
            props["file_path"] = props.pop("file_name")
        elif node_type == NodeType.CODE_JOB.value:
            if "language" in props and "code_type" not in props:
                props["code_type"] = props["language"]
        elif node_type == NodeType.DB.value and "file" in props:
            props["source_details"] = props.pop("file")
        elif node_type == NodeType.JSON_SCHEMA_VALIDATOR.value:
            # Map 'strict_mode' back to 'strict' for export compatibility
            if "strict_mode" in props and "strict" not in props:
                props["strict"] = props["strict_mode"]
        elif node_type == NodeType.PERSON_JOB.value:
            if "memory_config" in props:
                props.pop("memory_config")
            if "memory_settings" in props:
                props.pop("memory_settings")

        return props


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


class PersonExtractor:
    """Extracts person data from different formats."""

    @staticmethod
    def extract_from_dict(
        persons_data: dict[str, Any], is_light_format: bool = False
    ) -> dict[str, Any]:
        """Extract persons from dictionary format."""
        persons_dict = {}

        for person_key, person_config in persons_data.items():
            llm_config = {
                "service": person_config.get("service", "openai"),
                "model": person_config.get("model", "gpt-4-mini"),
                "api_key_id": person_config.get("api_key_id", "default"),
            }
            if "system_prompt" in person_config:
                llm_config["system_prompt"] = person_config["system_prompt"]
            if "prompt_file" in person_config:
                llm_config["prompt_file"] = person_config["prompt_file"]

            if is_light_format:
                # Light format: key is label, used directly as person_id
                person_id = person_config.get("id", person_key)
                person_dict = {
                    "id": person_id,
                    "label": person_key,
                    "type": "person",
                    "llm_config": llm_config,
                }
            else:
                person_id = person_key
                person_dict = {
                    "id": person_id,
                    "label": person_config.get("label", person_key),
                    "type": "person",
                    "llm_config": llm_config,
                }

            persons_dict[person_id] = person_dict

        return persons_dict

    @staticmethod
    def extract_from_list(persons_data: list[Any]) -> dict[str, Any]:
        """Extract persons from list format (readable or native array)."""
        persons_dict = {}

        for person_item in persons_data:
            if isinstance(person_item, dict):
                if "id" in person_item and "llm_config" in person_item:
                    person_id = person_item["id"]
                    persons_dict[person_id] = person_item
                else:
                    # Readable format with person name as key
                    for person_name, person_config in person_item.items():
                        llm_config = {
                            "service": person_config.get("service", "openai"),
                            "model": person_config.get("model", "gpt-4-mini"),
                            "api_key_id": person_config.get("api_key_id", "default"),
                        }
                        if "system_prompt" in person_config:
                            llm_config["system_prompt"] = person_config["system_prompt"]
                        if "prompt_file" in person_config:
                            llm_config["prompt_file"] = person_config["prompt_file"]

                        person_id = f"person_{person_name}"

                        person_dict = {
                            "id": person_id,
                            "label": person_name,
                            "type": "person",
                            "llm_config": llm_config,
                        }
                        persons_dict[person_id] = person_dict

        return persons_dict


class ArrowDataProcessor:
    """Processes arrow data for import/export."""

    @staticmethod
    def build_arrow_dict(
        arrow_id: str,
        source_handle_id: str,
        target_handle_id: str,
        arrow_data: dict[str, Any] | None = None,
        content_type: str | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        """Build arrow dictionary."""
        arrow_dict = {
            "id": arrow_id,
            "source": source_handle_id,
            "target": target_handle_id,
        }

        if arrow_data:
            arrow_dict["data"] = arrow_data

        if content_type:
            arrow_dict["content_type"] = content_type

        if label:
            arrow_dict["label"] = label

        if "content_type" not in arrow_dict and arrow_dict.get("content_type") is None:
            arrow_dict["content_type"] = ContentType.RAW_TEXT

        return arrow_dict

    @staticmethod
    def should_include_branch_data(source_handle: str, arrow_data: dict[str, Any]) -> bool:
        """Check if branch data should be included."""
        return "branch" in arrow_data and source_handle not in ["condtrue", "condfalse"]


def process_dotted_keys(props: dict[str, Any]) -> dict[str, Any]:
    """Convert dot notation keys to nested dictionaries."""
    dotted_keys = [k for k in props if "." in k]
    for key in dotted_keys:
        value = props.pop(key)
        parts = key.split(".")
        current = props
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return props
