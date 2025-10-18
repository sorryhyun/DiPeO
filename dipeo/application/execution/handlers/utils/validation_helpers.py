"""Validation utilities for handlers."""

import os
from typing import Any


def validate_file_paths(
    file_paths: list[str] | str | None,
    must_exist: bool = False,
    base_dir: str | None = None,
) -> tuple[list[str], str | None]:
    """Validate and normalize file paths, returning (paths, error_msg)."""
    if file_paths is None:
        return ([], "No file paths provided")

    if isinstance(file_paths, str):
        file_paths = [file_paths]
    elif not isinstance(file_paths, list):
        return ([], f"Invalid file_paths type: {type(file_paths)}")

    if not file_paths:
        return ([], "No file paths provided")

    normalized_paths = []
    for path in file_paths:
        if not path or not isinstance(path, str):
            return ([], f"Invalid path: {path}")

        if base_dir and not os.path.isabs(path):
            full_path = os.path.join(base_dir, path)
        else:
            full_path = path

        if must_exist and not os.path.exists(full_path):
            return ([], f"File does not exist: {path}")

        normalized_paths.append(full_path)

    return (normalized_paths, None)


def validate_operation(
    operation: str, valid_operations: list[str], operation_label: str = "operation"
) -> str | None:
    """Check if operation is valid, returning error message if not."""
    if operation not in valid_operations:
        valid_ops = ", ".join(valid_operations)
        return f"Invalid {operation_label}: {operation}. Valid operations: {valid_ops}"
    return None


def validate_required_field(value: Any, field_name: str, allow_empty: bool = False) -> str | None:
    """Check required field is present and non-empty."""
    if value is None:
        return f"No {field_name} provided"

    if not allow_empty:
        if (isinstance(value, str) and not value.strip()) or (
            isinstance(value, list | dict) and not value
        ):
            return f"No {field_name} provided"

    return None


def validate_config_field(config: dict[str, Any], field_name: str, config_type: str) -> str | None:
    """Check config contains required field."""
    if not config.get(field_name):
        return f"{config_type.capitalize()} config requires '{field_name}' field"
    return None
