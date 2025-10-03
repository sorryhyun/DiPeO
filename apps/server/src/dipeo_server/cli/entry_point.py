#!/usr/bin/env python3
"""Unified entry point for DiPeO - can run as server or CLI."""

import argparse
import asyncio
import json
import os
import sys

# Fix encoding issues on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"


async def run_cli_command(args: argparse.Namespace) -> bool:
    """Run CLI command using direct service calls."""
    from dipeo.application.bootstrap import init_resources, shutdown_resources
    from dipeo.infrastructure.logging_config import setup_logging
    from dipeo_server.app_context import create_server_container
    from dipeo_server.cli import CLIRunner

    # Setup logging for CLI
    debug = getattr(args, "debug", False)
    log_level = "DEBUG" if debug else os.environ.get("DIPEO_LOG_LEVEL", "INFO")
    setup_logging(component="cli", log_level=log_level, log_to_file=True, console_output=debug)

    # Create container and initialize resources
    container = await create_server_container()
    await init_resources(container)

    try:
        # Create CLI runner
        cli = CLIRunner(container)

        # Execute command
        if args.command == "ask":
            return await cli.ask_diagram(
                request=args.to,
                and_run=args.and_run,
                debug=args.debug,
                timeout=args.timeout,
                run_timeout=args.run_timeout,
            )

        elif args.command == "run":
            # Determine format type
            format_type = None
            if hasattr(args, "light") and args.light:
                format_type = "light"
            elif hasattr(args, "native") and args.native:
                format_type = "native"
            elif hasattr(args, "readable") and args.readable:
                format_type = "readable"

            # Parse input data
            input_variables = None
            if hasattr(args, "inputs") and args.inputs:
                with open(args.inputs) as f:
                    input_variables = json.load(f)
            elif hasattr(args, "input_data") and args.input_data:
                input_variables = json.loads(args.input_data)

            return await cli.run_diagram(
                diagram=args.diagram,
                debug=args.debug,
                timeout=args.timeout,
                format_type=format_type,
                input_variables=input_variables,
                use_unified=True,
                simple=hasattr(args, "simple") and args.simple,
            )

        elif args.command == "convert":
            return await cli.convert_diagram(
                input_path=args.input,
                output_path=args.output,
                from_format=getattr(args, "from_format", None),
                to_format=getattr(args, "to_format", None),
            )

        elif args.command == "stats":
            return await cli.show_stats(args.diagram)

        elif args.command == "monitor":
            # Open browser monitor
            import webbrowser

            url = "http://localhost:3000/?monitor=true"
            if args.diagram:
                url += f"&diagram={args.diagram}"
            webbrowser.open(url)
            return True

        elif args.command == "metrics":
            return await cli.show_metrics(
                execution_id=args.execution_id,
                diagram_id=getattr(args, "diagram", None),
                bottlenecks_only=getattr(args, "bottlenecks", False),
                optimizations_only=getattr(args, "optimizations", False),
                output_json=getattr(args, "json", False),
            )

        elif args.command == "integrations":
            action = args.integrations_action
            kwargs = {}

            if action == "init":
                kwargs["path"] = getattr(args, "path", None)
            elif action == "validate":
                kwargs["path"] = getattr(args, "path", None)
                kwargs["provider"] = getattr(args, "provider", None)
            elif action == "openapi-import":
                kwargs["openapi_path"] = args.openapi_path
                kwargs["name"] = args.name
                kwargs["output"] = getattr(args, "output", None)
                kwargs["base_url"] = getattr(args, "base_url", None)
            elif action == "test":
                kwargs["provider"] = args.provider
                kwargs["operation"] = getattr(args, "operation", None)
                kwargs["config"] = getattr(args, "config", None)
                kwargs["record"] = getattr(args, "record", False)
                kwargs["replay"] = getattr(args, "replay", False)
            elif action == "claude-code":
                kwargs["watch_todos"] = getattr(args, "watch_todos", False)
                kwargs["sync_mode"] = getattr(args, "sync_mode", "off")
                kwargs["output_dir"] = getattr(args, "output_dir", None)
                kwargs["auto_execute"] = getattr(args, "auto_execute", False)
                kwargs["debounce"] = getattr(args, "debounce", 2.0)
                kwargs["timeout"] = getattr(args, "timeout", None)

            return await cli.manage_integrations(action, **kwargs)

        elif args.command == "dipeocc":
            action = args.dipeocc_action
            kwargs = {}

            if action == "list":
                kwargs["limit"] = getattr(args, "limit", 50)
            elif action == "convert":
                kwargs["session_id"] = getattr(args, "session_id", None)
                kwargs["latest"] = getattr(args, "latest", False)
                kwargs["output_dir"] = getattr(args, "output_dir", None)
                kwargs["format"] = getattr(args, "format", "light")
            elif action == "watch":
                kwargs["interval"] = getattr(args, "interval", 30)
            elif action == "stats":
                kwargs["session_id"] = args.session_id

            return await cli.manage_claude_code(action, **kwargs)

        else:
            print(f"Unknown command: {args.command}")
            return False

    finally:
        # Cleanup
        await shutdown_resources(container)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI commands."""
    parser = argparse.ArgumentParser(description="DiPeO - Unified Interface")
    parser.add_argument("--server", action="store_true", help="Run as server (default)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Generate diagram from natural language")
    ask_parser.add_argument("--to", type=str, required=True, help="Natural language description")
    ask_parser.add_argument(
        "--and-run", action="store_true", help="Automatically run the generated diagram"
    )
    ask_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    ask_parser.add_argument("--timeout", type=int, default=90, help="Generation timeout in seconds")
    ask_parser.add_argument(
        "--run-timeout", type=int, default=300, help="Execution timeout in seconds"
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a diagram")
    run_parser.add_argument("diagram", help="Path to diagram file or diagram name")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    run_parser.add_argument("--timeout", type=int, default=300, help="Execution timeout in seconds")
    run_parser.add_argument("--simple", action="store_true", help="Use simple text display")

    # Input data options
    input_group = run_parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--inputs", type=str, help="Path to JSON file containing input variables"
    )
    input_group.add_argument(
        "--input-data", type=str, help="Inline JSON string with input variables"
    )

    # Format options
    format_group = run_parser.add_mutually_exclusive_group()
    format_group.add_argument("--light", action="store_true", help="Use light format (YAML)")
    format_group.add_argument("--native", action="store_true", help="Use native format (JSON)")
    format_group.add_argument("--readable", action="store_true", help="Use readable format (YAML)")

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("output", help="Output file")
    convert_parser.add_argument(
        "--from-format", choices=["native", "light", "readable"], help="Source format"
    )
    convert_parser.add_argument(
        "--to-format", choices=["native", "light", "readable"], help="Target format"
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show diagram statistics")
    stats_parser.add_argument("diagram", help="Path to diagram file")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Open browser monitor")
    monitor_parser.add_argument("diagram", nargs="?", help="Diagram name")

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Display execution metrics")
    metrics_parser.add_argument("execution_id", nargs="?", help="Execution ID to show metrics for")
    metrics_parser.add_argument(
        "--diagram", type=str, help="Show metrics history for specific diagram"
    )
    metrics_parser.add_argument(
        "--bottlenecks", action="store_true", help="Show only bottleneck analysis"
    )
    metrics_parser.add_argument(
        "--optimizations", action="store_true", help="Show optimization suggestions"
    )
    metrics_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Integrations command
    integrations_parser = subparsers.add_parser("integrations", help="Manage API integrations")
    integrations_subparsers = integrations_parser.add_subparsers(
        dest="integrations_action", help="Integration commands"
    )

    # Integrations subcommands
    init_parser = integrations_subparsers.add_parser(
        "init", help="Initialize integrations workspace"
    )
    init_parser.add_argument("--path", type=str, help="Path to initialize")

    validate_parser = integrations_subparsers.add_parser(
        "validate", help="Validate provider manifests"
    )
    validate_parser.add_argument("--path", type=str, help="Path to integrations directory")
    validate_parser.add_argument("--provider", type=str, help="Validate specific provider only")

    openapi_parser = integrations_subparsers.add_parser(
        "openapi-import", help="Import OpenAPI specification"
    )
    openapi_parser.add_argument("openapi_path", help="Path to OpenAPI spec file")
    openapi_parser.add_argument("--name", required=True, help="Provider name")
    openapi_parser.add_argument("--output", type=str, help="Output directory")
    openapi_parser.add_argument("--base-url", type=str, help="Override base URL")

    test_parser = integrations_subparsers.add_parser("test", help="Test integration provider")
    test_parser.add_argument("provider", help="Provider name to test")
    test_parser.add_argument("--operation", type=str, help="Specific operation to test")
    test_parser.add_argument("--config", type=str, help="Test configuration JSON")
    test_parser.add_argument("--record", action="store_true", help="Record test for replay")
    test_parser.add_argument("--replay", action="store_true", help="Replay recorded test")

    claude_code_parser = integrations_subparsers.add_parser(
        "claude-code", help="Manage Claude Code TODO synchronization"
    )
    claude_code_parser.add_argument(
        "--watch-todos", action="store_true", help="Enable TODO monitoring"
    )
    claude_code_parser.add_argument(
        "--sync-mode", type=str, default="off", choices=["off", "manual", "auto", "watch"]
    )
    claude_code_parser.add_argument("--output-dir", type=str, help="Output directory for diagrams")
    claude_code_parser.add_argument(
        "--auto-execute", action="store_true", help="Automatically execute generated diagrams"
    )
    claude_code_parser.add_argument(
        "--debounce", type=float, default=2.0, help="Debounce time in seconds"
    )
    claude_code_parser.add_argument("--timeout", type=int, help="Timeout in seconds for monitoring")

    # DiPeOCC command
    dipeocc_parser = subparsers.add_parser(
        "dipeocc", help="Convert Claude Code sessions to DiPeO diagrams"
    )
    dipeocc_subparsers = dipeocc_parser.add_subparsers(
        dest="dipeocc_action", help="DiPeOCC commands"
    )

    list_parser = dipeocc_subparsers.add_parser("list", help="List recent Claude Code sessions")
    list_parser.add_argument(
        "--limit", type=int, default=50, help="Maximum number of sessions to list"
    )

    convert_parser = dipeocc_subparsers.add_parser(
        "convert", help="Convert a session to DiPeO diagram"
    )
    convert_group = convert_parser.add_mutually_exclusive_group(required=True)
    convert_group.add_argument("session_id", nargs="?", help="Session ID to convert")
    convert_group.add_argument(
        "--latest",
        nargs="?",
        const=1,
        type=int,
        metavar="N",
        help="Convert the N most recent sessions",
    )
    convert_parser.add_argument("--output-dir", type=str, help="Output directory")
    convert_parser.add_argument(
        "--format", type=str, choices=["light", "native", "readable"], default="light"
    )

    watch_parser = dipeocc_subparsers.add_parser(
        "watch", help="Watch for new sessions and convert automatically"
    )
    watch_parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")

    stats_cc_parser = dipeocc_subparsers.add_parser(
        "stats", help="Show detailed session statistics"
    )
    stats_cc_parser.add_argument("session_id", help="Session ID to analyze")

    return parser


def main():
    """Main entry point."""
    import warnings

    warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)
    warnings.filterwarnings(
        "ignore", message="Field name.*shadows an attribute", category=UserWarning
    )

    parser = create_parser()
    args = parser.parse_args()

    # If no command specified or --server flag, run as server
    if not args.command or args.server:
        # Run as server
        import uvicorn

        from dipeo.infrastructure.logging_config import setup_logging

        # Setup logging
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        logger = setup_logging(
            component="server",
            log_level=log_level,
            log_to_file=True,
            log_dir=".logs",
            console_output=True,
        )

        # Import and run server
        from apps.server.main import app

        uvicorn.run(
            app,
            host=args.host if hasattr(args, "host") else "0.0.0.0",
            port=args.port if hasattr(args, "port") else 8000,
            log_level=log_level.lower(),
        )
    else:
        # Run as CLI
        try:
            success = asyncio.run(run_cli_command(args))
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


def dipeocc_main():
    """Direct entry point for dipeocc command."""
    # Insert 'dipeocc' as the first argument to simulate the subcommand
    sys.argv = [sys.argv[0], "dipeocc"] + sys.argv[1:]
    main()


if __name__ == "__main__":
    main()
