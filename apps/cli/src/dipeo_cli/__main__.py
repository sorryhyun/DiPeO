"""
Main CLI entry point for DiPeO.

This module provides the command-line interface for DiPeO diagram operations.
"""

import asyncio
import sys

from .convert import convert_command as convert
from .execution_handler import run_command as run
from .monitor import monitor_command as monitor
from .stats import stats_command as stats
from .hooks import hook_command as hook


def print_usage():
    """Print usage information"""
    print("DiPeO CLI Tool\n")
    print("Usage: dipeo <command> [options]\n")
    print("Commands:")
    print("  run <file> [options]       - 🚀 Run diagram")
    print("    --local                 - Run locally without server (limited features)")
    print("    --monitor               - Open browser monitor before execution")
    print("    --mode=headless         - Run without browser")
    print("    --debug                 - Enable debug mode")
    print("    --keep-server           - Keep server running after debug execution")
    print("    --timeout=<seconds>     - Set inactivity timeout (default: 300)")
    print("  monitor                    - Open browser monitoring page")
    print("  convert <input> <output>   - Convert between JSON/YAML formats")
    print("  stats <file>               - Show diagram statistics")
    print("  hook <subcommand>          - Manage execution hooks")
    print("\nExamples:")
    print("  dipeo run diagram.json")
    print("  dipeo run diagram.yaml --debug --timeout=60")
    print("  dipeo convert diagram.json diagram.yaml")
    print("  dipeo stats diagram.json")


def main():
    """Main entry point"""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    try:
        if command == "run":
            asyncio.run(run(args))
        elif command == "monitor":
            monitor(args)
        elif command == "convert":
            asyncio.run(convert(args))
        elif command == "stats":
            stats(args)
        elif command == "hook":
            hook(args)
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if "--debug" in sys.argv:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
