"""Maps node fields between different formats and node types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from dipeo.diagram_generated import NodeType


@dataclass
class FieldMapping:
    """Defines field mapping rules for a node type."""

    import_renames: dict[str, str] = field(default_factory=dict)
    import_defaults: dict[str, Any] = field(default_factory=dict)
    import_removes: list[str] = field(default_factory=list)
    export_renames: dict[str, str] = field(default_factory=dict)
    export_removes: list[str] = field(default_factory=list)
    custom_import: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    custom_export: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _person_job_import_transform(props: dict[str, Any]) -> dict[str, Any]:
    """Handle complex PERSON_JOB import transformations."""
    if "memory_config" in props:
        props.pop("memory_config")

    if "memory_profile" in props:
        profile_str = props.pop("memory_profile")
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

    if "memory_settings" in props:
        props.pop("memory_settings")

    return props


def _job_import_transform(props: dict[str, Any]) -> dict[str, Any]:
    """Handle 'job' node type special case."""
    if "code" in props and "code_type" in props:
        if "language" not in props:
            props["language"] = props.pop("code_type")
    return props


FIELD_MAPPINGS: dict[str, FieldMapping] = {
    NodeType.START.value: FieldMapping(
        import_defaults={"custom_data": {}, "output_data_structure": {}},
    ),
    NodeType.ENDPOINT.value: FieldMapping(
        import_renames={"file_path": "file_name"},
        export_renames={"file_name": "file_path"},
    ),
    "job": FieldMapping(
        custom_import=_job_import_transform,
    ),
    NodeType.CODE_JOB.value: FieldMapping(
        import_renames={"code_type": "language"},
        export_renames={"language": "code_type"},
    ),
    NodeType.DB.value: FieldMapping(
        import_renames={"source_details": "file"},
        export_renames={"file": "source_details"},
    ),
    NodeType.JSON_SCHEMA_VALIDATOR.value: FieldMapping(
        import_renames={"strict": "strict_mode"},
        export_renames={"strict_mode": "strict"},
    ),
    NodeType.PERSON_JOB.value: FieldMapping(
        import_removes=["memory_config", "memory_settings"],
        export_removes=["memory_config", "memory_settings"],
        custom_import=_person_job_import_transform,
    ),
}


class NodeFieldMapper:
    """Maps node fields between different formats and node types."""

    @staticmethod
    def map_import_fields(node_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Map fields during import based on node type."""
        mapping = FIELD_MAPPINGS.get(node_type)
        if not mapping:
            return props

        for old_name, new_name in mapping.import_renames.items():
            if old_name in props and new_name not in props:
                props[new_name] = props.pop(old_name)

        for field_name, default_value in mapping.import_defaults.items():
            props.setdefault(field_name, default_value)

        for field_name in mapping.import_removes:
            props.pop(field_name, None)

        if mapping.custom_import:
            props = mapping.custom_import(props)

        return props

    @staticmethod
    def map_export_fields(node_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Map fields during export based on node type."""
        mapping = FIELD_MAPPINGS.get(node_type)
        if not mapping:
            return props

        for old_name, new_name in mapping.export_renames.items():
            if old_name in props:
                if new_name not in props:
                    props[new_name] = props.pop(old_name)
                else:
                    props[new_name] = props[old_name]

        for field_name in mapping.export_removes:
            props.pop(field_name, None)

        if mapping.custom_export:
            props = mapping.custom_export(props)

        return props
