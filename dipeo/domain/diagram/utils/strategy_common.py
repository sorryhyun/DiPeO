"""Common utilities for diagram conversion strategies."""

from __future__ import annotations

from typing import Any


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
