#!/usr/bin/env python3
"""Unified entry point for DiPeO - can run as server or CLI."""

import asyncio
import io
import os
import sys
import warnings

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"


def main():
    """Main entry point."""
    warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)
    warnings.filterwarnings(
        "ignore", message="Field name.*shadows an attribute", category=UserWarning
    )

    from .dispatcher import run_cli_command
    from .parser import create_parser

    parser = create_parser()
    args = parser.parse_args()

    if not args.command or args.server:
        _run_server(args)
    else:
        _run_cli(args)


def _run_server(args):
    """Run as server."""
    import uvicorn

    from dipeo.infrastructure.logging_config import setup_logging

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    setup_logging(
        component="server",
        log_level=log_level,
        log_to_file=True,
        log_dir=".dipeo/logs",
        console_output=True,
    )

    from server.main import app

    uvicorn.run(
        app,
        host=args.host if hasattr(args, "host") else "0.0.0.0",
        port=args.port if hasattr(args, "port") else 8000,
        log_level=log_level.lower(),
    )


def _run_cli(args):
    """Run as CLI ."""
    from .dispatcher import run_cli_command

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
    sys.argv = [sys.argv[0], "dipeocc"] + sys.argv[1:]
    main()


if __name__ == "__main__":
    main()
