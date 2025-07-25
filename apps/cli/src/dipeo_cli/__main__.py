#!/usr/bin/env python3
"""
DiPeO CLI - Main entry point

Minimal command-line interface for DiPeO diagram operations.
"""

import argparse
import sys

from .cli import DiPeOCLI


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
        "--no-browser", action="store_true", help="Skip browser opening"
    )
    run_parser.add_argument("--quiet", action="store_true", help="Minimal output")
    run_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Execution timeout in seconds (default: 300)",
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
        help="Inline JSON string with input variables (e.g., '{\"node_spec_path\": \"sub_diagram\"}')",
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
                    with input_path.open() as f:
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
                args.diagram, args.debug, args.no_browser, args.timeout, format_type, input_variables
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

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        cli.server.stop()


if __name__ == "__main__":
    main()
