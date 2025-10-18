"""MCP Server using official MCP Python SDK.

This module implements a Model Context Protocol (MCP) server using the official
MCP Python SDK from Anthropic. It exposes DiPeO diagram execution as MCP tools.

The implementation uses FastMCP with HTTP JSON-RPC transport, maintaining backward
compatibility with the legacy /mcp/messages endpoint while using DiPeO's existing
OAuth 2.1 authentication infrastructure via FastAPI middleware.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from mcp.server import FastMCP
from mcp.types import TextContent

from dipeo.config.base_logger import get_module_logger
from dipeo_server.app_context import get_container

from .auth import get_current_user, get_oauth_config
from .auth.oauth import TokenData, get_authorization_server_metadata

logger = get_module_logger(__name__)

# Configuration
DEFAULT_MCP_TIMEOUT = int(os.environ.get("MCP_DEFAULT_TIMEOUT", "300"))

# Project root for absolute paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

# Create FastMCP server instance with HTTP transport at /mcp/messages (backward compatible)
mcp_server = FastMCP(
    name="dipeo-mcp-server",
    streamable_http_path="/mcp/messages",  # HTTP JSON-RPC endpoint path
    stateless_http=True,  # Stateless for REST-like behavior
)


@mcp_server.tool()
async def dipeo_run(
    diagram: str,
    input_data: dict[str, Any] | None = None,
    format_type: str = "light",
    timeout: int = DEFAULT_MCP_TIMEOUT,
) -> list[TextContent]:
    """Execute a DiPeO diagram with optional input variables.

    Args:
        diagram: Path or name of the diagram to execute (e.g., 'simple_iter', 'examples/simple_diagrams/simple_iter')
        input_data: Optional input variables for the diagram execution
        format_type: Diagram format type (light, native, or readable)
        timeout: Execution timeout in seconds

    Returns:
        List of text content with execution results
    """
    if input_data is None:
        input_data = {}

    arguments = {
        "diagram": diagram,
        "input_data": input_data,
        "format_type": format_type,
        "timeout": timeout,
    }

    return await _execute_diagram(arguments)


async def _execute_diagram(arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a DiPeO diagram.

    Args:
        arguments: Diagram execution arguments

    Returns:
        List of text content with execution results
    """
    from .mcp_utils import DiagramExecutionError, execute_diagram_shared

    diagram = arguments.get("diagram")
    input_data = arguments.get("input_data", {})
    format_type = arguments.get("format_type", "light")
    timeout = arguments.get("timeout", DEFAULT_MCP_TIMEOUT)

    try:
        # Execute diagram using shared logic (with validation enabled)
        result = await execute_diagram_shared(
            diagram=diagram,
            input_data=input_data,
            format_type=format_type,
            timeout=timeout,
            validate_inputs=True,
        )

        # Convert result to SDK format
        return [TextContent(type="text", text=result.to_json())]

    except DiagramExecutionError as e:
        # Validation error - return error response
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
            )
        ]


@mcp_server.resource("dipeo://diagrams")
async def list_diagrams() -> str:
    """List available DiPeO diagrams.

    Returns:
        JSON string with available diagrams
    """
    # List available diagrams using absolute paths
    diagrams = []

    # Use asyncio.to_thread for blocking I/O operations
    def scan_diagrams():
        result = []

        # Check MCP diagrams directory (pushed via --push-as)
        mcp_dir = PROJECT_ROOT / "projects" / "mcp-diagrams"
        if mcp_dir.exists():
            for file in mcp_dir.glob("*.yaml"):
                result.append({"name": file.stem, "path": str(file), "format": "light"})
            for file in mcp_dir.glob("*.json"):
                result.append({"name": file.stem, "path": str(file), "format": "native"})

        # Check examples directory
        examples_dir = PROJECT_ROOT / "examples" / "simple_diagrams"
        if examples_dir.exists():
            for file in examples_dir.glob("*.yaml"):
                result.append({"name": file.stem, "path": str(file), "format": "light"})

        return result

    # Run blocking I/O in thread pool
    diagrams = await asyncio.to_thread(scan_diagrams)

    return json.dumps({"diagrams": diagrams}, indent=2)


