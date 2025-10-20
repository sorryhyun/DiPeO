"""Data serialization utilities for JSON and YAML formats."""

import json
import logging
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def serialize_data(data: Any, format_type: str | None) -> str:
    """Serialize data to JSON, YAML, or text string."""
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
    """Parse JSON/YAML content, returning original string on parse errors."""
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
