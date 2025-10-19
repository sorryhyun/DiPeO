"""Command dispatcher for DiPeO CLI."""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import uuid
import webbrowser

from dipeo.application.bootstrap import init_resources, shutdown_resources
from dipeo.infrastructure.logging_config import setup_logging
from dipeo_server.app_context import create_server_container
from dipeo_server.cli import CLIRunner
from dipeo_server.cli.core import ServerManager


async def run_cli_command(args: argparse.Namespace) -> bool:
    """Run CLI command using direct service calls."""
    debug = getattr(args, "debug", False)
    timing = getattr(args, "timing", False)

    if timing:
        os.environ["DIPEO_TIMING_ENABLED"] = "true"

    if debug or timing:
        log_level = "DEBUG"
    else:
        log_level = os.environ.get("DIPEO_LOG_LEVEL", "INFO")

    file_mode = "w" if args.command == "run" else "a"

    setup_logging(
        component="cli",
        log_level=log_level,
        log_to_file=True,
        console_output=debug or timing,
        timing_only=timing and not debug,
        file_mode=file_mode,
    )

    server_manager = None
    if (debug or timing) and args.command == "run":
        print("🚀 Starting background server for monitoring...")
        server_manager = ServerManager()
        if await server_manager.start():
            print("✅ Monitor available at http://localhost:3000/?monitor=true")
        else:
            print("⚠️  Server failed to start, monitor unavailable")

    container = await create_server_container()
    await init_resources(container)

    try:
        cli = CLIRunner(container)

        if args.command == "ask":
            return await cli.ask_diagram(
                request=args.to,
                and_run=args.and_run,
                debug=args.debug,
                timeout=args.timeout,
                run_timeout=args.run_timeout,
            )

        elif args.command == "run":
            if hasattr(args, "background") and args.background:
                return _handle_background_execution(args)

            format_type = _get_format_type(args)
            input_variables = _get_input_variables(args)
            execution_id = os.environ.get("DIPEO_EXECUTION_ID")

            return await cli.run_diagram(
                diagram=args.diagram,
                debug=args.debug,
                timeout=args.timeout,
                format_type=format_type,
                input_variables=input_variables,
                use_unified=True,
                simple=hasattr(args, "simple") and args.simple,
                interactive=not (hasattr(args, "no_interactive") and args.no_interactive),
                execution_id=execution_id,
            )

        elif args.command == "convert":
            return await cli.convert_diagram(
                input_path=args.input,
                output_path=args.output,
                from_format=getattr(args, "from_format", None),
                to_format=getattr(args, "to_format", None),
            )

        elif args.command == "export":
            format_type = _get_format_type(args)
            return await cli.export_diagram(
                diagram_path=args.diagram,
                output_path=args.output,
                format_type=format_type,
            )

        elif args.command == "stats":
            return await cli.show_stats(args.diagram)

        elif args.command == "monitor":
            url = "http://localhost:3000/?monitor=true"
            if args.diagram:
                url += f"&diagram={args.diagram}"
            webbrowser.open(url)
            return True

        elif args.command == "metrics":
            return await cli.show_metrics(
                execution_id=args.execution_id,
                latest=getattr(args, "latest", False),
                diagram_id=getattr(args, "diagram", None),
                breakdown=getattr(args, "breakdown", False),
                bottlenecks_only=getattr(args, "bottlenecks", False),
                optimizations_only=getattr(args, "optimizations", False),
                output_json=getattr(args, "json", False),
            )

        elif args.command == "integrations":
            action = args.integrations_action
            kwargs = _get_integrations_kwargs(args, action)
            return await cli.manage_integrations(action, **kwargs)

        elif args.command == "dipeocc":
            action = args.dipeocc_action
            kwargs = _get_dipeocc_kwargs(args, action)
            return await cli.manage_claude_code(action, **kwargs)

        elif args.command == "compile":
            format_type = _get_format_type(args)
            return await cli.compile_diagram(
                diagram_path=getattr(args, "diagram", None),
                format_type=format_type,
                check_only=getattr(args, "check_only", False),
                output_json=getattr(args, "json", False),
                use_stdin=getattr(args, "stdin", False),
                push_as=getattr(args, "push_as", None),
                target_dir=getattr(args, "target_dir", None),
            )

        elif args.command == "list":
            return await cli.list_diagrams(
                output_json=getattr(args, "json", False),
                format_filter=getattr(args, "format", None),
            )

        elif args.command == "results":
            return await cli.show_results(session_id=args.session_id)

        else:
            print(f"Unknown command: {args.command}")
            return False

    finally:
        await shutdown_resources(container)

        if server_manager:
            await asyncio.sleep(0.5)
            await server_manager.stop()


def _handle_background_execution(args: argparse.Namespace) -> bool:
    """Handle background execution by spawning subprocess."""
    execution_id = f"exec_{uuid.uuid4().hex}"

    cmd_args = [
        sys.executable,
        "-m",
        "dipeo_server.cli.entry_point",
        "run",
        args.diagram,
    ]

    if args.debug:
        cmd_args.append("--debug")
    if args.timing:
        cmd_args.append("--timing")
    if args.timeout != 300:
        cmd_args.extend(["--timeout", str(args.timeout)])
    if hasattr(args, "simple") and args.simple:
        cmd_args.append("--simple")
    if hasattr(args, "no_interactive") and args.no_interactive:
        cmd_args.append("--no-interactive")

    if hasattr(args, "light") and args.light:
        cmd_args.append("--light")
    elif hasattr(args, "native") and args.native:
        cmd_args.append("--native")
    elif hasattr(args, "readable") and args.readable:
        cmd_args.append("--readable")

    if hasattr(args, "inputs") and args.inputs:
        cmd_args.extend(["--inputs", args.inputs])
    elif hasattr(args, "input_data") and args.input_data:
        cmd_args.extend(["--input-data", args.input_data])

    env = os.environ.copy()
    env["DIPEO_EXECUTION_ID"] = execution_id

    subprocess.Popen(
        cmd_args,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    print(json.dumps({"session_id": execution_id, "status": "started"}))
    return True


def _get_format_type(args: argparse.Namespace) -> str | None:
    """Extract format type from args."""
    if hasattr(args, "light") and args.light:
        return "light"
    elif hasattr(args, "native") and args.native:
        return "native"
    elif hasattr(args, "readable") and args.readable:
        return "readable"
    return None


def _get_input_variables(args: argparse.Namespace) -> dict | None:
    """Extract input variables from args."""
    if hasattr(args, "inputs") and args.inputs:
        with open(args.inputs) as f:
            return json.load(f)
    elif hasattr(args, "input_data") and args.input_data:
        return json.loads(args.input_data)
    return None


def _get_integrations_kwargs(args: argparse.Namespace, action: str) -> dict:
    """Extract kwargs for integrations command."""
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

    return kwargs


def _get_dipeocc_kwargs(args: argparse.Namespace, action: str) -> dict:
    """Extract kwargs for dipeocc command."""
    kwargs = {"project": getattr(args, "project", None)}

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

    return kwargs
