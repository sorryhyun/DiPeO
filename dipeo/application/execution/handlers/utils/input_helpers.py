"""Input preparation utilities for handlers."""

from typing import Any


def extract_first_non_empty(inputs: dict[str, Any] | None) -> Any | None:
    """Extract first non-None value from inputs."""
    if not inputs:
        return None
    for _k, v in inputs.items():
        if v is not None:
            return v
    return None


def extract_content_value(input_val: Any) -> Any:
    """Extract content from nested dict wrappers (generated_code/content/value)."""
    if not isinstance(input_val, dict):
        return input_val

    actual_content = (
        input_val.get("generated_code") or input_val.get("content") or input_val.get("value")
    )

    if actual_content is not None:
        return actual_content

    return input_val


def prepare_template_values(inputs: dict[str, Any]) -> dict[str, Any]:
    """Unwrap envelope bodies for template rendering."""
    prepared = {}
    for key, value in inputs.items():
        if isinstance(value, dict) and "body" in value:
            prepared[key] = value["body"]
        else:
            prepared[key] = value
    return prepared


def get_input_by_priority(inputs: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Get first non-None input value from priority-ordered keys."""
    for key in keys:
        value = inputs.get(key)
        if value is not None:
            return value
    return default
