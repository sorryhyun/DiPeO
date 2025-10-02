"""Claude Code session manager for DiPeO CLI integration.

This module provides a high-level interface for managing Claude Code sessions,
including listing, converting, watching, and analyzing sessions.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dipeo.domain.cc_translate import PhaseCoordinator
from dipeo.domain.diagram.strategies.light_strategy import LightYamlStrategy
from dipeo.infrastructure.cc_translate.adapters import SessionAdapter
from dipeo.infrastructure.cc_translate.session_parser import (
    ClaudeCodeSession,
    extract_session_timestamp,
    find_session_files,
    format_timestamp_for_directory,
    parse_session_file,
)
from dipeo.infrastructure.cc_translate.session_serializer import SessionSerializer

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Information about a Claude Code session."""

    id: str
    name: str
    created_at: datetime
    file_path: Path
    event_count: int = 0


class ClaudeCodeManager:
    """Manages Claude Code session conversion and analysis.

    This class provides a high-level interface for working with Claude Code sessions,
    including discovery, conversion to DiPeO diagrams, and session monitoring.
    """

    def __init__(self, session_dir: Optional[Path] = None):
        """Initialize the ClaudeCodeManager.

        Args:
            session_dir: Directory containing Claude Code session files.
                        Defaults to ~/.claude/projects/
        """
        self.session_dir = session_dir or self._discover_session_dir()
        self.coordinator = PhaseCoordinator()
        self.serializer = SessionSerializer()
        self.light_strategy = LightYamlStrategy()

    def _discover_session_dir(self) -> Path:
        """Discover the Claude Code session directory.

        Returns:
            Path to the session directory
        """
        # Check common locations
        default_locations = [
            Path.home() / ".claude" / "projects",
            Path.home() / ".claude" / "sessions",
        ]

        for location in default_locations:
            if location.exists():
                # Look for project-specific subdirectories
                project_dirs = [d for d in location.iterdir() if d.is_dir()]
                if project_dirs:
                    # Return most recently modified project directory
                    project_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    return project_dirs[0]
                return location

        # Default to standard location even if it doesn't exist
        return Path.home() / ".claude" / "projects"

    def _is_valid_session_id(self, session_id: str) -> bool:
        """Validate session ID to prevent path traversal attacks.

        Args:
            session_id: The session ID to validate

        Returns:
            True if the session ID is safe to use in file paths
        """
        # Check for path traversal sequences
        if ".." in session_id or "/" in session_id or "\\" in session_id:
            return False

        # Check for valid characters (alphanumeric, dash, underscore)
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
            return False

        return True

    def list_sessions(self, limit: int = 50) -> list[SessionInfo]:
        """List available Claude Code sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of SessionInfo objects sorted by creation time (newest first)
        """
        if not self.session_dir.exists():
            logger.warning(f"Session directory not found: {self.session_dir}")
            return []

        session_files = find_session_files(self.session_dir, limit=limit)
        sessions = []
        failed_count = 0

        for file_path in session_files:
            try:
                # Parse basic info without full processing
                session_id = file_path.stem
                timestamp = extract_session_timestamp(file_path)

                # Quick parse to get event count
                event_count = 0
                with open(file_path, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            event_count += 1

                sessions.append(
                    SessionInfo(
                        id=session_id,
                        name=file_path.name,
                        created_at=timestamp or datetime.fromtimestamp(file_path.stat().st_mtime),
                        file_path=file_path,
                        event_count=event_count,
                    )
                )
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to parse session info from {file_path}: {e}")
                continue

        # Warn if all sessions failed to parse
        if failed_count > 0 and len(sessions) == 0:
            logger.error(
                f"All {failed_count} session files failed to parse. "
                f"Session directory may contain corrupted files: {self.session_dir}"
            )

        return sessions

    def convert_session(
        self,
        session_id: str,
        output_dir: Optional[str] = None,
        format_type: str = "light",
    ) -> bool:
        """Convert a Claude Code session to a DiPeO diagram.

        Args:
            session_id: ID of the session to convert
            output_dir: Optional output directory (defaults to projects/claude_code/sessions/)
            format_type: Output format type (currently only 'light' supported)

        Returns:
            True if conversion succeeded, False otherwise
        """
        try:
            # Sanitize session_id to prevent path traversal
            if not self._is_valid_session_id(session_id):
                logger.error(
                    f"Invalid session_id: {session_id}. "
                    "Session IDs must not contain path separators or '..' sequences."
                )
                return False

            # Find session file
            session_file = self.session_dir / f"{session_id}.jsonl"
            if not session_file.exists():
                logger.error(f"Session file not found: {session_file}")
                return False

            # Parse session
            logger.info(f"Parsing session: {session_id}")
            session = parse_session_file(session_file)

            # Convert to domain session
            adapter = SessionAdapter(session)
            domain_session = adapter.to_domain_session()

            # Run translation pipeline
            logger.info("Running translation pipeline...")
            diagram, metrics = self.coordinator.translate(
                domain_session,
                post_process=True,  # Enable post-processing for optimization
            )

            if not metrics.success:
                logger.error(f"Translation failed: {', '.join(metrics.errors)}")
                return False

            # Determine output path
            if output_dir:
                output_base = Path(output_dir)
            else:
                # Default to projects/claude_code/sessions/{timestamp}_{session_id}/
                timestamp = extract_session_timestamp(session_file)
                if timestamp:
                    dir_name = format_timestamp_for_directory(timestamp)
                else:
                    dir_name = session_id

                output_base = Path("projects/claude_code/sessions") / dir_name

            output_base.mkdir(parents=True, exist_ok=True)

            # Save diagram
            output_file = output_base / "diagram.light.yaml"
            logger.info(f"Saving diagram to: {output_file}")

            # Convert diagram dict to DomainDiagram, then serialize to light YAML
            from dipeo.diagram_generated import DomainDiagram

            domain_diagram = DomainDiagram.model_validate(diagram)
            yaml_content = self.light_strategy.serialize_from_domain(domain_diagram)
            output_file.write_text(yaml_content, encoding="utf-8")

            # Save metadata
            metadata_file = output_base / "conversion_metadata.json"
            metadata = {
                "session_id": session_id,
                "converted_at": datetime.now().isoformat(),
                "output_format": format_type,
                "metrics": {
                    "total_duration_ms": metrics.total_duration_ms,
                    "phase_durations": {
                        phase.value: duration for phase, duration in metrics.phase_durations.items()
                    },
                    "success": metrics.success,
                    "errors": metrics.errors,
                },
                "diagram_stats": {
                    "node_count": len(diagram.get("nodes", [])),
                    "connection_count": len(diagram.get("connections", [])),
                },
            }

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)

            logger.info(f"✅ Conversion completed successfully")
            logger.info(f"   Duration: {metrics.total_duration_ms:.2f}ms")
            logger.info(f"   Nodes: {len(diagram.get('nodes', []))}")
            logger.info(f"   Output: {output_file}")

            return True

        except Exception as e:
            logger.error(f"Conversion failed: {e}", exc_info=True)
            return False

    async def watch_sessions(
        self,
        interval: int = 30,
        output_dir: Optional[str] = None,
        format_type: str = "light",
    ) -> bool:
        """Watch for new sessions and automatically convert them.

        Args:
            interval: Check interval in seconds
            output_dir: Optional output directory
            format_type: Output format type

        Returns:
            True if watching started successfully
        """
        logger.info(f"Watching {self.session_dir} for new sessions (interval: {interval}s)")
        seen_sessions = set()

        try:
            while True:
                sessions = self.list_sessions(limit=10)
                for session in sessions:
                    if session.id not in seen_sessions:
                        logger.info(f"New session detected: {session.id}")
                        self.convert_session(session.id, output_dir, format_type)
                        seen_sessions.add(session.id)

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Watching stopped by user")
            return True
        except Exception as e:
            logger.error(f"Watch failed: {e}", exc_info=True)
            return False

    async def get_session_stats(self, session_id: str) -> dict:
        """Get detailed statistics about a session.

        Args:
            session_id: ID of the session to analyze

        Returns:
            Dictionary containing session statistics
        """
        try:
            # Sanitize session_id to prevent path traversal
            if not self._is_valid_session_id(session_id):
                return {
                    "error": f"Invalid session_id: {session_id}. "
                    "Session IDs must not contain path separators or '..' sequences."
                }

            # Find session file
            session_file = self.session_dir / f"{session_id}.jsonl"
            if not session_file.exists():
                return {"error": f"Session file not found: {session_file}"}

            # Parse session
            session = parse_session_file(session_file)

            # Extract statistics
            stats = {
                "session_id": session_id,
                "event_count": len(session.events),
                "conversation_turn_count": len(session.conversation_turns),
                "metadata": {
                    "start_time": session.metadata.start_time.isoformat()
                    if session.metadata.start_time
                    else None,
                    "end_time": session.metadata.end_time.isoformat()
                    if session.metadata.end_time
                    else None,
                    "tool_usage": session.metadata.tool_usage_count,
                    "file_operations": session.metadata.file_operations,
                },
                "tool_usage": session.extract_tool_usage() if hasattr(session, "extract_tool_usage") else {},
                "file_operations": (
                    session.extract_file_operations()
                    if hasattr(session, "extract_file_operations")
                    else {}
                ),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get session stats: {e}", exc_info=True)
            return {"error": str(e)}
