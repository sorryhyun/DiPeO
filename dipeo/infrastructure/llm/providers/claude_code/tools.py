"""Tool definitions for Claude Code structured output."""

import logging
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


# Memory selection tool with proper type annotations
@tool(
    "select_memory_messages",
    "Select relevant messages from memory for context",
    {
        "type": "object",
        "properties": {
            "message_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of message IDs to select",
            }
        },
        "required": ["message_ids"],
    },
)
async def select_memory_messages(args: dict[str, Any]) -> dict[str, Any]:
    """
    Select relevant messages from memory for context.

    Args:
        args: Dictionary containing 'message_ids' key with list of message IDs

    Returns:
        Structured output with selected message IDs
    """
    message_ids = args.get("message_ids", [])

    # Return structured data directly - let SDK handle formatting
    result = {
        "content": [
            {
                "type": "text",
                "text": f"Selected {len(message_ids)} messages",
            }
        ],
        "data": {"message_ids": message_ids},
    }

    return result


# Decision making tool with proper boolean type
@tool(
    "make_decision",
    "Make a binary YES/NO decision based on evaluation criteria",
    {
        "type": "object",
        "properties": {
            "decision": {
                "type": "boolean",
                "description": "True for YES, False for NO",
            }
        },
        "required": ["decision"],
    },
)
async def make_decision(args: dict[str, Any]) -> dict[str, Any]:
    """
    Make a binary YES/NO decision based on evaluation criteria.

    Args:
        args: Dictionary containing 'decision' key with boolean value

    Returns:
        Structured output with the decision result
    """
    decision = args.get("decision", False)

    # Return structured data directly
    result = {
        "content": [
            {
                "type": "text",
                "text": "YES" if decision else "NO",
            }
        ],
        "data": {"decision": decision},
    }

    return result


def create_dipeo_mcp_server():
    """Create an MCP server with DiPeO structured output tools."""
    return create_sdk_mcp_server(
        name="dipeo_structured_output",
        version="1.0.0",
        tools=[select_memory_messages, make_decision],
    )
