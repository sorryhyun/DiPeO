"""Claude Code session command for converting JSONL sessions to DiPeO diagrams."""

import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.domain.diagram.cc_translate import ClaudeCodeTranslator
from dipeo.infrastructure.claude_code.session_parser import (
    ClaudeCodeSession,
    find_session_files,
    parse_session_file,
)


class ClaudeCodeCommand:
    """Command for converting Claude Code sessions to DiPeO diagrams."""

    def __init__(self, server_manager=None):
        """Initialize the command."""
        self.server_manager = server_manager
        self.base_dir = Path.home() / ".claude" / "projects" / "-home-soryhyun-DiPeO"
        self.output_base = Path("projects/claude_code")
        self.translator = ClaudeCodeTranslator()

    def execute(self, action: str, **kwargs) -> bool:
        """Execute the Claude Code command based on action."""
        if action == "list":
            return self._list_sessions(kwargs.get("limit", 50))
        elif action == "convert":
            return self._convert_session(
                session_id=kwargs.get("session_id"),
                latest=kwargs.get("latest", False),
                output_dir=kwargs.get("output_dir"),
                format_type=kwargs.get("format", "light"),
                auto_execute=kwargs.get("auto_execute", False),
                merge_reads=kwargs.get("merge_reads", False),
                simplify=kwargs.get("simplify", False),
            )
        elif action == "watch":
            return self._watch_sessions(
                interval=kwargs.get("interval", 30),
                auto_execute=kwargs.get("auto_execute", False),
            )
        elif action == "stats":
            return self._show_stats(kwargs.get("session_id"))
        else:
            print(f"Unknown action: {action}")
            return False

    def _list_sessions(self, limit: int) -> bool:
        """List recent Claude Code sessions."""
        print(f"📋 Listing recent Claude Code sessions (limit: {limit})")
        print(f"   Directory: {self.base_dir}\n")

        session_files = find_session_files(self.base_dir, limit=limit)

        if not session_files:
            print("No session files found.")
            return True

        print(f"Found {len(session_files)} session(s):\n")
        print("-" * 80)

        for idx, session_file in enumerate(session_files, 1):
            try:
                # Parse basic info from the session
                session = parse_session_file(session_file)
                stats = session.get_summary_stats()

                # Format timestamps
                mod_time = datetime.fromtimestamp(session_file.stat().st_mtime)
                duration = stats.get("duration_human", "unknown")

                print(f"{idx:3}. Session: {session_file.stem}")
                print(f"     Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     Duration: {duration}")
                print(f"     Events: {stats['total_events']} total")
                print(
                    f"             ({stats['user_messages']} user, {stats['assistant_messages']} assistant)"
                )

                # Show tool usage summary
                tool_usage = stats.get("tool_usage", {})
                if tool_usage:
                    tools_summary = ", ".join(
                        f"{tool}:{count}" for tool, count in tool_usage.items()
                    )
                    print(f"     Tools: {tools_summary}")

                print(f"     File: {session_file.name}")
                print("-" * 80)

            except Exception as e:
                print(f"{idx:3}. Error parsing {session_file.name}: {e}")
                print("-" * 80)

        print(f"\n✅ Successfully listed {len(session_files)} session(s)!")
        return True

    def _convert_session(
        self,
        session_id: Optional[str] = None,
        latest: Optional[int | bool] = False,
        output_dir: Optional[str] = None,
        format_type: str = "light",
        auto_execute: bool = False,
        merge_reads: bool = False,
        simplify: bool = False,
    ) -> bool:
        """Convert Claude Code session(s) to DiPeO diagram(s)."""
        sessions_to_convert = []

        # Determine which session(s) to convert
        if latest:
            # latest can be True (convert 1) or an integer (convert N)
            num_sessions = 1 if latest is True else latest
            session_files = find_session_files(self.base_dir, limit=num_sessions)
            if not session_files:
                print("No session files found.")
                return False

            if num_sessions == 1:
                print(f"Converting latest session: {session_files[0].stem}")
            else:
                print(f"Converting {len(session_files)} most recent sessions...")

            sessions_to_convert = [(f.stem, f) for f in session_files]
        elif session_id:
            # Look for the session file
            session_file = self.base_dir / f"{session_id}.jsonl"
            if not session_file.exists():
                # Try with "session-" prefix
                session_file = self.base_dir / f"session-{session_id}.jsonl"
                if not session_file.exists():
                    print(f"Session file not found: {session_id}")
                    return False
            sessions_to_convert = [(session_id, session_file)]
        else:
            print("Please provide either --session-id or --latest flag")
            return False

        # Convert each session
        successful_conversions = 0
        failed_conversions = 0

        for idx, (session_id, session_file) in enumerate(sessions_to_convert, 1):
            if len(sessions_to_convert) > 1:
                print(
                    f"\n[{idx}/{len(sessions_to_convert)}] Converting session: {session_file.name}"
                )
            else:
                print(f"📊 Converting session: {session_file.name}")

            try:
                # Parse the session
                session = parse_session_file(session_file)
                stats = session.get_summary_stats()

                print(f"   Events: {stats['total_events']}")
                print(f"   Duration: {stats.get('duration_human', 'unknown')}")
                print(f"   Tools used: {len(stats.get('tool_usage', {}))}")

                # Translate to diagram
                print("\n🔄 Translating to DiPeO diagram...")
                diagram_data = self.translator.translate(session)

                # Apply optimizations if requested
                if merge_reads:
                    diagram_data = self._merge_consecutive_reads(diagram_data)
                if simplify:
                    diagram_data = self._simplify_diagram(diagram_data)

                # Determine output path
                output_dir_path = Path(output_dir) if output_dir else self.output_base
                output_dir_path = output_dir_path / "sessions" / session_id
                output_dir_path.mkdir(parents=True, exist_ok=True)

                # Save diagram based on format
                if format_type == "light":
                    output_file = output_dir_path / "diagram.light.yaml"

                    # Create a custom YAML dumper with better formatting
                    class CustomYAMLDumper(yaml.SafeDumper):
                        pass

                    # Custom representer for multi-line strings using literal style
                    def str_representer(dumper, data):
                        # Check if this is a multi-line string (has actual newlines)
                        if "\n" in data:
                            # Use literal style for multi-line strings
                            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
                        # Check for diff patterns even in single-line strings
                        elif (
                            data.startswith("---") or data.startswith("+++") or data.startswith("#")
                        ):
                            # Might be the start of a diff, use literal style
                            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
                        # Use default style for single-line strings
                        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

                    # Custom representer for compact position dicts
                    def dict_representer(dumper, data):
                        # Use flow style for simple position/vec2 dicts
                        if isinstance(data, dict) and len(data) == 2:
                            keys = set(data.keys())
                            if keys == {"x", "y"}:
                                # Use flow style for position objects
                                return dumper.represent_mapping(
                                    "tag:yaml.org,2002:map", data, flow_style=True
                                )
                        # Use default block style for other dicts
                        return dumper.represent_mapping("tag:yaml.org,2002:map", data)

                    # Register representers with our custom dumper
                    CustomYAMLDumper.add_representer(str, str_representer)
                    CustomYAMLDumper.add_representer(dict, dict_representer)

                    with open(output_file, "w", encoding="utf-8") as f:
                        yaml.dump(
                            diagram_data,
                            f,
                            Dumper=CustomYAMLDumper,
                            default_flow_style=False,
                            sort_keys=False,
                            allow_unicode=True,
                            width=4096,  # Wider lines for better readability
                        )
                elif format_type == "native":
                    output_file = output_dir_path / "diagram.native.json"
                    with open(output_file, "w") as f:
                        json.dump(diagram_data, f, indent=2)
                else:
                    print(f"Unsupported format: {format_type}")
                    failed_conversions += 1
                    continue

                print(f"✅ Diagram saved to: {output_file}")

                # Copy original session JSONL file to the session folder
                session_jsonl_dest = output_dir_path / "session.jsonl"
                shutil.copy2(session_file, session_jsonl_dest)
                print(f"📄 Session JSONL saved to: {session_jsonl_dest}")

                # Save metadata
                metadata_file = output_dir_path / "metadata.json"
                metadata = {
                    "session_id": session_id,
                    "converted_at": datetime.now().isoformat(),
                    "source_file": str(session_file),
                    "stats": stats,
                    "format": format_type,
                    "optimizations": {
                        "merge_reads": merge_reads,
                        "simplify": simplify,
                    },
                }
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                # Create/update symlink to latest (only for single conversion)
                if len(sessions_to_convert) == 1:
                    latest_link = self.output_base / f"latest.{format_type}.yaml"
                    if latest_link.exists() or latest_link.is_symlink():
                        latest_link.unlink()
                    latest_link.symlink_to(output_file.relative_to(self.output_base.parent))
                    print(f"🔗 Latest symlink updated: {latest_link}")

                print(f"📊 Metadata saved to: {metadata_file}")

                # Auto-execute if requested (only for single conversion)
                if auto_execute and self.server_manager and len(sessions_to_convert) == 1:
                    print("\n🚀 Auto-executing generated diagram...")
                    self._execute_diagram(str(output_file))

                successful_conversions += 1
                if len(sessions_to_convert) == 1:
                    print("\n✨ Success! Claude Code session converted to DiPeO diagram.")

            except Exception as e:
                print(f"❌ Conversion failed: {e}")
                import traceback

                traceback.print_exc()
                failed_conversions += 1

        # Report results for multiple conversions
        if len(sessions_to_convert) > 1:
            print(f"\n{'='*60}")
            print(f"✅ Successfully converted: {successful_conversions} session(s)")
            if failed_conversions > 0:
                print(f"❌ Failed: {failed_conversions} session(s)")
            print(f"{'='*60}\n")

        return successful_conversions > 0

    def _watch_sessions(self, interval: int = 30, auto_execute: bool = False) -> bool:
        """Watch for new sessions and convert them automatically."""
        print(f"👀 Watching for new Claude Code sessions (interval: {interval}s)")
        print(f"   Directory: {self.base_dir}")
        print("   Press Ctrl+C to stop\n")

        processed_sessions = set()

        # Get initial list of sessions
        initial_sessions = find_session_files(self.base_dir, limit=100)
        for session_file in initial_sessions:
            processed_sessions.add(session_file.stem)

        print(f"✅ Found {len(processed_sessions)} existing sessions")
        print("⏳ Waiting for new sessions...")

        try:
            while True:
                time.sleep(interval)

                # Check for new sessions
                current_sessions = find_session_files(self.base_dir, limit=10)
                for session_file in current_sessions:
                    session_id = session_file.stem
                    if session_id not in processed_sessions:
                        print(f"\n🆕 New session detected: {session_id}")
                        processed_sessions.add(session_id)

                        # Convert the new session
                        success = self._convert_session(
                            session_id=session_id,
                            auto_execute=auto_execute,
                        )
                        if success:
                            print(f"✅ Successfully converted: {session_id}")
                        else:
                            print(f"❌ Failed to convert: {session_id}")

        except KeyboardInterrupt:
            print("\n\n👋 Stopping session watcher")
            print("✅ Watch mode ended successfully!")
            return True

    def _show_stats(self, session_id: str) -> bool:
        """Show detailed statistics for a session."""
        # Find the session file
        session_file = self.base_dir / f"{session_id}.jsonl"
        if not session_file.exists():
            session_file = self.base_dir / f"session-{session_id}.jsonl"
            if not session_file.exists():
                print(f"Session file not found: {session_id}")
                return False

        print(f"📊 Session Statistics: {session_id}\n")

        try:
            session = parse_session_file(session_file)
            stats = session.get_summary_stats()

            # Basic stats
            print("═" * 60)
            print("OVERVIEW")
            print("═" * 60)
            print(f"Session ID:        {stats['session_id']}")
            print(f"Total Events:      {stats['total_events']}")
            print(f"User Messages:     {stats['user_messages']}")
            print(f"Assistant Messages: {stats['assistant_messages']}")
            print(f"Duration:          {stats.get('duration_human', 'N/A')}")

            # Tool usage
            print("\n" + "═" * 60)
            print("TOOL USAGE")
            print("═" * 60)
            tool_usage = stats.get("tool_usage", {})
            if tool_usage:
                for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True):
                    print(f"{tool:20} {count:5} calls")
            else:
                print("No tools used")

            # File operations
            print("\n" + "═" * 60)
            print("FILE OPERATIONS")
            print("═" * 60)
            file_ops = session.metadata.file_operations
            if file_ops:
                for op_type, files in file_ops.items():
                    print(f"\n{op_type} ({len(files)} files):")
                    for file_path in sorted(set(files))[:10]:  # Show first 10 unique files
                        print(f"  - {file_path}")
                    if len(set(files)) > 10:
                        print(f"  ... and {len(set(files)) - 10} more")
            else:
                print("No file operations")

            # Bash commands
            print("\n" + "═" * 60)
            print("BASH COMMANDS")
            print("═" * 60)
            bash_commands = session.get_bash_commands()
            if bash_commands:
                print(f"Total commands: {len(bash_commands)}")
                print("\nRecent commands:")
                for cmd in bash_commands[-5:]:  # Show last 5 commands
                    cmd_preview = cmd[:80] + "..." if len(cmd) > 80 else cmd
                    print(f"  $ {cmd_preview}")
            else:
                print("No bash commands executed")

            print("\n" + "═" * 60)
            print("\n✅ Session statistics generated successfully!")

            return True

        except Exception as e:
            print(f"Error analyzing session: {e}")
            return False

    def _merge_consecutive_reads(self, diagram: dict[str, Any]) -> dict[str, Any]:
        """Merge consecutive file read operations into single nodes."""
        # TODO: Implement merge logic for consecutive read operations
        # For now, return the diagram as-is
        return diagram

    def _simplify_diagram(self, diagram: dict[str, Any]) -> dict[str, Any]:
        """Simplify the diagram by removing intermediate tool results."""
        # TODO: Implement simplification logic
        # For now, return the diagram as-is
        return diagram

    def _execute_diagram(self, diagram_path: str) -> bool:
        """Execute the generated diagram using the server."""
        if not self.server_manager:
            print("Server manager not available for execution")
            return False

        try:
            from dipeo_cli.commands.run_command import RunCommand

            run_command = RunCommand(self.server_manager)

            # Determine format from file extension
            format_type = "light" if diagram_path.endswith(".light.yaml") else "native"

            return run_command.execute(
                diagram=diagram_path,
                debug=False,
                no_browser=True,
                timeout=300,
                format_type=format_type,
            )
        except Exception as e:
            print(f"Failed to execute diagram: {e}")
            return False
