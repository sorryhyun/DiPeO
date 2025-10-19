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
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from mcp.server import FastMCP
from mcp.types import TextContent

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo_server.app_context import get_container

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


# Background execution tracking is now handled by CLI commands
# (dipeo run --background and dipeo results)


def discover_diagrams() -> list[dict[str, str]]:
    """Discover available DiPeO diagrams.

    Returns:
        List of diagram metadata dicts with 'name', 'path', 'format', 'location'
    """
    diagrams = []

    # Search MCP diagrams directory
    mcp_dir = PROJECT_ROOT / "projects" / "mcp-diagrams"
    if mcp_dir.exists():
        for file in mcp_dir.glob("*.yaml"):
            diagrams.append(
                {
                    "name": file.stem,
                    "path": str(file),
                    "format": "light",
                    "location": "mcp-diagrams",
                }
            )
        for file in mcp_dir.glob("*.json"):
            diagrams.append(
                {
                    "name": file.stem,
                    "path": str(file),
                    "format": "native",
                    "location": "mcp-diagrams",
                }
            )

    # Search examples directory
    examples_dir = PROJECT_ROOT / "examples" / "simple_diagrams"
    if examples_dir.exists():
        for file in examples_dir.glob("*.yaml"):
            # Only add if name doesn't already exist (mcp-diagrams takes priority)
            if not any(d["name"] == file.stem for d in diagrams):
                diagrams.append(
                    {
                        "name": file.stem,
                        "path": str(file),
                        "format": "light",
                        "location": "examples",
                    }
                )

    return diagrams


def register_diagram_tools():
    """Register individual tools for each discovered diagram.

    This function dynamically creates MCP tools for each available diagram,
    making them appear as separate capabilities to MCP clients.
    """
    diagrams = discover_diagrams()

    logger.info(f"Registering {len(diagrams)} diagram tools")

    for diagram_info in diagrams:
        diagram_name = diagram_info["name"]
        diagram_path = diagram_info["path"]
        diagram_format = diagram_info["format"]

        # Create closure to capture diagram-specific values
        def make_diagram_tool(d_name: str, d_format: str):
            async def diagram_tool(
                input_data: dict[str, Any] | None = None,
                timeout: int = DEFAULT_MCP_TIMEOUT,
            ) -> list[TextContent]:
                """Execute the {d_name} diagram.

                Args:
                    input_data: Optional input variables for diagram execution
                    timeout: Execution timeout in seconds

                Returns:
                    Execution results
                """
                if input_data is None:
                    input_data = {}

                from .mcp_utils import DiagramExecutionError, execute_diagram_shared

                try:
                    result = await execute_diagram_shared(
                        diagram=d_name,
                        input_data=input_data,
                        format_type=d_format,
                        timeout=timeout,
                        validate_inputs=True,
                    )
                    return [TextContent(type="text", text=result.to_json())]
                except DiagramExecutionError as e:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({"success": False, "error": str(e)}, indent=2),
                        )
                    ]

            # Set function metadata
            diagram_tool.__name__ = d_name
            diagram_tool.__doc__ = f"Execute the {d_name} diagram"
            return diagram_tool

        # Create the tool function with closure
        tool_func = make_diagram_tool(diagram_name, diagram_format)

        # Register the tool with FastMCP
        try:
            mcp_server._tool_manager.add_tool(tool_func)
            logger.debug(f"Registered diagram tool: {diagram_name}")
        except Exception as e:
            logger.warning(f"Failed to register diagram tool {diagram_name}: {e}")

    logger.info("Completed registering diagram tools")