def create_messages_router() -> APIRouter:
    """Create FastAPI router with custom JSON-RPC endpoint for MCP.

    This router provides a /mcp/messages endpoint that manually handles JSON-RPC 2.0
    and delegates to the FastMCP server's tool handlers.

    Why custom implementation?
    - FastMCP's streamable_http_app() requires its own runtime context (task groups)
    - Cannot be mounted into an existing FastAPI app
    - This approach gives us full control over authentication and error handling

    Returns:
        APIRouter with /mcp/messages endpoint
    """
    router = APIRouter(tags=["mcp-messages"])

    @router.post("/mcp/messages")
    async def mcp_messages_endpoint(
        request: Request,
        user: Optional[TokenData] = Depends(get_current_user),
    ):
        """MCP messages endpoint for JSON-RPC requests.

        Handles JSON-RPC 2.0 requests and delegates to FastMCP tool handlers.

        Authentication:
            - Bearer token (OAuth 2.1 JWT) via Authorization header
            - API key via X-API-Key header
            - Optional/required based on MCP_AUTH_REQUIRED env var
        """
        # Log authentication status
        if user:
            logger.debug(f"MCP request authenticated: {user.sub}")
        else:
            logger.debug("MCP request unauthenticated")

        try:
            request_data = await request.json()
            logger.debug(f"MCP request: {request_data}")

            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")

            # Handle different MCP protocol methods
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                    },
                    "serverInfo": {
                        "name": "dipeo-mcp-server",
                        "version": "1.0.0",
                    },
                }
            elif method == "tools/list":
                # Get tools from FastMCP server's tool manager
                tools_list = []
                if hasattr(mcp_server, "_tool_manager"):
                    for _tool_name, tool_obj in mcp_server._tool_manager._tools.items():
                        tools_list.append(
                            {
                                "name": tool_obj.name,
                                "description": tool_obj.description,
                                "inputSchema": tool_obj.parameters,
                            }
                        )

                result = {"tools": tools_list}

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                # Call the tool from FastMCP server's tool manager
                if (
                    hasattr(mcp_server, "_tool_manager")
                    and tool_name in mcp_server._tool_manager._tools
                ):
                    tool_obj = mcp_server._tool_manager._tools[tool_name]
                    tool_result = await tool_obj.fn(**arguments)

                    # Convert result to MCP format
                    if isinstance(tool_result, list):
                        # Already in correct format (list of TextContent)
                        result = {
                            "content": [
                                {"type": item.type, "text": item.text} for item in tool_result
                            ]
                        }
                    else:
                        result = {"content": [{"type": "text", "text": str(tool_result)}]}
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                    }

            elif method == "resources/list":
                # Get resources from FastMCP server's resource manager
                resources_list = []
                if hasattr(mcp_server, "_resource_manager"):
                    for uri, resource_obj in mcp_server._resource_manager._resources.items():
                        resources_list.append(
                            {
                                "uri": uri,
                                "name": resource_obj.name
                                if hasattr(resource_obj, "name") and resource_obj.name
                                else uri.split("://")[-1].title()
                                if "://" in uri
                                else uri,
                                "description": resource_obj.description
                                if hasattr(resource_obj, "description") and resource_obj.description
                                else "",
                                "mimeType": resource_obj.mime_type
                                if hasattr(resource_obj, "mime_type")
                                else "application/json",
                            }
                        )

                result = {"resources": resources_list}

            elif method == "resources/read":
                uri = params.get("uri")

                # Call the resource from FastMCP server's resource manager
                if (
                    hasattr(mcp_server, "_resource_manager")
                    and uri in mcp_server._resource_manager._resources
                ):
                    resource_obj = mcp_server._resource_manager._resources[uri]
                    resource_result = await resource_obj.fn()

                    result = {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": resource_obj.mime_type
                                if hasattr(resource_obj, "mime_type")
                                else "application/json",
                                "text": resource_result
                                if isinstance(resource_result, str)
                                else json.dumps(resource_result),
                            }
                        ]
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Resource not found: {uri}"},
                    }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
            logger.debug(f"MCP response: {response}")
            return response

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in MCP request: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id") if "request_data" in locals() else None,
                "error": {"code": -32603, "message": f"Internal error: {e!s}"},
            }

    logger.info("MCP SDK server initialized with custom JSON-RPC handler at /mcp/messages")
    return router


