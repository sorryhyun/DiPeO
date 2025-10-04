"""Input preparation utilities for handlers."""

from typing import Any


def extract_first_non_empty(inputs: dict[str, Any] | None) -> Any | None:
    """Extract first non-None value from inputs dictionary.

    Args:
        inputs: Dictionary of input values

    Returns:
        First non-None value found, or None if all values are None

    Example:
        >>> extract_first_non_empty({"a": None, "b": "value", "c": "other"})
        'value'
        >>> extract_first_non_empty({"a": None, "b": None})
        None
    """
    if not inputs:
        return None
    for _k, v in inputs.items():
        if v is not None:
            return v
    return None


def extract_content_value(input_val: Any) -> Any:
    """Extract actual content from nested input value.

    Handles cases where input is wrapped in a dict with 'content', 'value',
    or 'generated_code' keys.

    Args:
        input_val: Input value (may be nested dict or direct value)

    Returns:
        Extracted content value

    Example:
        >>> extract_content_value({"content": "actual value"})
        'actual value'
        >>> extract_content_value({"generated_code": "code"})
        'code'
        >>> extract_content_value("direct value")
        'direct value'
    """
    if not isinstance(input_val, dict):
        return input_val

    actual_content = (
        input_val.get("generated_code") or input_val.get("content") or input_val.get("value")
    )

    if actual_content is not None:
        return actual_content

    return input_val


def prepare_template_values(inputs: dict[str, Any]) -> dict[str, Any]:
    """Prepare input values for template processing.

    This handles nested structures and makes node outputs available.

    Args:
        inputs: Raw input dictionary

    Returns:
        Prepared inputs suitable for template rendering

    Example:
        >>> prepare_template_values({"key": {"body": "value"}})
        {'key': 'value'}
    """
    prepared = {}
    for key, value in inputs.items():
        if isinstance(value, dict) and "body" in value:
            prepared[key] = value["body"]
        else:
            prepared[key] = value
    return prepared


def get_input_by_priority(inputs: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Get input value by checking keys in priority order.

    Args:
        inputs: Input dictionary
        *keys: Keys to check in priority order
        default: Default value if none found

    Returns:
        First non-None value found, or default

    Example:
        >>> get_input_by_priority({"a": None, "b": "value"}, "a", "b", "c")
        'value'
        >>> get_input_by_priority({"x": "first"}, "y", "x")
        'first'
    """
    for key in keys:
        value = inputs.get(key)
        if value is not None:
            return value
    return default
