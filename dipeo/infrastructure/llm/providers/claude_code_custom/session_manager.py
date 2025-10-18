"""Session lifecycle management for Claude Code Custom provider."""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from dipeo.config.base_logger import get_module_logger

from .config import FORK_SESSION_ENABLED

logger = get_module_logger(__name__)


class SessionManager:
    """Manage template sessions and forking for efficient execution."""

    def __init__(self):
        self._template_sessions: dict[str, ClaudeSDKClient | None] = {}
        self._template_lock = asyncio.Lock()
        self._active_sessions: list[ClaudeSDKClient] = []
        self._session_lock = asyncio.Lock()

    async def get_or_create_template(
        self, options: ClaudeAgentOptions, execution_phase: str
    ) -> ClaudeSDKClient:
        """Get or create a template session for the given phase.

        Template sessions are created once and maintained for efficiency.
        They serve as base sessions that can be forked for individual requests.

        Args:
            options: Claude Code options with system prompt
            execution_phase: Execution phase identifier

        Returns:
            Template session (not for direct use, should be forked)
        """
        async with self._template_lock:
            if self._template_sessions.get(execution_phase):
                return self._template_sessions[execution_phase]

            logger.info(
                f"[ClaudeCodeCustom] Creating template session for phase '{execution_phase}'"
            )

            if FORK_SESSION_ENABLED:
                options.fork_session = True

            template_session = ClaudeSDKClient(options=options)
            await template_session.connect(None)

            self._template_sessions[execution_phase] = template_session

            return template_session

    async def create_forked_session(
        self, options: ClaudeAgentOptions, execution_phase: str
    ) -> ClaudeSDKClient:
        """Create a session by forking from template or creating fresh.

        This method attempts to fork from an existing template session for efficiency.
        If forking is not supported or fails, it falls back to creating a fresh session.

        Args:
            options: Claude Code options with system prompt
            execution_phase: Execution phase identifier

        Returns:
            New or forked ClaudeSDKClient session for this request
        """
        if FORK_SESSION_ENABLED:
            try:
                template = await self.get_or_create_template(options, execution_phase)

                logger.debug(
                    f"[ClaudeCodeCustom] Forking session from template for phase '{execution_phase}'"
                )

                fork_options = ClaudeAgentOptions(
                    **{
                        **options.__dict__,
                        "resume": template.session_id if hasattr(template, "session_id") else None,
                        "fork_session": True,
                    }
                )

                forked_session = ClaudeSDKClient(options=fork_options)
                await forked_session.connect(None)

                async with self._session_lock:
                    self._active_sessions.append(forked_session)

                return forked_session

            except Exception as e:
                logger.warning(
                    f"[ClaudeCodeCustom] Failed to fork from template: {e}, creating fresh session"
                )

        logger.debug(f"[ClaudeCodeCustom] Creating fresh session for phase '{execution_phase}'")

        session = ClaudeSDKClient(options=options)
        await session.connect(None)

        async with self._session_lock:
            self._active_sessions.append(session)

        return session

    async def cleanup_session(self, session: ClaudeSDKClient) -> None:
        """Clean up a session after use."""
        try:
            await session.disconnect()
            async with self._session_lock:
                if session in self._active_sessions:
                    self._active_sessions.remove(session)
        except Exception as e:
            logger.warning(f"[ClaudeCodeCustom] Error disconnecting session: {e}")

    async def cleanup_all(self) -> None:
        """Cleanup all sessions on shutdown."""
        async with self._session_lock:
            for session in self._active_sessions[:]:
                try:
                    await session.disconnect()
                    logger.debug("[ClaudeCodeCustom] Disconnected active forked session")
                except Exception as e:
                    logger.warning(f"[ClaudeCodeCustom] Error disconnecting forked session: {e}")
            self._active_sessions.clear()

        async with self._template_lock:
            for phase, template in self._template_sessions.items():
                if template:
                    try:
                        await template.disconnect()
                        logger.debug(
                            f"[ClaudeCodeCustom] Disconnected template session for phase '{phase}'"
                        )
                    except Exception as e:
                        logger.warning(
                            f"[ClaudeCodeCustom] Error disconnecting template for phase '{phase}': {e}"
                        )
            self._template_sessions.clear()

        logger.info("[ClaudeCodeCustom] Cleanup complete (templates and forked sessions)")
