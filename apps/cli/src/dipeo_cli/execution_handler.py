import asyncio
import json
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from .execution_options import ExecutionMode, ExecutionOptions, parse_run_options
from .runners import LocalDiagramRunner, ServerDiagramRunner
from .server_manager import restart_backend_server, stop_backend_server
from .utils import DiagramLoader


def _resolve_diagram_path(path: str, format_id: str | None) -> str:
    """Resolve short diagram names to full paths based on format.
    
    If the path is a short name (no path separators and no extension),
    resolve it to the appropriate directory based on the format.
    
    Examples:
        quicksave --format=light -> files/diagrams/light/quicksave.yaml
        quicksave --format=native -> files/diagrams/native/quicksave.json
        quicksave --format=readable -> files/diagrams/readable/quicksave.yaml
    """
    path_obj = Path(path)
    
    # Check if it's a short name (no path separators and no extension)
    if "/" not in path and "\\" not in path and not path_obj.suffix:
        # Determine format from options or default to native
        if format_id is None:
            format_id = "native"
            
        # Map format to directory and extension
        format_mapping = {
            "native": ("native", ".json"),
            "light": ("light", ".yaml"),
            "readable": ("readable", ".yaml")
        }
        
        if format_id in format_mapping:
            dir_name, extension = format_mapping[format_id]
            resolved_path = f"files/diagrams/{dir_name}/{path}{extension}"
            
            # Check if the file exists
            if Path(resolved_path).exists():
                print(f"✓ Resolved '{path}' to '{resolved_path}'")
                return resolved_path
            else:
                print(f"⚠️  Warning: Resolved path '{resolved_path}' does not exist")
                # Fall back to original path
    
    return path


async def run_command(args: list[str]) -> None:
    """Execute run command"""
    if not args:
        print("Error: Missing input file")
        return

    file_path = args[0]
    options = parse_run_options(args[1:])
    
    # Resolve short diagram names based on format
    file_path = _resolve_diagram_path(file_path, options.format)
    
    options.diagram_file = file_path  # Store the file path for later use

    # Load diagram
    diagram = DiagramLoader.load(file_path, format_id=options.format)

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

    # Display conversation logs
    _display_conversation_logs(result, options)

    # Save results
    _save_results(result, options)

    # Kill server in debug mode to see final logs (unless --keep-server is used or monitor mode is active)
    if (
        options.debug
        and not options.keep_server
        and options.mode != ExecutionMode.MONITOR
    ):
        # Only show server shutdown message if in verbose debug mode
        verbose_debug = os.environ.get("VERBOSE_DEBUG", "false").lower() == "true"
        if verbose_debug:
            await stop_backend_server()
        else:
            # Silently stop the server for cleaner output
            try:
                subprocess.run(
                    ["pkill", "-f", "python main.py"], check=False, capture_output=True
                )
                subprocess.run(
                    ["pkill", "-f", "hypercorn"], check=False, capture_output=True
                )
            except Exception:
                pass
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


def _display_conversation_logs(result: dict[str, Any], options: ExecutionOptions) -> None:
    """Display conversation logs from execution results."""
    context = result.get("context", {})
    
    # Collect all conversations from node outputs
    conversations = []
    for node_id, node_output in context.items():
        if isinstance(node_output, dict) and "value" in node_output:
            value = node_output["value"]
            if isinstance(value, dict) and "conversation" in value:
                conversation = value["conversation"]
                if conversation:
                    conversations.append({
                        "node_id": node_id,
                        "conversation": conversation
                    })
    
    # Display conversations if found
    if conversations:
        print("\n📝 Conversation Logs:")
        print("=" * 60)
        
        for conv_data in conversations:
            node_id = conv_data["node_id"]
            conversation = conv_data["conversation"]
            
            # Get person label from first message if available
            person_label = None
            if conversation and isinstance(conversation[0], dict):
                person_label = conversation[0].get("person_label", conversation[0].get("person_id", node_id))
            
            print(f"\n🤖 Person: {person_label or node_id}")
            print("-" * 40)
            
            for msg in conversation:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                # Format role display
                role_icon = "👤" if role == "user" else "🤖" if role == "assistant" else "📎"
                role_display = role.capitalize()
                
                # Display message
                print(f"\n{role_icon} {role_display}:")
                # Indent content for readability
                for line in content.split('\n'):
                    print(f"   {line}")
        
        print("\n" + "=" * 60)


def _save_results(result: dict[str, Any], options: ExecutionOptions) -> None:
    """Save execution results"""
    Path("files/results").mkdir(parents=True, exist_ok=True)
    save_path = options.output_file or "files/results/results.json"

    with open(save_path, "w") as f:
        json.dump(result, f, indent=2)

    if options.debug:
        print(f"  Results saved to: {save_path}")