@mcp_server.tool()
async def run_backend(
    diagram: str,
    input_data: dict[str, Any] | None = None,
    format_type: str = "light",
    timeout: int = DEFAULT_MCP_TIMEOUT,
) -> list[TextContent]:
    """Start a DiPeO diagram execution in the background and return immediately.

    This tool starts diagram execution asynchronously and returns a session ID
    that can be used with see_result to check status and retrieve results.

    Args:
        diagram: Path or name of the diagram to execute
        input_data: Optional input variables for the diagram execution
        format_type: Diagram format type (light, native, or readable)
        timeout: Execution timeout in seconds

    Returns:
        Session ID for querying execution status with see_result
    """
    import subprocess
    import sys

    if input_data is None:
        input_data = {}

    # Build CLI command: dipeo run --background
    cmd_args = [
        sys.executable,
        "-m",
        "dipeo_server.cli.entry_point",
        "run",
        diagram,
        "--background",
    ]

    if timeout != DEFAULT_MCP_TIMEOUT:
        cmd_args.extend(["--timeout", str(timeout)])

    # Add format flag
    if format_type == "light":
        cmd_args.append("--light")
    elif format_type == "native":
        cmd_args.append("--native")
    elif format_type == "readable":
        cmd_args.append("--readable")

    # Add input data if provided
    if input_data:
        cmd_args.extend(["--input-data", json.dumps(input_data)])

    try:
        # Run CLI command and capture output
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            result = {
                "success": False,
                "error": f"Failed to start background execution: {error_msg}",
                "diagram": diagram,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # Parse output to get session_id
        output = stdout.decode().strip()
        cli_result = json.loads(output)
        session_id = cli_result.get("session_id")

        result = {
            "success": True,
            "session_id": session_id,
            "diagram": diagram,
            "status": "started",
            "message": f"Diagram execution started. Use see_result('{session_id}') to check status.",
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error starting background execution: {e}", exc_info=True)
        result = {
            "success": False,
            "error": f"Error starting background execution: {e!s}",
            "diagram": diagram,
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]


@mcp_server.tool()
async def see_result(session_id: str) -> list[TextContent]:
    """Check status and retrieve results of a background diagram execution.

    Args:
        session_id: Session ID returned by run_backend

    Returns:
        Execution status and results if completed
    """
    import sys

    try:
        # Build CLI command: dipeo results <session_id>
        cmd_args = [sys.executable, "-m", "dipeo_server.cli.entry_point", "results", session_id]

        # Run CLI command and capture output
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        # Parse output (CLI returns JSON)
        output = stdout.decode().strip()
        cli_result = json.loads(output)

        # Check if there was an error
        if "error" in cli_result:
            result = {
                "success": False,
                "session_id": session_id,
                "error": cli_result["error"],
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # Return the result from CLI
        return [TextContent(type="text", text=json.dumps(cli_result, indent=2))]

    except Exception as e:
        logger.error(f"Error retrieving result for {session_id}: {e}", exc_info=True)
        error_result = {
            "success": False,
            "session_id": session_id,
            "error": f"Error retrieving result: {e!s}",
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


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


@mcp_server.tool()
async def search(query: str) -> list[TextContent]:
    """Search for DiPeO diagrams by name or description.

    This tool searches through available diagrams in the MCP diagrams directory
    and examples directory, matching against diagram names and paths.

    Args:
        query: Search query string to match against diagram names

    Returns:
        List of text content with matching diagrams in JSON format
    """

    def search_diagrams(search_query: str):
        """Search for diagrams matching the query."""
        results = []
        search_lower = search_query.lower()

        # Search MCP diagrams directory
        mcp_dir = PROJECT_ROOT / "projects" / "mcp-diagrams"
        if mcp_dir.exists():
            for file in mcp_dir.glob("*.yaml"):
                if search_lower in file.stem.lower():
                    results.append(
                        {
                            "name": file.stem,
                            "path": str(file),
                            "format": "light",
                            "location": "mcp-diagrams",
                        }
                    )
            for file in mcp_dir.glob("*.json"):
                if search_lower in file.stem.lower():
                    results.append(
                        {
                            "name": file.stem,
                            "path": str(file),
                            "format": "native",
                            "location": "mcp-diagrams",
                        }
                    )

        # Search examples directory
        examples_dir = PROJECT_ROOT / "examples" / "simple_diagrams"
        if examples_dir.exists():
            for file in examples_dir.glob("*.yaml"):
                if search_lower in file.stem.lower() or search_lower in str(file).lower():
                    results.append(
                        {
                            "name": file.stem,
                            "path": str(file),
                            "format": "light",
                            "location": "examples",
                        }
                    )

        return results

    # Run blocking I/O in thread pool
    matching_diagrams = await asyncio.to_thread(search_diagrams, query)

    response = {
        "success": True,
        "query": query,
        "count": len(matching_diagrams),
        "results": matching_diagrams,
    }

    return [TextContent(type="text", text=json.dumps(response, indent=2))]


@mcp_server.tool()
async def fetch(uri: str) -> list[TextContent]:
    """Fetch the content of a specific DiPeO diagram.

    This tool retrieves the full content of a diagram file, allowing inspection
    of the diagram structure, nodes, connections, and configuration.

    Args:
        uri: URI or path to the diagram (e.g., 'dipeo://diagrams/my_workflow' or diagram name)

    Returns:
        List of text content with diagram content and metadata
    """

    def fetch_diagram_content(diagram_uri: str):
        """Fetch diagram content by URI or name."""
        # Handle different URI formats
        if diagram_uri.startswith("dipeo://diagrams/"):
            diagram_name = diagram_uri.replace("dipeo://diagrams/", "")
        else:
            diagram_name = diagram_uri

        # Search for the diagram in MCP directory first
        mcp_dir = PROJECT_ROOT / "projects" / "mcp-diagrams"
        diagram_path = None

        # Try as direct path first
        test_path = Path(diagram_name)
        if test_path.exists() and test_path.is_file():
            diagram_path = test_path
        else:
            # Search in MCP diagrams directory
            if mcp_dir.exists():
                for ext in ["*.yaml", "*.json"]:
                    matches = list(mcp_dir.glob(f"{diagram_name}.{ext[2:]}"))
                    if matches:
                        diagram_path = matches[0]
                        break

            # Search in examples directory if not found
            if not diagram_path:
                examples_dir = PROJECT_ROOT / "examples" / "simple_diagrams"
                if examples_dir.exists():
                    for ext in ["*.yaml", "*.json"]:
                        matches = list(examples_dir.glob(f"{diagram_name}.{ext[2:]}"))
                        if matches:
                            diagram_path = matches[0]
                            break

        if not diagram_path:
            return {
                "success": False,
                "error": f"Diagram not found: {diagram_name}",
                "uri": diagram_uri,
            }

        # Read diagram content
        try:
            content = diagram_path.read_text()
            return {
                "success": True,
                "uri": diagram_uri,
                "name": diagram_path.stem,
                "path": str(diagram_path),
                "format": "light" if diagram_path.suffix == ".yaml" else "native",
                "size": len(content),
                "content": content,
            }
        except Exception as e:
            return {"success": False, "error": f"Error reading diagram: {e!s}", "uri": diagram_uri}

    # Run blocking I/O in thread pool
    result = await asyncio.to_thread(fetch_diagram_content, uri)

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


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
    async def mcp_messages_endpoint(request: Request):
        """MCP messages endpoint for JSON-RPC requests.

        Handles JSON-RPC 2.0 requests and delegates to FastMCP tool handlers.

        Authentication:
            - Handled by ngrok basic auth at infrastructure level
        """
        logger.debug("MCP request received")

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
    async def mcp_info_endpoint():
        """Get information about the MCP server.

        Returns server capabilities, available tools, and connection information.

        Authentication:
            - Handled by ngrok basic auth at infrastructure level
        """
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


# Initialize diagram tools on module load
try:
    register_diagram_tools()
    logger.info("Diagram tools registered successfully")
except Exception as e:
    logger.warning(f"Failed to register diagram tools: {e}")


# Export for compatibility
__all__ = ["create_info_router", "create_messages_router", "mcp_server", "register_diagram_tools"]
