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


@mcp_server.tool(
    description="""Start a DiPeO diagram execution in the background (asynchronous).

This tool starts execution in a background process and returns immediately with a session ID.
Use the see_result tool to check status and retrieve results later.

Use Cases:
  - Long-running diagrams that exceed typical request timeouts
  - Parallel execution of multiple diagrams
  - Fire-and-forget workflows

Parameters:
  - diagram: Name or path of the diagram to execute
  - input_data: Optional dictionary of input variables for the diagram
  - format_type: Diagram format - "light" | "native" | "readable" (default: "light")
  - timeout: Execution timeout in seconds (default: 300)

Examples:
  Start a long-running analysis:
    {
      "diagram": "data_analysis",
      "format_type": "light",
      "timeout": 600
    }

  Start with input data:
    {
      "diagram": "batch_processor",
      "input_data": {"batch_size": 1000, "dataset": "sales_2024"},
      "timeout": 900
    }

  Quick background job:
    {
      "diagram": "notification_sender",
      "input_data": {"recipients": ["alice@example.com"]},
      "format_type": "light"
    }

Returns:
  JSON object with session_id, status, and instructions to use see_result to check progress.
"""
)
async def run_backend(
    diagram: str,
    input_data: dict[str, Any] | None = None,
    format_type: str = "light",
    timeout: int = DEFAULT_MCP_TIMEOUT,
) -> list[TextContent]:
    if input_data is None:
        input_data = {}

    # Default to mcp-diagrams directory if diagram is just a name (no path separators)
    if "/" not in diagram and "\\" not in diagram:
        diagram = f"projects/mcp-diagrams/{diagram}"

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

        # Add timeout to prevent hanging
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            result = {
                "success": False,
                "error": "Background execution start timed out after 60 seconds",
                "diagram": diagram,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

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


@mcp_server.tool(
    description="""Check status and retrieve results of a background diagram execution.

Use this tool to check the status of a diagram started with run_backend.
Returns rich output including conversation history, node outputs, execution metadata, and LLM usage statistics.

Parameters:
  - session_id: The session ID returned by run_backend

Possible Statuses:
  - running: Execution in progress
  - completed: Execution finished successfully
  - failed: Execution encountered an error

Examples:
  Check status of background execution:
    {
      "session_id": "exec_9ebb3df7180a4a7383079680c28c6028"
    }

  Typical workflow:
    1. Start background: run_backend({"diagram": "analysis"})
       Returns: {"session_id": "exec_abc123..."}

    2. Check status: see_result({"session_id": "exec_abc123..."})
       Returns: {"status": "running", "executed_nodes": [...]}

    3. Check again: see_result({"session_id": "exec_abc123..."})
       Returns: {"status": "completed", "node_outputs": {...}, "llm_usage": {...}}

Returns:
  JSON object with:
    - session_id: The execution session identifier
    - status: Current execution status (running|completed|failed)
    - executed_nodes: List of nodes that have been executed
    - node_outputs: Final outputs from each node (if completed)
    - llm_usage: Token usage statistics (if completed)
    - started_at/ended_at: Timestamps
    - error: Error message (if failed)
"""
)
async def see_result(session_id: str) -> list[TextContent]:
    from dipeo_server.app_context import get_container
    from dipeo_server.cli import CLIRunner

    try:
        container = get_container()
        cli = CLIRunner(container)

        result_data = await cli.query.get_results_data(session_id, verbose=True)

        return [TextContent(type="text", text=json.dumps(result_data, indent=2))]

    except Exception as e:
        logger.error(f"Error retrieving result for {session_id}: {e}", exc_info=True)
        error_result = {
            "error": f"Error retrieving result: {e!s}",
            "session_id": session_id,
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


@mcp_server.tool(
    description="""Execute a DiPeO diagram synchronously with optional input variables.

Parameters:
  - diagram: Name or path of the diagram to execute
  - input_data: Optional dictionary of input variables for the diagram
  - format_type: Diagram format - "light" | "native" | "readable" (default: "light")
  - timeout: Execution timeout in seconds (default: 300)

Examples:
  Basic execution:
    {
      "diagram": "simple_iter",
      "format_type": "light"
    }

  With input data:
    {
      "diagram": "greeting_workflow",
      "input_data": {"user_name": "Alice"},
      "format_type": "light"
    }

  With timeout and complex inputs:
    {
      "diagram": "data_processing",
      "input_data": {
        "dataset": "sales_2024",
        "analysis_type": "trend",
        "granularity": "monthly"
      },
      "timeout": 600
    }

Returns:
  JSON object with execution status, results, and any errors.
"""
)
async def dipeo_run(
    diagram: str,
    input_data: dict[str, Any] | None = None,
    format_type: str = "light",
    timeout: int = DEFAULT_MCP_TIMEOUT,
) -> list[TextContent]:
    if input_data is None:
        input_data = {}

    # Default to mcp-diagrams directory if diagram is just a name (no path separators)
    if "/" not in diagram and "\\" not in diagram:
        diagram = f"projects/mcp-diagrams/{diagram}"

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


@mcp_server.tool(
    description="""Search for DiPeO diagrams by name across available directories.

Searches in:
  - projects/mcp-diagrams/ (uploaded diagrams)
  - examples/simple_diagrams/ (example diagrams)

The search is case-insensitive and matches against diagram names and paths.

Parameters:
  - query: Search term to match against diagram names

Examples:
  Search for iteration diagrams:
    {
      "query": "iter"
    }
    Returns: ["simple_iter", "multi_iter", ...]

  Search for greeting workflows:
    {
      "query": "greeting"
    }
    Returns: ["greeting_workflow", "hello_greeting", ...]

  Search for specific diagram:
    {
      "query": "data_analysis"
    }
    Returns: ["data_analysis"] (exact match)

  Broad search:
    {
      "query": "simple"
    }
    Returns: All diagrams containing "simple" in their name

Returns:
  JSON object with:
    - success: true
    - query: The search term used
    - count: Number of matching diagrams
    - results: Array of matching diagrams with name, path, format, and location
"""
)
async def search(query: str) -> list[TextContent]:
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


@mcp_server.tool(
    description="""Fetch the full content of a specific DiPeO diagram file.

Use this tool to retrieve the complete YAML or JSON content of a diagram.
Useful for inspecting diagram structure, understanding node configurations, or preparing diagrams for modification.

Parameters:
  - uri: Diagram URI or name to fetch

URI Formats:
  - dipeo://diagrams/diagram_name
  - diagram_name (shorthand)
  - /absolute/path/to/diagram.yaml

Examples:
  Fetch using URI:
    {
      "uri": "dipeo://diagrams/simple_iter"
    }

  Fetch using short name:
    {
      "uri": "simple_iter"
    }

  Fetch from MCP directory:
    {
      "uri": "greeting_workflow"
    }

  Fetch example diagram:
    {
      "uri": "examples/simple_diagrams/simple_iter.light.yaml"
    }

Returns:
  JSON object with:
    - success: true/false
    - uri: The requested URI
    - name: Diagram name (without extension)
    - path: Full file path
    - format: "light" or "native"
    - size: Content size in characters
    - content: Full diagram content (YAML or JSON)
    - error: Error message (if failed)
"""
)
async def fetch(uri: str) -> list[TextContent]:
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


@mcp_server.tool(
    description="""Validate and push a DiPeO diagram to the MCP directory.

This tool validates diagram syntax, structure, and configuration, then automatically
pushes the validated diagram to the MCP directory for immediate use.

Safe by Design:
  - Only validated diagrams are pushed
  - No file system access needed - works from text content
  - Prevents path traversal attacks

Parameters:
  - diagram_content: The complete diagram content (YAML or JSON string)
  - push_as: Filename to save validated diagram to projects/mcp-diagrams/
  - format_type: Diagram format - "light" | "native" | "readable" (default: "light")

Examples:
  Validate and push minimal workflow:
    {
      "diagram_content": "version: light\\nnodes:\\n- label: start\\n  type: start\\n  position: {x: 100, y: 100}\\n  trigger_mode: manual\\n- label: end\\n  type: endpoint\\n  position: {x: 300, y: 100}\\n  file_format: txt\\nconnections:\\n- {from: start, to: end, content_type: raw_text}",
      "push_as": "my_workflow",
      "format_type": "light"
    }

  Create and push greeting workflow:
    {
      "diagram_content": "<full YAML content here>",
      "push_as": "greeting_v2",
      "format_type": "light"
    }

  Push analysis diagram:
    {
      "diagram_content": "version: light\\nnodes:\\n...",
      "push_as": "data_analysis",
      "format_type": "light"
    }

Common Use Cases:
  1. LLM creates diagram → compile_diagram to validate and deploy
  2. User edits diagram → compile_diagram to update deployed version
  3. Automated workflow → compile_diagram for immediate availability

Returns:
  JSON object with:
    - success: true/false
    - valid: Whether diagram passed validation
    - errors: List of validation errors (if any)
    - warnings: List of validation warnings (if any)
    - node_count: Number of nodes in diagram
    - edge_count: Number of connections
    - pushed_as: Filename where diagram was saved
    - message: Human-readable status message
"""
)
async def compile_diagram(
    diagram_content: str,
    push_as: str,
    format_type: str = "light",
) -> list[TextContent]:
    try:
        # Sanitize push_as to prevent path traversal attacks
        # Check for path separators and traversal sequences
        if "/" in push_as or "\\" in push_as or ".." in push_as:
            result = {
                "success": False,
                "valid": False,
                "error": "Invalid filename: path separators and '..' are not allowed in push_as parameter",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # Additional validation: ensure it's a valid filename
        if not push_as.strip() or push_as.startswith("."):
            result = {
                "success": False,
                "valid": False,
                "error": "Invalid filename: push_as must be a valid filename (non-empty, not starting with '.')",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # Check for null bytes and control characters
        if "\x00" in push_as or any(ord(c) < 32 for c in push_as if c not in ("\t", "\n", "\r")):
            result = {
                "success": False,
                "valid": False,
                "error": "Invalid filename: null bytes and control characters are not allowed",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        cmd_args = [
            sys.executable,
            "-m",
            "dipeo_server.cli.entry_point",
            "compile",
            "--stdin",
            "--json",
        ]

        if format_type == "light":
            cmd_args.append("--light")
        elif format_type == "native":
            cmd_args.append("--native")
        elif format_type == "readable":
            cmd_args.append("--readable")

        # Always push with the provided filename
        cmd_args.extend(["--push-as", push_as])

        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Add timeout to prevent hanging (30 seconds should be sufficient for compilation)
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=diagram_content.encode()), timeout=30.0
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            result = {
                "success": False,
                "valid": False,
                "error": "Compilation timed out after 30 seconds",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            result = {
                "success": False,
                "valid": False,
                "error": f"Compilation failed: {error_msg}",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        output = stdout.decode().strip()
        compile_result = json.loads(output)

        result = {
            "success": True,
            "valid": compile_result.get("valid", False),
            "errors": compile_result.get("errors", []),
            "warnings": compile_result.get("warnings", []),
            "node_count": compile_result.get("node_count"),
            "edge_count": compile_result.get("edge_count"),
        }

        if compile_result.get("valid"):
            result["pushed_as"] = push_as
            result["message"] = f"Diagram validated and pushed to MCP directory as {push_as}"
        else:
            result["message"] = "Diagram validation failed - not pushed to MCP directory"

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error compiling diagram: {e}", exc_info=True)
        result = {
            "success": False,
            "valid": False,
            "error": f"Error compiling diagram: {e!s}",
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
