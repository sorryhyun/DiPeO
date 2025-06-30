"""Shared utility functions used across the DiPeO system."""

import json
from datetime import UTC, datetime
from typing import Any, TypeVar

T = TypeVar("T")


def ensure_list(value: T | list[T] | None) -> list[T]:
    """Ensure a value is a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_json_loads(data: str | bytes, default: Any = None) -> Any:
    """Safely load JSON data, returning default on error."""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def safe_json_dumps(data: Any, indent: int | None = None) -> str:
    """Safely dump data to JSON string."""
    try:
        return json.dumps(data, indent=indent, default=str)
    except (TypeError, ValueError):
        return "{}"


def get_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    import re
    
    # Insert underscore before uppercase letters (except at start)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    # Insert underscore before uppercase letters followed by lowercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def merge_dicts(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


__all__ = [
    "ensure_list",
    "safe_json_loads",
    "safe_json_dumps",
    "get_timestamp",
    "truncate_string",
    "snake_to_camel",
    "camel_to_snake",
    "merge_dicts",
]