"""MCP resource implementations."""

import asyncio
import json

from .config import PROJECT_ROOT, mcp_server


@mcp_server.resource("dipeo://diagrams")
async def list_diagrams() -> str:
    """List available DiPeO diagrams."""

    def scan_diagrams():
        result = []

        mcp_dir = PROJECT_ROOT / "projects" / "mcp-diagrams"
        if mcp_dir.exists():
            for file in mcp_dir.glob("*.yaml"):
                result.append({"name": file.stem, "path": str(file), "format": "light"})
            for file in mcp_dir.glob("*.json"):
                result.append({"name": file.stem, "path": str(file), "format": "native"})

        examples_dir = PROJECT_ROOT / "examples" / "simple_diagrams"
        if examples_dir.exists():
            for file in examples_dir.glob("*.yaml"):
                result.append({"name": file.stem, "path": str(file), "format": "light"})

        return result

    diagrams = await asyncio.to_thread(scan_diagrams)

    return json.dumps({"diagrams": diagrams}, indent=2)