# Create a separate router for info endpoints (not mounted, so we can use FastAPI features)
def create_info_router() -> APIRouter:
    """Create router for MCP info and OAuth endpoints.

    These endpoints are implemented in FastAPI (not the SDK) to maintain
    compatibility with DiPeO's authentication system.

    Returns:
        APIRouter with info endpoints
    """
    router = APIRouter(tags=["mcp-info"])

    @router.get("/mcp/info")
    async def mcp_info_endpoint(
        user: Optional[TokenData] = Depends(get_current_user),
    ):
        """Get information about the MCP server.

        Returns server capabilities, available tools, and connection information.

        Authentication:
            - Optional (provides authentication status in response)
        """
        config = get_oauth_config()

        # Get tools and resources from FastMCP managers
        tools = []
        resources = []

        # Get tools from tool manager
        if hasattr(mcp_server, "_tool_manager"):
            tools = [
                {
                    "name": tool_obj.name,
                    "description": tool_obj.description,
                }
                for tool_name, tool_obj in mcp_server._tool_manager._tools.items()
            ]

        # Get resources from resource manager
        if hasattr(mcp_server, "_resource_manager"):
            resources = [
                {
                    "uri": uri,
                    "name": resource_obj.name
                    if hasattr(resource_obj, "name") and resource_obj.name
                    else uri,
                    "description": resource_obj.description
                    if hasattr(resource_obj, "description") and resource_obj.description
                    else "",
                }
                for uri, resource_obj in mcp_server._resource_manager._resources.items()
            ]

        # Build authentication info
        auth_info = {
            "enabled": config.enabled,
            "required": config.require_auth,
            "methods": [],
        }

        if config.enabled:
            if config.jwt_enabled:
                auth_info["methods"].append("Bearer (OAuth 2.1 JWT)")
            if config.api_key_enabled:
                auth_info["methods"].append("API Key (X-API-Key header)")

        if config.authorization_server_url:
            auth_info["oauth_server"] = config.authorization_server_url
            auth_info["discovery"] = "/.well-known/oauth-authorization-server"

        # Include authenticated user info if available
        if user:
            auth_info["authenticated"] = True
            auth_info["user"] = user.sub
        else:
            auth_info["authenticated"] = False

        return {
            "server": {
                "name": "dipeo-mcp-server",
                "version": "1.0.0",
                "description": "MCP server for executing DiPeO diagrams (SDK-based)",
            },
            "protocol": {
                "version": "2024-11-05",
                "transport": "http",
            },
            "endpoints": {
                "messages": "/mcp/messages",
                "info": "/mcp/info",
                "oauth_metadata": "/.well-known/oauth-authorization-server",
            },
            "authentication": auth_info,
            "capabilities": {
                "tools": len(tools),
                "resources": len(resources),
            },
            "tools": tools,
            "resources": resources,
        }

    @router.get("/.well-known/oauth-authorization-server")
    async def oauth_authorization_server_metadata():
        """OAuth 2.0 Authorization Server Metadata endpoint.

        This endpoint is required by MCP specification (2025-03-26) for
        OAuth metadata discovery (RFC 8414).

        Returns:
            Authorization server metadata including endpoints and capabilities
        """
        try:
            metadata = get_authorization_server_metadata()
            logger.debug(f"OAuth metadata requested: {metadata}")
            return metadata
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating OAuth metadata: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Error generating OAuth authorization server metadata",
            )

    return router


# Export for compatibility
__all__ = ["create_info_router", "create_messages_router", "mcp_server"]
