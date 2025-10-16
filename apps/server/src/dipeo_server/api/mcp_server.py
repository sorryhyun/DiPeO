"""MCP Server for exposing DiPeO diagram execution as MCP tools.

This module implements a Model Context Protocol (MCP) server that allows
external LLM applications to execute DiPeO diagrams as tools.

Supports OAuth 2.1 authentication as required by MCP specification (2025-03-26).
"""

import json
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from dipeo.config.base_logger import get_module_logger
from dipeo_server.app_context import get_container

from .auth import get_current_user, get_oauth_config
from .auth.oauth import TokenData, get_authorization_server_metadata

logger = get_module_logger(__name__)

router = APIRouter()

# Configuration
DEFAULT_MCP_TIMEOUT = int(os.environ.get("MCP_DEFAULT_TIMEOUT", "300"))


class MCPServer:
    """MCP Server that exposes DiPeO diagram execution capabilities."""

    def __init__(self):
        """Initialize the MCP server."""
        self.tools = {
            "dipeo_run": {
                "name": "dipeo_run",
                "description": "Execute a DiPeO diagram with optional input variables",
                "inputSchema": {
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
            }
        }
        self.resources = {
            "diagrams": {
                "uri": "dipeo://diagrams",
                "name": "Available Diagrams",
                "description": "List of available DiPeO diagrams",
                "mimeType": "application/json",
            }
        }

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools.

        Returns:
            List of tool definitions
        """
        return list(self.tools.values())

    async def list_resources(self) -> list[dict[str, Any]]:
        """List available MCP resources.

        Returns:
            List of resource definitions
        """
        return list(self.resources.values())

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call.

        Args:
            name: Tool name to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if name == "dipeo_run":
            return await self._execute_diagram(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _execute_diagram(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a DiPeO diagram.

        Args:
            arguments: Diagram execution arguments

        Returns:
            Execution result
        """
        from dipeo_server.cli import CLIRunner

        diagram = arguments.get("diagram")
        input_data = arguments.get("input_data", {})
        format_type = arguments.get("format_type", "light")
        timeout = arguments.get("timeout", DEFAULT_MCP_TIMEOUT)

        if not diagram:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {"success": False, "error": "diagram parameter is required"},
                            indent=2,
                        ),
                    }
                ],
                "isError": True,
            }

        try:
            logger.info(f"Executing diagram via MCP: {diagram}")

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

            return {
                "content": [{"type": "text", "text": result_text}],
                "isError": not success,
            }

        except Exception as e:
            logger.error(f"Error executing diagram via MCP: {e}", exc_info=True)
            return {
                "content": [
                    {"type": "text", "text": json.dumps({"success": False, "error": str(e)}, indent=2)}
                ],
                "isError": True,
            }

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource.

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        if uri == "dipeo://diagrams":
            # List available diagrams
            import os
            from pathlib import Path

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

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({"diagrams": diagrams}, indent=2),
                    }
                ]
            }
        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def handle_jsonrpc(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Handle a JSON-RPC 2.0 request.

        Args:
            request_data: JSON-RPC request

        Returns:
            JSON-RPC response with structure:
            - jsonrpc: "2.0"
            - id: Request ID
            - result: Method result (on success)
            - error: Error object (on failure)
        """
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": {
                        "name": "dipeo-mcp-server",
                        "version": "1.0.0",
                    },
                }
            elif method == "tools/list":
                tools_list = await self.list_tools()
                result = {"tools": tools_list}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.call_tool(tool_name, arguments)
            elif method == "resources/list":
                resources_list = await self.list_resources()
                result = {"resources": resources_list}
            elif method == "resources/read":
                uri = params.get("uri")
                result = await self.read_resource(uri)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }

            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        except Exception as e:
            logger.error(f"Error handling JSON-RPC request: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(e)},
            }


# Global MCP server instance
_mcp_server: MCPServer | None = None


def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance.

    Returns:
        MCPServer instance
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


# MCP message endpoint
@router.post("/mcp/messages")
async def mcp_messages_endpoint(
    request: Request,
    user: Optional[TokenData] = Depends(get_current_user),
):
    """MCP messages endpoint for JSON-RPC requests.

    This endpoint handles JSON-RPC 2.0 requests from the MCP client.
    Supports OAuth 2.1 authentication (optional or required based on configuration).

    Authentication:
        - Bearer token (OAuth 2.1 JWT) via Authorization header
        - API key via X-API-Key header
        - Optional/required based on MCP_AUTH_REQUIRED env var
    """
    mcp_server = get_mcp_server()

    # Log authentication status
    if user:
        logger.debug(f"MCP request authenticated: {user.sub}")
    else:
        logger.debug("MCP request unauthenticated")

    try:
        request_data = await request.json()
        logger.debug(f"MCP request: {request_data}")

        response = await mcp_server.handle_jsonrpc(request_data)
        logger.debug(f"MCP response: {response}")

        return response

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in MCP request: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
        }


# MCP info endpoint
@router.get("/mcp/info")
async def mcp_info_endpoint(
    user: Optional[TokenData] = Depends(get_current_user),
):
    """Get information about the MCP server.

    Returns server capabilities, available tools, and connection information.

    Authentication:
        - Optional (provides authentication status in response)
    """
    mcp_server = get_mcp_server()
    config = get_oauth_config()

    tools = await mcp_server.list_tools()
    resources = await mcp_server.list_resources()

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
            "description": "MCP server for executing DiPeO diagrams",
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


# OAuth 2.0 Authorization Server Metadata endpoint (RFC 8414)
# Required by MCP specification for metadata discovery
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
