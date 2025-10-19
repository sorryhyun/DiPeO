"""MCP Server using official MCP Python SDK.

This module implements a Model Context Protocol (MCP) server using the official
MCP Python SDK from Anthropic. It exposes DiPeO diagram execution as MCP tools.

The implementation uses FastMCP with HTTP JSON-RPC transport, maintaining backward
compatibility with the legacy /mcp/messages endpoint while using DiPeO's existing
OAuth 2.1 authentication infrastructure via FastAPI middleware.
"""

from dipeo.config.base_logger import get_module_logger

from .config import DEFAULT_MCP_TIMEOUT, PROJECT_ROOT, mcp_server
from .discovery import register_diagram_tools
from .resources import list_diagrams
from .routers import create_info_router, create_messages_router
from .tools import dipeo_run, fetch, run_backend, search, see_result

logger = get_module_logger(__name__)

try:
    register_diagram_tools()
    logger.info("Diagram tools registered successfully")
except Exception as e:
    logger.warning(f"Failed to register diagram tools: {e}")

__all__ = [
    "DEFAULT_MCP_TIMEOUT",
    "PROJECT_ROOT",
    "create_info_router",
    "create_messages_router",
    "dipeo_run",
    "fetch",
    "list_diagrams",
    "mcp_server",
    "register_diagram_tools",
    "run_backend",
    "search",
    "see_result",
]
