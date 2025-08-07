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

from .commands import ConvertCommand, MetricsCommand, RunCommand, UtilsCommand
from .commands.base import DiagramLoader
from .server_manager import ServerManager

# Suppress non-critical warnings
warnings.filterwarnings(
    "ignore", message="Pydantic serializer warnings", category=UserWarning
)
warnings.filterwarnings(
    "ignore", message="Field name.*shadows an attribute", category=UserWarning
)


class DiPeOCLI:
    """Minimal DiPeO CLI - thin orchestration layer."""

    def __init__(self):
        self.server = ServerManager()

        # Initialize command handlers
        self.run_command = RunCommand(self.server)
        self.convert_command = ConvertCommand()
        self.metrics_command = MetricsCommand(self.server)
        self.utils_command = UtilsCommand()

    def run(
        self,
        diagram: str,
        debug: bool = False,
        no_browser: bool = False,
        timeout: int = 300,
        format_type: str | None = None,
        input_variables: dict[str, Any] | None = None,
        use_unified: bool = False,
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
        "--legacy",
        action="store_true",
        help="Use legacy monitoring architecture (deprecated)",
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
    format_group.add_argument(
        "--light", action="store_true", help="Use light format (YAML)"
    )
    format_group.add_argument(
        "--native", action="store_true", help="Use native format (JSON)"
    )
    format_group.add_argument(
        "--readable", action="store_true", help="Use readable format (YAML)"
    )

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
        help="Execution ID to show metrics for (shows latest if not specified)"
    )
    metrics_parser.add_argument(
        "--diagram",
        type=str,
        help="Show metrics history for specific diagram"
    )
    metrics_parser.add_argument(
        "--bottlenecks",
        action="store_true",
        help="Show only bottleneck analysis"
    )
    metrics_parser.add_argument(
        "--optimizations",
        action="store_true",
        help="Show optimization suggestions"
    )
    metrics_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = DiPeOCLI()

    try:
        if args.command == "run":
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
                not args.legacy,  # Use unified by default, legacy only if flag is set
            )
            sys.exit(0 if success else 1)
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
                output_json=args.json
            )

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        cli.server.stop()
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        cli.server.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
