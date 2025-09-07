"""Optional hooks for Notion provider complex operations.

This file demonstrates how to handle complex logic that can't be expressed
in the manifest alone. These hooks are optional - the manifest works without them.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_text_from_blocks(data: dict[str, Any]) -> dict[str, Any]:
    """Post-response hook to extract text content from Notion blocks.

    This can be used with list_blocks operation to get plain text.

    Args:
        data: Contains 'result' (API response) and 'context' (request context)

    Returns:
        Modified response with extracted text
    """
    result = data.get("result", {})
    blocks = result.get("results", [])

    text_parts = []
    for block in blocks:
        block_type = block.get("type")
        if block_type in [
            "paragraph",
            "heading_1",
            "heading_2",
            "heading_3",
            "bulleted_list_item",
            "numbered_list_item",
            "to_do",
            "toggle",
            "quote",
        ]:
            block_content = block.get(block_type, {})
            rich_text = block_content.get("rich_text", [])
            for text_item in rich_text:
                if text_item.get("type") == "text":
                    text_parts.append(text_item.get("text", {}).get("content", ""))

    # Add extracted text to the result
    result["extracted_text"] = "\n".join(text_parts)
    return result


def prepare_rich_text(data: dict[str, Any]) -> dict[str, Any]:
    """Pre-request hook to convert simple text to Notion's rich text format.

    Simplifies creating pages/blocks by accepting plain text.

    Args:
        data: Request context with 'config', 'resource_id', etc.

    Returns:
        Modified context with rich text formatting
    """
    config = data.get("config", {})

    # Convert simple text properties to rich text format
    if "properties" in config:
        for key, value in config["properties"].items():
            if isinstance(value, str):
                # Convert plain string to Notion rich text format
                config["properties"][key] = {
                    "title": [{"type": "text", "text": {"content": value}}]
                }

    # Convert simple text blocks to rich text blocks
    if "blocks" in config:
        formatted_blocks = []
        for block in config["blocks"]:
            if isinstance(block, str):
                # Convert plain string to paragraph block
                formatted_blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": block}}]},
                    }
                )
            else:
                formatted_blocks.append(block)
        config["blocks"] = formatted_blocks

    return data


def handle_database_pagination(data: dict[str, Any]) -> dict[str, Any]:
    """Post-response hook for advanced pagination handling.

    This is actually handled by the manifest's pagination config,
    but shown here as an example of custom pagination logic.

    Args:
        data: Response data with pagination info

    Returns:
        Modified response with pagination metadata
    """
    result = data.get("result", {})

    # Add custom pagination metadata if needed
    if result.get("has_more"):
        result["_pagination"] = {
            "has_next": True,
            "next_cursor": result.get("next_cursor"),
            "page_count": len(result.get("results", [])),
        }

    return result


def validate_parent_structure(data: dict[str, Any]) -> dict[str, Any]:
    """Pre-request hook to validate and format parent references.

    Ensures parent structure is correct for page/database creation.

    Args:
        data: Request context

    Returns:
        Modified context with validated parent structure
    """
    config = data.get("config", {})

    if "parent" in config:
        parent = config["parent"]

        # If parent is just an ID string, convert to proper structure
        if isinstance(parent, str):
            # Detect if it's a database or page ID by length/format
            if len(parent) == 32 or "-" not in parent:
                # Likely a database ID (no hyphens)
                config["parent"] = {"database_id": parent}
            else:
                # Likely a page ID (with hyphens)
                config["parent"] = {"page_id": parent}

        # Validate parent structure has required fields
        elif isinstance(parent, dict):
            if not any(k in parent for k in ["database_id", "page_id", "workspace"]):
                raise ValueError("Parent must contain 'database_id', 'page_id', or 'workspace'")

    return data


# Additional helper functions that could be useful


def create_text_block(text: str, block_type: str = "paragraph") -> dict[str, Any]:
    """Helper to create a Notion text block.

    Not a hook, but a utility function that could be imported.
    """
    return {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def create_heading_block(text: str, level: int = 1) -> dict[str, Any]:
    """Helper to create a heading block."""
    heading_type = f"heading_{min(max(level, 1), 3)}"
    return create_text_block(text, heading_type)


def create_database_property(
    name: str, property_type: str = "title", options: list[str] | None = None
) -> dict[str, Any]:
    """Helper to create database property definitions."""
    prop = {"type": property_type}

    if property_type == "select" and options:
        prop["select"] = {"options": [{"name": opt, "color": "default"} for opt in options]}
    elif property_type == "multi_select" and options:
        prop["multi_select"] = {"options": [{"name": opt, "color": "default"} for opt in options]}

    return {name: prop}
