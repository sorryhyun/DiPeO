"""Command-line argument parser for DiPeO CLI."""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI commands."""
    parser = argparse.ArgumentParser(description="DiPeO - Unified Interface")
    parser.add_argument("--server", action="store_true", help="Run as server (default)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    _add_ask_command(subparsers)
    _add_run_command(subparsers)
    _add_convert_command(subparsers)
    _add_export_command(subparsers)
    _add_stats_command(subparsers)
    _add_monitor_command(subparsers)
    _add_metrics_command(subparsers)
    _add_integrations_command(subparsers)
    _add_dipeocc_command(subparsers)
    _add_compile_command(subparsers)
    _add_list_command(subparsers)
    _add_results_command(subparsers)

    return parser


def _add_ask_command(subparsers):
    """Add 'ask' subcommand."""
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


def _add_run_command(subparsers):
    """Add 'run' subcommand."""
    run_parser = subparsers.add_parser("run", help="Execute a diagram")
    run_parser.add_argument("diagram", help="Path to diagram file or diagram name")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    run_parser.add_argument("--timing", action="store_true", help="Enable timing collection + logs")
    run_parser.add_argument("--timeout", type=int, default=300, help="Execution timeout in seconds")
    run_parser.add_argument("--simple", action="store_true", help="Use simple text display")
    run_parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive user input (user_response nodes return empty)",
    )
    run_parser.add_argument(
        "--background",
        action="store_true",
        help="Run execution in background and return session_id immediately",
    )

    input_group = run_parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--inputs", type=str, help="Path to JSON file containing input variables"
    )
    input_group.add_argument(
        "--input-data", type=str, help="Inline JSON string with input variables"
    )

    format_group = run_parser.add_mutually_exclusive_group()
    format_group.add_argument("--light", action="store_true", help="Use light format (YAML)")
    format_group.add_argument("--native", action="store_true", help="Use native format (JSON)")
    format_group.add_argument("--readable", action="store_true", help="Use readable format (YAML)")


def _add_convert_command(subparsers):
    """Add 'convert' subcommand."""
    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("output", help="Output file")
    convert_parser.add_argument(
        "--from-format", choices=["native", "light", "readable"], help="Source format"
    )
    convert_parser.add_argument(
        "--to-format", choices=["native", "light", "readable"], help="Target format"
    )


def _add_export_command(subparsers):
    """Add 'export' subcommand."""
    export_parser = subparsers.add_parser("export", help="Export diagram to Python script")
    export_parser.add_argument("diagram", help="Path to diagram file")
    export_parser.add_argument("output", help="Output Python file path")

    export_format_group = export_parser.add_mutually_exclusive_group()
    export_format_group.add_argument(
        "--light", action="store_true", help="Input is light format (YAML)"
    )
    export_format_group.add_argument(
        "--native", action="store_true", help="Input is native format (JSON)"
    )
    export_format_group.add_argument(
        "--readable", action="store_true", help="Input is readable format (YAML)"
    )


def _add_stats_command(subparsers):
    """Add 'stats' subcommand."""
    stats_parser = subparsers.add_parser("stats", help="Show diagram statistics")
    stats_parser.add_argument("diagram", help="Path to diagram file")


def _add_monitor_command(subparsers):
    """Add 'monitor' subcommand."""
    monitor_parser = subparsers.add_parser("monitor", help="Open browser monitor")
    monitor_parser.add_argument("diagram", nargs="?", help="Diagram name")


def _add_metrics_command(subparsers):
    """Add 'metrics' subcommand."""
    metrics_parser = subparsers.add_parser("metrics", help="Display execution metrics")
    metrics_parser.add_argument("execution_id", nargs="?", help="Execution ID to show metrics for")
    metrics_parser.add_argument(
        "--latest", action="store_true", help="Show latest execution metrics"
    )
    metrics_parser.add_argument(
        "--diagram", type=str, help="Show metrics history for specific diagram"
    )
    metrics_parser.add_argument(
        "--breakdown", action="store_true", help="Show detailed phase breakdown"
    )
    metrics_parser.add_argument(
        "--bottlenecks", action="store_true", help="Show only bottleneck analysis"
    )
    metrics_parser.add_argument(
        "--optimizations", action="store_true", help="Show optimization suggestions"
    )
    metrics_parser.add_argument("--json", action="store_true", help="Output as JSON")


def _add_integrations_command(subparsers):
    """Add 'integrations' subcommand."""
    integrations_parser = subparsers.add_parser("integrations", help="Manage API integrations")
    integrations_subparsers = integrations_parser.add_subparsers(
        dest="integrations_action", help="Integration commands"
    )

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


def _add_dipeocc_command(subparsers):
    """Add 'dipeocc' subcommand."""
    dipeocc_parser = subparsers.add_parser(
        "dipeocc", help="Convert Claude Code sessions to DiPeO diagrams"
    )
    dipeocc_parser.add_argument(
        "--project",
        type=str,
        help="Claude Code project directory name (e.g., -home-soryhyun-DiPeO)",
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


def _add_compile_command(subparsers):
    """Add 'compile' subcommand."""
    compile_parser = subparsers.add_parser("compile", help="Validate and compile diagram")
    compile_parser.add_argument(
        "diagram", nargs="?", help="Path to diagram file or diagram name (optional with --stdin)"
    )
    compile_parser.add_argument("--check-only", action="store_true", help="Only validate structure")
    compile_parser.add_argument("--json", action="store_true", help="Output as JSON")
    compile_parser.add_argument(
        "--stdin", action="store_true", help="Read diagram content from stdin"
    )
    compile_parser.add_argument(
        "--push-as",
        dest="push_as",
        type=str,
        help="Push compiled diagram to MCP directory with specified filename (works with --stdin)",
    )
    compile_parser.add_argument(
        "--target-dir",
        dest="target_dir",
        type=str,
        help="Target directory for --push-as (default: projects/mcp-diagrams/)",
    )

    compile_format_group = compile_parser.add_mutually_exclusive_group()
    compile_format_group.add_argument(
        "--light", action="store_true", help="Use light format (YAML)"
    )
    compile_format_group.add_argument(
        "--native", action="store_true", help="Use native format (JSON)"
    )
    compile_format_group.add_argument(
        "--readable", action="store_true", help="Use readable format (YAML)"
    )


def _add_list_command(subparsers):
    """Add 'list' subcommand."""
    list_parser = subparsers.add_parser(
        "list", help="List available diagrams in projects/ and examples/simple_diagrams/"
    )
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument(
        "--format",
        type=str,
        choices=["light", "native", "readable"],
        help="Filter by diagram format",
    )


def _add_results_command(subparsers):
    """Add 'results' subcommand."""
    results_parser = subparsers.add_parser(
        "results", help="Query execution status and results by session_id"
    )
    results_parser.add_argument(
        "session_id", help="Execution/session ID (format: exec_[32-char-hex])"
    )
