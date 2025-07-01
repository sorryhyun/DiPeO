import asyncio
import json
import webbrowser
from pathlib import Path
from typing import Any

from .execution_options import ExecutionMode, ExecutionOptions, parse_run_options
from .runners import LocalDiagramRunner, ServerDiagramRunner
from .server_manager import restart_backend_server, stop_backend_server
from .utils import DiagramLoader, to_graphql_format


async def run_command(args: list[str]) -> None:
    """Execute run command"""
    if not args:
        print("Error: Missing input file")
        return

    file_path = args[0]
    options = parse_run_options(args[1:])
    options.diagram_file = file_path  # Store the file path for later use

    # Load diagram
    diagram = DiagramLoader.load(file_path, format_id=options.format)

    # Convert to GraphQL format if needed
    diagram = to_graphql_format(diagram)

    # Execute based on mode
    if options.local:
        # Local execution without server
        print("🏠 Running in local mode (no server required)...")
        local_executor = LocalDiagramRunner(options)
        result = await local_executor.execute(diagram)
    else:
        # Server-based execution
        # Restart backend server if debug mode
        if options.debug:
            await restart_backend_server()

        # Handle special modes
        if options.mode == ExecutionMode.MONITOR:
            await _run_monitor_mode(diagram, options)
            # Don't return here - continue to execute the diagram

        # Execute diagram (both for normal and monitor mode)
        server_executor = ServerDiagramRunner(options)
        result = await server_executor.execute(diagram)

    print(
        f"✓ Execution complete - Total token count: {result.get('total_token_count', 0)}"
    )

    # Save results
    _save_results(result, options)

    # Kill server in debug mode to see final logs (unless --keep-server is used or monitor mode is active)
    if (
        options.debug
        and not options.keep_server
        and options.mode != ExecutionMode.MONITOR
    ):
        await stop_backend_server()
    elif options.debug and (
        options.keep_server or options.mode == ExecutionMode.MONITOR
    ):
        print("\n🐛 Debug: Server kept running", end="")
        if options.mode == ExecutionMode.MONITOR:
            print(" (monitor mode active)")
            print(
                "📊 Monitor remains available at: http://localhost:3000/?monitor=true"
            )
            print("   ℹ️  Press Ctrl+C to stop the server when done monitoring")
        else:
            print(" (--keep-server flag used)")


async def _run_monitor_mode(diagram: dict[str, Any], options: ExecutionOptions) -> None:
    """Handle monitor mode setup"""
    # Extract diagram ID from file path (e.g., quicksave.json -> quicksave)
    if options.diagram_file:
        diagram_id = Path(options.diagram_file).stem
    else:
        # Fallback to metadata name or "unknown"
        diagram_id = diagram.get("metadata", {}).get("name", "unknown")

    # Open browser with both monitor mode and diagram ID
    monitor_url = f"http://localhost:3000/?monitor=true&diagram={diagram_id}"
    webbrowser.open(monitor_url)

    # Wait for browser to load
    await asyncio.sleep(2.0)
    print(f"✓ Monitor ready - Diagram: {diagram_id}")

    if options.debug:
        print("💡 Tip: Server will remain running after execution for monitoring")


def _save_results(result: dict[str, Any], options: ExecutionOptions) -> None:
    """Save execution results"""
    Path("files/results").mkdir(parents=True, exist_ok=True)
    save_path = options.output_file or "files/results/results.json"

    with open(save_path, "w") as f:
        json.dump(result, f, indent=2)

    if options.debug:
        print(f"  Results saved to: {save_path}")
