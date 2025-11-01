"""Configuration for MCP SDK server."""

import os
from pathlib import Path

from mcp.server import FastMCP

DEFAULT_MCP_TIMEOUT = int(os.environ.get("MCP_DEFAULT_TIMEOUT", "300"))

PROJECT_ROOT = Path(__file__).parent.parent.parent

mcp_server = FastMCP(
    name="dipeo-mcp-server",
    streamable_http_path="/mcp/messages",
    stateless_http=True,
)
