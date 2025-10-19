"""MCP tool implementations."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp.types import TextContent

from dipeo.config.base_logger import get_module_logger

from .config import DEFAULT_MCP_TIMEOUT, PROJECT_ROOT, mcp_server

logger = get_module_logger(__name__)


@mcp_server.tool()
async def run_backend(
    diagram: str,
    input_data: dict[str, Any] | None = None,
    format_type: str = "light",
    timeout: int = DEFAULT_MCP_TIMEOUT,
) -> list[TextContent]:
    """Start diagram execution in background, returning session ID for see_result."""
    if input_data is None:
        input_data = {}

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

    if format_type == "light":
        cmd_args.append("--light")
    elif format_type == "native":
        cmd_args.append("--native")
    elif format_type == "readable":
        cmd_args.append("--readable")

    if input_data:
        cmd_args.extend(["--input-data", json.dumps(input_data)])

    try:
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
    """Check status and retrieve results of a background execution."""
    try:
        cmd_args = [sys.executable, "-m", "dipeo_server.cli.entry_point", "results", session_id]

        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        output = stdout.decode().strip()
        cli_result = json.loads(output)

        if "error" in cli_result:
            result = {
                "success": False,
                "session_id": session_id,
                "error": cli_result["error"],
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

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
    """Execute a DiPeO diagram with optional input variables."""
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
    from ..mcp_utils import DiagramExecutionError, execute_diagram_shared

    diagram = arguments.get("diagram")
    input_data = arguments.get("input_data", {})
    format_type = arguments.get("format_type", "light")
    timeout = arguments.get("timeout", DEFAULT_MCP_TIMEOUT)

    try:
        result = await execute_diagram_shared(
            diagram=diagram,
            input_data=input_data,
            format_type=format_type,
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


@mcp_server.tool()
async def search(query: str) -> list[TextContent]:
    """Search for DiPeO diagrams by name."""

    def search_diagrams(search_query: str):
        results = []
        search_lower = search_query.lower()

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
    """Fetch the full content of a specific DiPeO diagram file."""

    def fetch_diagram_content(diagram_uri: str):
        if diagram_uri.startswith("dipeo://diagrams/"):
            diagram_name = diagram_uri.replace("dipeo://diagrams/", "")
        else:
            diagram_name = diagram_uri

        mcp_dir = PROJECT_ROOT / "projects" / "mcp-diagrams"
        diagram_path = None

        test_path = Path(diagram_name)
        if test_path.exists() and test_path.is_file():
            diagram_path = test_path
        else:
            if mcp_dir.exists():
                for ext in ["*.yaml", "*.json"]:
                    matches = list(mcp_dir.glob(f"{diagram_name}.{ext[2:]}"))
                    if matches:
                        diagram_path = matches[0]
                        break

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

    result = await asyncio.to_thread(fetch_diagram_content, uri)

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
