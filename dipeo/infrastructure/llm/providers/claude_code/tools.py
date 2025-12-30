"""Tool definitions for Claude Code structured output.

This module provides backward-compatible access to MCP tools.
The actual tool definitions are now in tool_definitions/ using Pydantic models.
"""

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from dipeo.config.base_logger import get_module_logger

from .tool_definitions import ToolGroup, get_registry

logger = get_module_logger(__name__)


# Legacy tool functions for backward compatibility
# These are still needed for direct MCP server creation


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
    """Select relevant messages from memory for context."""
    message_ids = args.get("message_ids", [])

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
    """Make a binary YES/NO decision based on evaluation criteria."""
    decision = args.get("decision", False)

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
    """Create MCP server with structured output tools.

    This is the legacy function that creates MCP server directly.
    For new code, prefer using MCPRegistry.build_mcp_config() for
    group-based tool management.
    """
    return create_sdk_mcp_server(
        name="dipeo_structured_output",
        version="1.0.0",
        tools=[select_memory_messages, make_decision],
    )


def create_mcp_config_from_registry(
    enabled_groups: set[ToolGroup] | None = None,
    include_subagent_tools: bool = False,
):
    """Create MCP configuration using the registry.

    Args:
        enabled_groups: Tool groups to enable (defaults to memory + decision)
        include_subagent_tools: Whether to include Task/TaskOutput tools

    Returns:
        MCPServerConfig with servers and allowed tools
    """
    registry = get_registry()

    extra_tools = None
    if include_subagent_tools:
        extra_tools = ["Task", "TaskOutput"]

    return registry.build_mcp_config(
        enabled_groups=enabled_groups,
        extra_tools=extra_tools,
    )
