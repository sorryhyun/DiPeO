#!/usr/bin/env python3
"""
DiPeO CLI - Main entry point

Minimal command-line interface for DiPeO diagram operations.
"""

import argparse
import os
import sys
import warnings
from typing import Any

# Fix encoding issues on Windows
if sys.platform == "win32":
    # Set UTF-8 encoding for stdout and stderr
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    # Set environment variable for child processes
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"

from .commands import (
    AskCommand,
    ClaudeCodeCommand,
    ConvertCommand,
    IntegrationsCommand,
    MetricsCommand,
    RunCommand,
    UtilsCommand,
)
from .commands.base import DiagramLoader
from .server_manager import ServerManager

# Suppress non-critical warnings
warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)
warnings.filterwarnings("ignore", message="Field name.*shadows an attribute", category=UserWarning)


class DiPeOCLI:
    """Minimal DiPeO CLI - thin orchestration layer."""

    def __init__(self):
        self.server = ServerManager()

        # Initialize command handlers
        self.ask_command = AskCommand(self.server)
        self.run_command = RunCommand(self.server)
        self.convert_command = ConvertCommand()
        self.metrics_command = MetricsCommand(self.server)
        self.utils_command = UtilsCommand()
        self.integrations_command = IntegrationsCommand(self.server)
        self.claude_code_command = ClaudeCodeCommand(self.server)

    def ask(
        self,
        request: str,
        and_run: bool = False,
        debug: bool = False,
        timeout: int = 90,
        run_timeout: int = 300,
        no_browser: bool = True,
    ):
        """Generate a diagram from natural language and optionally run it."""
        return self.ask_command.execute(
            request=request,
            and_run=and_run,
            debug=debug,
            timeout=timeout,
            run_timeout=run_timeout,
            no_browser=no_browser,
        )

    def run(
        self,
        diagram: str,
        debug: bool = False,
        no_browser: bool = False,
        timeout: int = 300,
        format_type: str | None = None,
        input_variables: dict[str, Any] | None = None,
        use_unified: bool = True,  # Default to unified monitoring
        simple: bool = False,
    ):
        """Run a diagram via server."""
        return self.run_command.execute(
            diagram=diagram,
            debug=debug,
            no_browser=no_browser,
            timeout=timeout,
            format_type=format_type,
            input_variables=input_variables,
            use_unified=use_unified,
            simple=simple,
        )

    def convert(
        self,
        input_path: str,
        output_path: str,
        from_format: str | None = None,
        to_format: str | None = None,
    ):
        """Convert between diagram formats."""
        self.convert_command.execute(
            input_path=input_path,
            output_path=output_path,
            from_format=from_format,
            to_format=to_format,
        )

    def stats(self, diagram_path: str):
        """Show diagram statistics."""
        self.utils_command.stats(diagram_path)

    def monitor(self, diagram_name: str | None = None):
        """Open browser monitor."""
        self.utils_command.monitor(diagram_name)

    def metrics(
        self,
        execution_id: str | None = None,
        diagram_id: str | None = None,
        bottlenecks_only: bool = False,
        optimizations_only: bool = False,
        output_json: bool = False,
    ):
        """Display execution metrics."""
        self.metrics_command.execute(
            execution_id=execution_id,
            diagram_id=diagram_id,
            bottlenecks_only=bottlenecks_only,
            optimizations_only=optimizations_only,
            output_json=output_json,
        )

    def integrations(self, action: str, **kwargs):
        """Manage integrations."""
        return self.integrations_command.execute(action, **kwargs)

    def claude_code(self, action: str, **kwargs):
        """Convert Claude Code sessions to DiPeO diagrams."""
        return self.claude_code_command.execute(action, **kwargs)

    # Compatibility methods for backward compatibility
    def resolve_diagram_path(self, diagram: str, format_type: str | None = None) -> str:
        """Resolve diagram path based on format type (backward compatibility)."""
        loader = DiagramLoader()
        return loader.resolve_diagram_path(diagram, format_type)

    def load_diagram(self, file_path: str) -> dict[str, Any]:
        """Load diagram from file (backward compatibility)."""
        loader = DiagramLoader()
        return loader.load_diagram(file_path)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DiPeO CLI - Simplified Interface")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Generate diagram from natural language")
    ask_parser.add_argument(
        "--to",
        type=str,
        required=True,
        help="Natural language description of what to create",
    )
    ask_parser.add_argument(
        "--and-run",
        action="store_true",
        help="Automatically run the generated diagram",
    )
    ask_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    ask_parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="Generation timeout in seconds (default: 90)",
    )
    ask_parser.add_argument(
        "--run-timeout",
        type=int,
        default=300,
        help="Execution timeout for generated diagram in seconds (default: 300)",
    )
    ask_parser.add_argument(
        "--browser",
        action="store_true",
        help="Open browser when running generated diagram",
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a diagram")
    run_parser.add_argument(
        "diagram",
        help="Path to diagram file or diagram name (when using format options)",
    )
    run_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    run_parser.add_argument(
        "--browser", action="store_true", help="Open browser to monitor execution"
    )
    run_parser.add_argument("--quiet", action="store_true", help="Minimal output")
    run_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Execution timeout in seconds (default: 300)",
    )
    run_parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple text display instead of rich UI",
    )

    # Input data options (mutually exclusive)
    input_group = run_parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--inputs",
        type=str,
        help="Path to JSON file containing input variables for the diagram",
    )
    input_group.add_argument(
        "--input-data",
        type=str,
        help='Inline JSON string with input variables (e.g., \'{"node_spec_path": "sub_diagram"}\')',
    )

    # Format options (mutually exclusive)
    format_group = run_parser.add_mutually_exclusive_group()
    format_group.add_argument("--light", action="store_true", help="Use light format (YAML)")
    format_group.add_argument("--native", action="store_true", help="Use native format (JSON)")
    format_group.add_argument("--readable", action="store_true", help="Use readable format (YAML)")

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("output", help="Output file")
    convert_parser.add_argument(
        "--from-format",
        choices=["native", "light", "readable"],
        help="Source format (auto-detected if not specified)",
    )
    convert_parser.add_argument(
        "--to-format",
        choices=["native", "light", "readable"],
        help="Target format (auto-detected from output extension if not specified)",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show diagram statistics")
    stats_parser.add_argument("diagram", help="Path to diagram file")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Open browser monitor")
    monitor_parser.add_argument("diagram", nargs="?", help="Diagram name")

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Display execution metrics")
    metrics_parser.add_argument(
        "execution_id",
        nargs="?",
        help="Execution ID to show metrics for (shows latest if not specified)",
    )
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

    # Init subcommand
    init_parser = integrations_subparsers.add_parser(
        "init", help="Initialize integrations workspace"
    )
    init_parser.add_argument(
        "--path", type=str, help="Path to initialize (default: ./integrations)"
    )

    # Validate subcommand
    validate_parser = integrations_subparsers.add_parser(
        "validate", help="Validate provider manifests"
    )
    validate_parser.add_argument("--path", type=str, help="Path to integrations directory")
    validate_parser.add_argument("--provider", type=str, help="Validate specific provider only")

    # OpenAPI import subcommand
    openapi_parser = integrations_subparsers.add_parser(
        "openapi-import", help="Import OpenAPI specification"
    )
    openapi_parser.add_argument("openapi_path", help="Path to OpenAPI spec file")
    openapi_parser.add_argument("--name", required=True, help="Provider name")
    openapi_parser.add_argument("--output", type=str, help="Output directory")
    openapi_parser.add_argument("--base-url", type=str, help="Override base URL")

    # Test subcommand
    test_parser = integrations_subparsers.add_parser("test", help="Test integration provider")
    test_parser.add_argument("provider", help="Provider name to test")
    test_parser.add_argument("--operation", type=str, help="Specific operation to test")
    test_parser.add_argument("--config", type=str, help="Test configuration JSON")
    test_parser.add_argument("--record", action="store_true", help="Record test for replay")
    test_parser.add_argument("--replay", action="store_true", help="Replay recorded test")

    # Claude Code subcommand
    claude_code_parser = integrations_subparsers.add_parser(
        "claude-code", help="Manage Claude Code TODO synchronization"
    )
    claude_code_parser.add_argument(
        "--watch-todos", action="store_true", help="Enable TODO monitoring"
    )
    claude_code_parser.add_argument(
        "--sync-mode",
        type=str,
        default="off",
        choices=["off", "manual", "auto", "watch"],
        help="Synchronization mode (default: off)",
    )
    claude_code_parser.add_argument(
        "--output-dir", type=str, help="Output directory for diagrams (default: projects/dipeo_cc)"
    )
    claude_code_parser.add_argument(
        "--auto-execute", action="store_true", help="Automatically execute generated diagrams"
    )
    claude_code_parser.add_argument(
        "--debounce", type=float, default=2.0, help="Debounce time in seconds (default: 2.0)"
    )
    claude_code_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds for monitoring (no timeout if not specified)",
    )

    # DiPeOCC command for Claude Code session conversion
    dipeocc_parser = subparsers.add_parser(
        "dipeocc", help="Convert Claude Code sessions to DiPeO diagrams"
    )
    dipeocc_subparsers = dipeocc_parser.add_subparsers(
        dest="dipeocc_action", help="DiPeOCC commands"
    )

    # List subcommand
    list_parser = dipeocc_subparsers.add_parser("list", help="List recent Claude Code sessions")
    list_parser.add_argument(
        "--limit", type=int, default=50, help="Maximum number of sessions to list (default: 50)"
    )
    list_parser.add_argument("--debug", action="store_true", help="(Ignored for dipeocc commands)")

    # Convert subcommand
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
        help="Convert the N most recent sessions (default: 1 if no value provided)",
    )
    convert_parser.add_argument(
        "--output-dir", type=str, help="Output directory (default: projects/claude_code)"
    )
    convert_parser.add_argument(
        "--format",
        type=str,
        choices=["light", "native", "readable"],
        default="light",
        help="Output format (default: light)",
    )
    convert_parser.add_argument(
        "--debug", action="store_true", help="(Ignored for dipeocc commands)"
    )

    # Watch subcommand
    watch_parser = dipeocc_subparsers.add_parser(
        "watch", help="Watch for new sessions and convert automatically"
    )
    watch_parser.add_argument(
        "--interval", type=int, default=30, help="Check interval in seconds (default: 30)"
    )
    watch_parser.add_argument("--debug", action="store_true", help="(Ignored for dipeocc commands)")

    # Stats subcommand
    stats_cc_parser = dipeocc_subparsers.add_parser(
        "stats", help="Show detailed session statistics"
    )
    stats_cc_parser.add_argument("session_id", help="Session ID to analyze")
    stats_cc_parser.add_argument(
        "--debug", action="store_true", help="(Ignored for dipeocc commands)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = DiPeOCLI()

    try:
        if args.command == "ask":
            success = cli.ask(
                request=args.to,
                and_run=args.and_run,
                debug=args.debug,
                timeout=args.timeout,
                run_timeout=args.run_timeout,
                no_browser=not args.browser,  # Invert logic
            )
            os._exit(0 if success else 1)
        elif args.command == "run":
            # Determine format type
            format_type = None
            if args.light:
                format_type = "light"
            elif args.native:
                format_type = "native"
            elif args.readable:
                format_type = "readable"

            # Parse input data
            input_variables = None
            if args.inputs:
                # Load from file
                import json
                from pathlib import Path

                input_path = Path(args.inputs)
                if not input_path.exists():
                    print(f"Error: Input file not found: {args.inputs}")
                    sys.exit(1)
                try:
                    with input_path.open(encoding="utf-8") as f:
                        input_variables = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in input file: {e}")
                    sys.exit(1)
            elif args.input_data:
                # Parse inline JSON
                import json

                try:
                    input_variables = json.loads(args.input_data)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in input data: {e}")
                    sys.exit(1)

            success = cli.run(
                args.diagram,
                args.debug,
                not args.browser,  # Invert the logic: default is no browser
                args.timeout,
                format_type,
                input_variables,
                True,  # Always use unified monitoring
                args.simple,  # Use simple display if flag is set
            )
            # Use os._exit for forced termination to ensure all threads/subprocesses are killed
            os._exit(0 if success else 1)
        elif args.command == "convert":
            cli.convert(
                args.input,
                args.output,
                from_format=getattr(args, "from_format", None),
                to_format=getattr(args, "to_format", None),
            )
        elif args.command == "stats":
            cli.stats(args.diagram)
        elif args.command == "monitor":
            cli.monitor(args.diagram)
        elif args.command == "metrics":
            cli.metrics(
                execution_id=args.execution_id,
                diagram_id=args.diagram,
                bottlenecks_only=args.bottlenecks,
                optimizations_only=args.optimizations,
                output_json=args.json,
            )
        elif args.command == "integrations":
            if not args.integrations_action:
                integrations_parser.print_help()
                sys.exit(0)

            # Build kwargs based on action
            kwargs = {}
            print(f"DEBUG: integrations action = {args.integrations_action}")
            if args.integrations_action == "init":
                kwargs["path"] = getattr(args, "path", None)
            elif args.integrations_action == "validate":
                kwargs["path"] = getattr(args, "path", None)
                kwargs["provider"] = getattr(args, "provider", None)
            elif args.integrations_action == "openapi-import":
                kwargs["openapi_path"] = args.openapi_path
                kwargs["name"] = args.name
                kwargs["output"] = getattr(args, "output", None)
                kwargs["base_url"] = getattr(args, "base_url", None)
            elif args.integrations_action == "test":
                kwargs["provider"] = args.provider
                kwargs["operation"] = getattr(args, "operation", None)
                kwargs["config"] = getattr(args, "config", None)
                kwargs["record"] = getattr(args, "record", False)
                kwargs["replay"] = getattr(args, "replay", False)
            elif args.integrations_action == "claude-code":
                kwargs["watch_todos"] = getattr(args, "watch_todos", False)
                kwargs["sync_mode"] = getattr(args, "sync_mode", "off")
                kwargs["output_dir"] = getattr(args, "output_dir", None)
                kwargs["auto_execute"] = getattr(args, "auto_execute", False)
                kwargs["debounce"] = getattr(args, "debounce", 2.0)
                kwargs["timeout"] = getattr(args, "timeout", None)

            print(
                f"DEBUG: calling cli.integrations with action={args.integrations_action}, kwargs={kwargs}"
            )
            success = cli.integrations(args.integrations_action, **kwargs)
            os._exit(0 if success else 1)
        elif args.command == "dipeocc":
            if not args.dipeocc_action:
                dipeocc_parser.print_help()
                sys.exit(0)

            # Build kwargs based on action
            kwargs = {}
            if args.dipeocc_action == "list":
                kwargs["limit"] = getattr(args, "limit", 50)
            elif args.dipeocc_action == "convert":
                kwargs["session_id"] = getattr(args, "session_id", None)
                kwargs["latest"] = getattr(args, "latest", False)
                kwargs["output_dir"] = getattr(args, "output_dir", None)
                kwargs["format"] = getattr(args, "format", "light")
            elif args.dipeocc_action == "watch":
                kwargs["interval"] = getattr(args, "interval", 30)
            elif args.dipeocc_action == "stats":
                kwargs["session_id"] = args.session_id

            success = cli.claude_code(args.dipeocc_action, **kwargs)
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        cli.server.stop()
        os._exit(1)
    except Exception as e:
        print(f"Error: {e}")
        cli.server.stop()
        os._exit(1)


def dipeocc_main():
    """Direct entry point for dipeocc command."""
    import sys

    # Insert 'dipeocc' as the first argument to simulate the subcommand
    sys.argv = [sys.argv[0], "dipeocc"] + sys.argv[1:]
    main()


if __name__ == "__main__":
    main()
