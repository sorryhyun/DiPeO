"""Validation utilities for handlers."""

import os
from pathlib import Path
from typing import Any


def validate_file_paths(
    file_paths: list[str] | str | None, must_exist: bool = False, base_dir: str | None = None
) -> tuple[list[str], str | None]:
    """Validate file paths and return normalized paths with optional error.

    Args:
        file_paths: Single path or list of paths to validate
        must_exist: If True, all paths must exist
        base_dir: Base directory for relative paths

    Returns:
        Tuple of (normalized_paths, error_message)
        error_message is None if validation passes

    Example:
        >>> validate_file_paths("/tmp/file.txt", must_exist=False)
        (['/tmp/file.txt'], None)
        >>> validate_file_paths(None)
        ([], 'No file paths provided')
    """
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

        # Resolve relative paths
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
    """Validate operation is in list of valid operations.

    Args:
        operation: Operation to validate
        valid_operations: List of valid operation names
        operation_label: Label for error message (default: "operation")

    Returns:
        Error message if invalid, None if valid

    Example:
        >>> validate_operation("read", ["read", "write", "append"])
        None
        >>> validate_operation("delete", ["read", "write"])
        "Invalid operation: delete. Valid operations: read, write"
    """
    if operation not in valid_operations:
        valid_ops = ", ".join(valid_operations)
        return f"Invalid {operation_label}: {operation}. Valid operations: {valid_ops}"
    return None


def validate_required_field(value: Any, field_name: str, allow_empty: bool = False) -> str | None:
    """Validate that required field is present and non-empty.

    Args:
        value: Field value to validate
        field_name: Name of field for error message
        allow_empty: If False, empty strings/lists also fail validation

    Returns:
        Error message if invalid, None if valid

    Example:
        >>> validate_required_field("value", "username")
        None
        >>> validate_required_field(None, "password")
        "No password provided"
        >>> validate_required_field("", "email", allow_empty=False)
        "No email provided"
    """
    if value is None:
        return f"No {field_name} provided"

    if not allow_empty:
        if (isinstance(value, str) and not value.strip()) or (
            isinstance(value, list | dict) and not value
        ):
            return f"No {field_name} provided"

    return None


def validate_config_field(config: dict[str, Any], field_name: str, config_type: str) -> str | None:
    """Validate that configuration contains required field.

    Args:
        config: Configuration dictionary
        field_name: Required field name
        config_type: Type of config for error message (e.g., "webhook", "shell")

    Returns:
        Error message if invalid, None if valid

    Example:
        >>> validate_config_field({"url": "http://..."}, "url", "webhook")
        None
        >>> validate_config_field({}, "command", "shell")
        "Shell config requires 'command' field"
    """
    if not config.get(field_name):
        return f"{config_type.capitalize()} config requires '{field_name}' field"
    return None
