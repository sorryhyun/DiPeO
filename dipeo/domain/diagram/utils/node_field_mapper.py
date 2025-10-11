"""Maps node fields between different formats and node types."""

from __future__ import annotations

from typing import Any

from dipeo.diagram_generated import NodeType


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
