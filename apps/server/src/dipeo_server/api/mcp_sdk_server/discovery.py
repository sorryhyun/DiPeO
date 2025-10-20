"""Diagram discovery and registration for MCP server."""

import json
from typing import Any

from mcp.types import TextContent

from dipeo.config.base_logger import get_module_logger

from .config import DEFAULT_MCP_TIMEOUT, PROJECT_ROOT, mcp_server

logger = get_module_logger(__name__)


def discover_diagrams() -> list[dict[str, str]]:
    """Discover available DiPeO diagrams in mcp-diagrams and examples directories."""
    diagrams = []

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

    examples_dir = PROJECT_ROOT / "examples" / "simple_diagrams"
    if examples_dir.exists():
        for file in examples_dir.glob("*.yaml"):
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
    """Register individual MCP tools for each discovered diagram."""
    diagrams = discover_diagrams()

    logger.info(f"Registering {len(diagrams)} diagram tools")

    for diagram_info in diagrams:
        diagram_name = diagram_info["name"]
        diagram_path = diagram_info["path"]
        diagram_format = diagram_info["format"]

        def make_diagram_tool(d_name: str, d_format: str):
            async def diagram_tool(
                input_data: dict[str, Any] | None = None,
                timeout: int = DEFAULT_MCP_TIMEOUT,
            ) -> list[TextContent]:
                if input_data is None:
                    input_data = {}

                from ..mcp_utils import DiagramExecutionError, execute_diagram_shared

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

            diagram_tool.__name__ = d_name
            diagram_tool.__doc__ = f"Execute the {d_name} diagram"
            return diagram_tool

        tool_func = make_diagram_tool(diagram_name, diagram_format)

        try:
            mcp_server._tool_manager.add_tool(tool_func)
            logger.debug(f"Registered diagram tool: {diagram_name}")
        except Exception as e:
            logger.warning(f"Failed to register diagram tool {diagram_name}: {e}")

    logger.info("Completed registering diagram tools")
