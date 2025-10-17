"""MCP Server using official MCP Python SDK.

This module implements a Model Context Protocol (MCP) server using the official
MCP Python SDK from Anthropic. It exposes DiPeO diagram execution as MCP tools.

The implementation uses the SDK's decorator-based API for defining tools and resources,
while preserving DiPeO's existing OAuth 2.1 authentication infrastructure.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from mcp.server import Server
from mcp.server.fastapi import add_mcp_to_fastapi
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    Resource,
    TextContent,
    Tool,
)

from dipeo.config.base_logger import get_module_logger
from dipeo_server.app_context import get_container

from .auth import get_current_user
from .auth.oauth import TokenData

logger = get_module_logger(__name__)

# Configuration
DEFAULT_MCP_TIMEOUT = int(os.environ.get("MCP_DEFAULT_TIMEOUT", "300"))
DEBUG_MODE = os.environ.get("DIPEO_DEBUG", "false").lower() == "true"

# Project root for absolute paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

# Create MCP server instance
mcp_server = Server("dipeo-mcp-server")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools.

    Returns:
        List of tool definitions
    """
    return [
        Tool(
            name="dipeo_run",
            description="Execute a DiPeO diagram with optional input variables",
            inputSchema={
                "type": "object",
                "properties": {
                    "diagram": {
                        "type": "string",
                        "description": "Path or name of the diagram to execute (e.g., 'simple_iter', 'examples/simple_diagrams/simple_iter')",
                    },
                    "input_data": {
                        "type": "object",
                        "description": "Optional input variables for the diagram execution",
                        "default": {},
                    },
                    "format_type": {
                        "type": "string",
                        "enum": ["light", "native", "readable"],
                        "description": "Diagram format type",
                        "default": "light",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Execution timeout in seconds",
                        "default": DEFAULT_MCP_TIMEOUT,
                    },
                },
                "required": ["diagram"],
            },
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool call.

    Args:
        name: Tool name to execute
        arguments: Tool arguments

    Returns:
        List of text content results
    """
    if name != "dipeo_run":
        raise ValueError(f"Unknown tool: {name}")

    return await _execute_diagram(arguments)


async def _execute_diagram(arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a DiPeO diagram.

    Args:
        arguments: Diagram execution arguments

    Returns:
        List of text content with execution results
    """
    from dipeo_server.cli import CLIRunner

    diagram = arguments.get("diagram")
    input_data = arguments.get("input_data", {})
    format_type = arguments.get("format_type", "light")
    timeout = arguments.get("timeout", DEFAULT_MCP_TIMEOUT)

    # Validate required parameters
    if not diagram:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"success": False, "error": "diagram parameter is required"},
                    indent=2,
                ),
            )
        ]

    # Validate input_data type
    if input_data is not None and not isinstance(input_data, dict):
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"success": False, "error": "input_data must be a dictionary"},
                    indent=2,
                ),
            )
        ]

    # Validate format_type
    valid_formats = ["light", "native", "readable"]
    if format_type not in valid_formats:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": False,
                        "error": f"Invalid format_type: {format_type}. Must be one of {valid_formats}",
                    },
                    indent=2,
                ),
            )
        ]

    try:
        logger.info(f"Executing diagram via MCP SDK: {diagram}")

        # Get the container
        container = get_container()

        # Create CLI runner
        cli = CLIRunner(container)

        # Execute the diagram
        success = await cli.run_diagram(
            diagram=diagram,
            debug=False,
            timeout=timeout,
            format_type=format_type,
            input_variables=input_data if input_data else None,
            use_unified=True,
            simple=True,  # Use simple output for MCP
            interactive=False,  # Non-interactive for MCP
        )

        # Return result
        result_text = json.dumps(
            {
                "success": success,
                "diagram": diagram,
                "format": format_type,
                "message": "Diagram executed successfully"
                if success
                else "Diagram execution failed",
            },
            indent=2,
        )

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error executing diagram via MCP SDK: {e}", exc_info=True)

        # Sanitize error message - don't expose full stack traces in production
        error_msg = str(e) if DEBUG_MODE else "Diagram execution failed"

        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": error_msg}, indent=2),
            )
        ]


@mcp_server.list_resources()
async def list_resources() -> list[Resource]:
    """List available MCP resources.

    Returns:
        List of resource definitions
    """
    return [
        Resource(
            uri="dipeo://diagrams",
            name="Available Diagrams",
            description="List of available DiPeO diagrams",
            mimeType="application/json",
        )
    ]


@mcp_server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource.

    Args:
        uri: Resource URI

    Returns:
        Resource content as JSON string
    """
    if uri == "dipeo://diagrams":
        # List available diagrams using absolute paths
        diagrams = []

        # Use asyncio.to_thread for blocking I/O operations
        def scan_diagrams():
            result = []

            # Check MCP diagrams directory (pushed via --and-push)
            mcp_dir = PROJECT_ROOT / "projects" / "mcp-diagrams"
            if mcp_dir.exists():
                for file in mcp_dir.glob("*.yaml"):
                    result.append(
                        {"name": file.stem, "path": str(file), "format": "light"}
                    )
                for file in mcp_dir.glob("*.json"):
                    result.append(
                        {"name": file.stem, "path": str(file), "format": "native"}
                    )

            # Check examples directory
            examples_dir = PROJECT_ROOT / "examples" / "simple_diagrams"
            if examples_dir.exists():
                for file in examples_dir.glob("*.yaml"):
                    result.append(
                        {"name": file.stem, "path": str(file), "format": "light"}
                    )

            return result

        # Run blocking I/O in thread pool
        diagrams = await asyncio.to_thread(scan_diagrams)

        return json.dumps({"diagrams": diagrams}, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


def create_sdk_router() -> APIRouter:
    """Create FastAPI router with MCP SDK integration.

    The SDK handles the MCP protocol (JSON-RPC 2.0), while FastAPI
    provides the HTTP transport and authentication middleware.

    IMPORTANT: This router enforces the same authentication as the legacy
    MCP endpoint (/mcp/messages). All SDK endpoints require authentication
    based on the MCP_AUTH_REQUIRED configuration.

    Returns:
        APIRouter with MCP endpoints protected by authentication
    """
    # Create router with authentication dependency applied to all routes
    # This ensures all SDK-generated endpoints require authentication
    router = APIRouter(
        dependencies=[Depends(get_current_user)],
        tags=["mcp-sdk"],
    )

    # Add MCP SDK to FastAPI
    # This creates /mcp/sse endpoint for Server-Sent Events transport
    # All routes added here will inherit the authentication dependency
    add_mcp_to_fastapi(mcp_server, router)

    logger.info("MCP SDK server initialized with official Python SDK and authentication")

    return router


# Export for compatibility
__all__ = ["mcp_server", "create_sdk_router"]
