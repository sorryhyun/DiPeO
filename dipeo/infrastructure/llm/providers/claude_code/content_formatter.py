"""Content formatting utilities for Claude Code SDK.

Handles conversion of various content types to Claude SDK block format.
"""

import json
from typing import Any


def build_sdk_content(raw_content: Any) -> list[dict[str, Any]]:
    """Convert message content into Claude SDK block format."""
    if isinstance(raw_content, list):
        if all(isinstance(item, dict) and item.get("type") for item in raw_content):
            return raw_content
        elif all(isinstance(item, dict) and not item.get("type") for item in raw_content):
            blocks = []
            for item in raw_content:
                if "text" in item:
                    blocks.append(
                        {
                            "type": "text",
                            "text": stringify_content(item["text"]),
                        }
                    )
                else:
                    blocks.append(
                        {
                            "type": "text",
                            "text": stringify_content(item),
                        }
                    )
            return blocks
        else:
            return [
                {
                    "type": "text",
                    "text": stringify_content(raw_content),
                }
            ]

    if isinstance(raw_content, dict):
        if raw_content.get("type"):
            return [raw_content]
        if "content" in raw_content and isinstance(raw_content["content"], list):
            return build_sdk_content(raw_content["content"])

    return [
        {
            "type": "text",
            "text": stringify_content(raw_content),
        }
    ]


def stringify_payload(payload: dict[str, Any]) -> str:
    """Convert payload to JSON string."""
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return json.dumps(str(payload), ensure_ascii=False)


def stringify_content(raw_content: Any) -> str:
    """Convert content to string representation."""
    if raw_content is None:
        return ""

    if isinstance(raw_content, str):
        return raw_content

    if hasattr(raw_content, "model_dump_json"):
        try:
            return raw_content.model_dump_json()
        except Exception:  # pragma: no cover
            pass

    if hasattr(raw_content, "model_dump"):
        try:
            return json.dumps(raw_content.model_dump(), ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(raw_content)

    try:
        return json.dumps(raw_content, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(raw_content)
