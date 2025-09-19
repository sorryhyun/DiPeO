"""Claude Code session command for converting JSONL sessions to DiPeO diagrams."""

import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.domain.cc_translate import PhaseCoordinator
from dipeo.domain.cc_translate.post_processing import PipelineConfig, ProcessingPreset
from dipeo.infrastructure.cc_translate import (
    SessionAdapter,
    SessionSerializer,
    extract_session_timestamp,
    find_session_files,
    format_timestamp_for_directory,
    parse_session_file,
)


class ClaudeCodeCommand:
    """Command for converting Claude Code sessions to DiPeO diagrams."""

    def __init__(self, server_manager=None):
        """Initialize the command."""
        self.server_manager = server_manager
        self.base_dir = Path.home() / ".claude" / "projects" / "-home-soryhyun-DiPeO"
        self.output_base = Path("projects/claude_code")
        self.coordinator = PhaseCoordinator()
        self.session_serializer = SessionSerializer()

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
            )
        elif action == "watch":
            return self._watch_sessions(
                interval=kwargs.get("interval", 30),
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
    ) -> bool:
        """Convert Claude Code session(s) to DiPeO diagram(s)."""
        # Determine which session(s) to convert
        sessions_to_convert = []

        if latest:
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
            session_file = self.base_dir / f"{session_id}.jsonl"
            if not session_file.exists():
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

        for idx, (current_session_id, session_file) in enumerate(sessions_to_convert, 1):
            if len(sessions_to_convert) > 1:
                print(
                    f"\n[{idx}/{len(sessions_to_convert)}] Converting session: {session_file.name}"
                )
            else:
                print(f"📊 Converting session: {session_file.name}")

            try:
                # Parse the session
                session = self._parse_session_file(session_file)

                print("\n🔄 Translating to DiPeO diagram...")

                # Generate both original and optimized diagrams (always)
                original_diagram_data = self._generate_original_diagram(session)
                optimized_diagram_data = self._generate_optimized_diagram(session)

                # Setup output directory
                output_dir_path = self._setup_output_directory(
                    current_session_id, output_dir, session_file
                )

                # Save both diagrams with new naming convention
                file_extension = "yaml" if format_type == "light" else "json"

                # Save original diagram as 'diagram.light.yaml'
                original_file = output_dir_path / f"diagram.{format_type}.{file_extension}"
                self._save_diagram(original_diagram_data, original_file, format_type)
                print(f"📄 Original diagram saved to: {original_file}")

                # Save optimized diagram as 'optimized.light.yaml'
                optimized_file = output_dir_path / f"optimized.{format_type}.{file_extension}"
                self._save_diagram(optimized_diagram_data, optimized_file, format_type)
                print(f"✅ Optimized diagram saved to: {optimized_file}")

                # Create diagrams info for metadata
                diagrams_info = {
                    "original": {
                        "file": f"diagram.{format_type}.{file_extension}",
                        "type": "original",
                        "statistics": self._get_diagram_stats(original_diagram_data),
                    },
                    "optimized": {
                        "file": f"optimized.{format_type}.{file_extension}",
                        "type": "optimized",
                        "statistics": self._get_diagram_stats(optimized_diagram_data),
                    },
                }

                # Create metadata
                metadata = self._create_session_metadata(
                    current_session_id, session, diagrams_info, format_type, output_dir_path.name
                )

                metadata_file = output_dir_path / "metadata.json"
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)
                print(f"📊 Metadata saved to: {metadata_file}")

                # Create latest symlink for single conversions (point to optimized version)
                if len(sessions_to_convert) == 1:
                    self._create_latest_symlink(optimized_file, format_type)

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

    def _get_diagram_stats(self, diagram_data: dict[str, Any]) -> dict[str, Any]:
        """Extract basic statistics from a diagram."""
        nodes = diagram_data.get("nodes", [])
        connections = diagram_data.get("connections", [])
        return {
            "node_count": len(nodes),
            "connection_count": len(connections),
            "node_types": list(set(node.get("type", "unknown") for node in nodes)),
        }

    def _parse_session_file(self, session_file: Path) -> Any:
        """Parse and validate a Claude Code session file."""
        session = parse_session_file(session_file)
        stats = session.get_summary_stats()

        print(f"   Events: {stats['total_events']}")
        print(f"   Duration: {stats.get('duration_human', 'unknown')}")
        print(f"   Tools used: {len(stats.get('tool_usage', {}))}")

        return session

    def _generate_optimized_diagram(self, session: Any) -> dict[str, Any]:
        """Generate optimized diagram using standard post-processing."""
        print("   ⚡ Generating optimized diagram...")

        # Adapt infrastructure session to domain port
        session_adapter = SessionAdapter(session)

        # Use standard preset for optimization
        config = PipelineConfig.from_preset(ProcessingPreset.STANDARD)
        diagram, _ = self.coordinator.translate(
            session_adapter, post_process=True, processing_config=config
        )
        return diagram

    def _generate_original_diagram(self, session: Any) -> dict[str, Any]:
        """Generate original diagram with minimal post-processing."""
        print("   📄 Generating original diagram...")

        # Adapt infrastructure session to domain port
        session_adapter = SessionAdapter(session)

        # Use minimal processing for original
        diagram, _ = self.coordinator.translate(session_adapter)
        return diagram

    def _save_diagram(
        self, diagram_data: dict[str, Any], file_path: Path, format_type: str
    ) -> None:
        """Save diagram to file in the specified format."""
        if format_type == "light":
            self._save_light_diagram(diagram_data, file_path)
        elif format_type == "native":
            with open(file_path, "w") as f:
                json.dump(diagram_data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _save_light_diagram(self, diagram_data: dict[str, Any], file_path: Path) -> None:
        """Save diagram in light format with custom YAML formatting."""

        class CustomYAMLDumper(yaml.SafeDumper):
            pass

        def str_representer(dumper, data):
            if "\n" in data or (
                data.startswith("---") or data.startswith("+++") or data.startswith("#")
            ):
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        def dict_representer(dumper, data):
            if isinstance(data, dict):
                keys = set(data.keys())
                # Handle position dictionaries
                if len(data) == 2 and keys == {"x", "y"}:
                    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)
                # Handle connection dictionaries
                if ("from" in keys and "to" in keys and "content_type" in keys) and keys <= {
                    "from",
                    "to",
                    "content_type",
                    "label",
                }:
                    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)
            return dumper.represent_mapping("tag:yaml.org,2002:map", data)

        CustomYAMLDumper.add_representer(str, str_representer)
        CustomYAMLDumper.add_representer(dict, dict_representer)

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(
                diagram_data,
                f,
                Dumper=CustomYAMLDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=4096,
            )

    def _setup_output_directory(
        self, session_id: str, output_dir: Optional[str], session_file: Path
    ) -> Path:
        """Setup output directory using timestamp-based naming and copy session files."""
        output_dir_path = Path(output_dir) if output_dir else self.output_base

        # Extract timestamp from session file for directory naming
        timestamp = extract_session_timestamp(session_file)
        if timestamp:
            dir_name = format_timestamp_for_directory(timestamp)
        else:
            # Fallback to session_id if timestamp extraction fails
            dir_name = session_id
            print(f"⚠️  Warning: Could not extract timestamp, using session ID: {session_id}")

        output_dir_path = output_dir_path / "sessions" / dir_name
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Copy original session JSONL file as 'original_session.jsonl' (exact copy)
        original_session_dest = output_dir_path / "original_session.jsonl"
        shutil.copy2(session_file, original_session_dest)
        print(f"📄 Original session JSONL saved to: {original_session_dest}")

        # Create pruned version as 'session.jsonl'
        session_jsonl_dest = output_dir_path / "session.jsonl"

        # Parse the session for pruning
        session = parse_session_file(session_file)

        # Create a SessionAdapter to convert to domain model
        session_adapter = SessionAdapter(session)

        # Preprocess the session to prune unnecessary fields
        preprocessed_data = self.coordinator.preprocess_only(session_adapter)

        # Use SessionSerializer to convert preprocessed session to JSONL
        bytes_written = self.session_serializer.to_jsonl_file(
            preprocessed_data.session, session_jsonl_dest
        )

        # Calculate size difference for display
        original_size = session_file.stat().st_size
        size_reduction_pct = (
            ((original_size - bytes_written) / original_size * 100) if original_size > 0 else 0
        )

        print(f"📄 Preprocessed session JSONL saved to: {session_jsonl_dest}")
        if size_reduction_pct > 0:
            print(
                f"   ↳ Size reduction: {size_reduction_pct:.1f}% "
                f"({original_size:,} → {bytes_written:,} bytes)"
            )

        return output_dir_path

    def _create_session_metadata(
        self,
        session_id: str,
        session: Any,
        diagrams_info: dict[str, Any],
        format_type: str,
        directory_name: str,
    ) -> dict[str, Any]:
        """Generate essential session metadata."""
        stats = session.get_summary_stats()

        metadata = {
            "session_id": session_id,
            "directory_name": directory_name,  # Timestamp-based directory name
            "converted_at": datetime.now().isoformat(),
            "stats": stats,
            "format": format_type,
            "diagrams": diagrams_info,
            "file_structure": {
                "original_session": "original_session.jsonl",
                "processed_session": "session.jsonl",
                "original_diagram": f"diagram.{format_type}.yaml"
                if format_type == "light"
                else f"diagram.{format_type}.json",
                "optimized_diagram": f"optimized.{format_type}.yaml"
                if format_type == "light"
                else f"optimized.{format_type}.json",
                "metadata": "metadata.json",
            },
            "options": {
                "save_original": True,  # Always save both versions now
                "timestamp_based_naming": True,
            },
        }

        return metadata

    def _create_latest_symlink(self, diagram_file: Path, format_type: str) -> None:
        """Create symlink to latest converted diagram."""
        latest_link = self.output_base / f"latest.{format_type}.yaml"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(diagram_file.relative_to(self.output_base.parent))
        print(f"🔗 Latest symlink updated: {latest_link}")

    def _watch_sessions(self, interval: int = 30) -> bool:
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
                        success = self._convert_session(session_id=session_id)
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
