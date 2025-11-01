"""Claude Code session management for CLI."""

import json
from pathlib import Path

from dipeo.application.bootstrap import Container
from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class ClaudeCodeCommandManager:
    """Manages Claude Code session conversion commands for CLI."""

    def __init__(self, container: Container):
        """Initialize Claude Code command manager.

        Args:
            container: Dependency injection container
        """
        self.container = container
        self.registry = container.registry

    async def manage_claude_code(self, action: str, **kwargs) -> bool:
        """Manage Claude Code session conversion.

        Args:
            action: The action to perform (list, convert, watch, stats)
            **kwargs: Action-specific parameters

        Returns:
            True if action completed successfully, False otherwise
        """
        try:
            from dipeo.infrastructure.cc_translate import ClaudeCodeManager

            session_dir = None
            if project := kwargs.get("project"):
                session_dir = Path.home() / ".claude" / "projects" / project
                if not session_dir.exists():
                    print(f"❌ Project directory not found: {session_dir}")
                    return False

            manager = ClaudeCodeManager(session_dir=session_dir)

            if action == "list":
                sessions = manager.list_sessions(kwargs.get("limit", 50))
                for session in sessions:
                    print(f"  {session.id}: {session.name} ({session.created_at})")
                return True

            elif action == "convert":
                session_id = kwargs.get("session_id")
                latest = kwargs.get("latest", False)

                if latest:
                    sessions = manager.list_sessions(latest if isinstance(latest, int) else 1)
                    if not sessions:
                        print("No sessions found")
                        return False
                    results = []
                    for session in sessions:
                        result = manager.convert_session(
                            session.id,
                            kwargs.get("output_dir"),
                            kwargs.get("format", "light"),
                        )
                        results.append(result)
                    return all(results)
                elif session_id:
                    return manager.convert_session(
                        session_id,
                        kwargs.get("output_dir"),
                        kwargs.get("format", "light"),
                    )
                else:
                    print("Either session_id or --latest required")
                    return False

            elif action == "watch":
                return await manager.watch_sessions(
                    kwargs.get("interval", 30),
                    kwargs.get("output_dir"),
                    kwargs.get("format", "light"),
                )

            elif action == "stats":
                stats = await manager.get_session_stats(kwargs["session_id"])
                print(json.dumps(stats, indent=2, default=str))
                return True

            else:
                print(f"❌ Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Claude Code management failed: {e}")
            return False
