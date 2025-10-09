"""Data serialization utilities for JSON and YAML formats."""

import json
import logging
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def serialize_data(data: Any, format_type: str | None) -> str:
    """Serialize data to string based on format type.

    Args:
        data: Data to serialize (dict, list, or any object)
        format_type: Format type ("json", "yaml", "text", or None)

    Returns:
        Serialized string representation

    Example:
        >>> serialize_data({"key": "value"}, "json")
        '{\n  "key": "value"\n}'
        >>> serialize_data({"key": "value"}, "yaml")
        'key: value\n'
    """
    if format_type == "json":
        return json.dumps(data, indent=2)
    elif format_type == "yaml":
        return yaml.dump(data, default_flow_style=False)
    elif format_type == "text" or format_type is None:
        return str(data)
    else:
        logger.warning(f"Unknown format '{format_type}', using text format")
        return str(data)


def deserialize_data(content: str, format_type: str | None) -> Any:
    """Deserialize string content based on format type.

    Args:
        content: String content to deserialize
        format_type: Format type ("json", "yaml", "text", or None)

    Returns:
        Deserialized data (dict, list, str, or original content on error)

    Example:
        >>> deserialize_data('{"key": "value"}', "json")
        {'key': 'value'}
        >>> deserialize_data('key: value', "yaml")
        {'key': 'value'}
    """
    if not content:
        return content

    if format_type == "json":
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return content
    elif format_type == "yaml":
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML: {e}")
            return content
    elif format_type == "text" or format_type is None:
        return content
    else:
        logger.warning(f"Unknown format '{format_type}', returning as text")
        return content
