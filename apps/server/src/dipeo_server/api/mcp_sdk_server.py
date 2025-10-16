"""MCP Server using official MCP Python SDK.

This module implements a Model Context Protocol (MCP) server using the official
MCP Python SDK from Anthropic. It exposes DiPeO diagram execution as MCP tools.

The implementation uses the SDK's decorator-based API for defining tools and resources,
while preserving DiPeO's existing OAuth 2.1 authentication infrastructure.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
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

logger = get_module_logger(__name__)

# Configuration
DEFAULT_MCP_TIMEOUT = int(os.environ.get("MCP_DEFAULT_TIMEOUT", "300"))

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
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
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
        # List available diagrams
        diagrams = []

        # Check MCP diagrams directory (pushed via --and-push)
        mcp_dir = Path("projects/mcp-diagrams")
        if mcp_dir.exists():
            for file in mcp_dir.glob("*.yaml"):
                diagrams.append(
                    {"name": file.stem, "path": str(file), "format": "light"}
                )
            for file in mcp_dir.glob("*.json"):
                diagrams.append(
                    {"name": file.stem, "path": str(file), "format": "native"}
                )

        # Check examples directory
        examples_dir = Path("examples/simple_diagrams")
        if examples_dir.exists():
            for file in examples_dir.glob("*.yaml"):
                diagrams.append(
                    {"name": file.stem, "path": str(file), "format": "light"}
                )

        return json.dumps({"diagrams": diagrams}, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


def create_sdk_router() -> APIRouter:
    """Create FastAPI router with MCP SDK integration.

    The SDK handles the MCP protocol (JSON-RPC 2.0), while FastAPI
    provides the HTTP transport and authentication middleware.

    Returns:
        APIRouter with MCP endpoints
    """
    router = APIRouter()

    # Add MCP SDK to FastAPI
    # This creates /mcp/sse endpoint for Server-Sent Events transport
    add_mcp_to_fastapi(mcp_server, router)

    logger.info("MCP SDK server initialized with official Python SDK")

    return router


# Export for compatibility
__all__ = ["mcp_server", "create_sdk_router"]
