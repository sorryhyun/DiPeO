"""FastAPI routers for MCP server."""

import json
import os

from fastapi import APIRouter, HTTPException, Request

from dipeo.config.base_logger import get_module_logger

from .config import mcp_server

logger = get_module_logger(__name__)


def create_messages_router() -> APIRouter:
    """Create FastAPI router with custom JSON-RPC endpoint for MCP.

    This router provides a /mcp/messages endpoint that manually handles JSON-RPC 2.0
    and delegates to the FastMCP server's tool handlers.

    Why custom implementation?
    - FastMCP's streamable_http_app() requires its own runtime context (task groups)
    - Cannot be mounted into an existing FastAPI app
    - This approach gives us full control over authentication and error handling
    """
    router = APIRouter(tags=["mcp-messages"])

    @router.post("/mcp/messages")
    async def mcp_messages_endpoint(request: Request):
        """MCP messages endpoint for JSON-RPC 2.0 requests."""
        logger.debug("MCP request received")

        try:
            request_data = await request.json()
            logger.debug(f"MCP request: {request_data}")

            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")

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

                if (
                    hasattr(mcp_server, "_tool_manager")
                    and tool_name in mcp_server._tool_manager._tools
                ):
                    tool_obj = mcp_server._tool_manager._tools[tool_name]
                    tool_result = await tool_obj.fn(**arguments)

                    if isinstance(tool_result, list):
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


def create_info_router() -> APIRouter:
    """Create router for MCP info endpoints."""
    router = APIRouter(tags=["mcp-info"])

    @router.get("/mcp/info")
    async def mcp_info_endpoint():
        """Get MCP server capabilities, tools, and connection information."""
        tools = []
        resources = []

        if hasattr(mcp_server, "_tool_manager"):
            tools = [
                {
                    "name": tool_obj.name,
                    "description": tool_obj.description,
                }
                for tool_name, tool_obj in mcp_server._tool_manager._tools.items()
            ]

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

        chatgpt_origins = os.environ.get("MCP_CHATGPT_ORIGINS", "")
        auth_info = {
            "method": "ngrok basic auth",
            "origin_validation": chatgpt_origins.split(",")
            if chatgpt_origins
            else ["https://chatgpt.com", "https://chat.openai.com"],
        }

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
            },
            "authentication": auth_info,
            "capabilities": {
                "tools": len(tools),
                "resources": len(resources),
            },
            "tools": tools,
            "resources": resources,
        }

    return router
