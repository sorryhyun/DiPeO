"""Simple session helper for Claude Code SDK using fork_session.

Provides direct session creation with fork_session, eliminating the need
for complex pooling and session management.
"""

import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from claude_code_sdk import ClaudeAgentOptions, ClaudeSDKClient

logger = logging.getLogger(__name__)

# fork_session feature detection
FORK_SESSION_SUPPORTED = "fork_session" in getattr(ClaudeAgentOptions, "__dataclass_fields__", {})

if FORK_SESSION_SUPPORTED:
    logger.info("[SessionHelper] fork_session feature is supported")
else:
    logger.warning("[SessionHelper] fork_session feature is not supported")


class DirectSessionClient:
    """Simple context manager for Claude Code sessions with fork_session.

    Creates a fresh forked session for each query, ensuring clean state
    without any pooling or template management.
    """

    def __init__(
        self,
        options: ClaudeAgentOptions,
        execution_phase: str = "default",
    ):
        """Initialize session client.

        Args:
            options: Claude Code options (includes system_prompt)
            execution_phase: Execution phase for logging
        """
        self.options = options
        self.execution_phase = execution_phase
        self.client = None
        self.session_id = f"{execution_phase}_{datetime.now().isoformat()}"

        # Enable fork_session if supported
        if FORK_SESSION_SUPPORTED and not getattr(options, "fork_session", False):
            self.options.fork_session = True
            logger.debug(
                f"[DirectSessionClient] Enabled fork_session for phase '{execution_phase}'"
            )

    async def __aenter__(self):
        """Enter context - create and connect client."""
        self.client = ClaudeSDKClient(options=self.options)
        await self.client.connect(None)

        logger.debug(
            f"[DirectSessionClient] Connected session for phase '{self.execution_phase}'"
        )

        # Log MCP server configuration if present
        if hasattr(self.options, "mcp_servers") and self.options.mcp_servers:
            logger.debug(
                f"[DirectSessionClient] Session initialized with MCP servers: "
                f"{list(self.options.mcp_servers.keys())}, allowed_tools: {getattr(self.options, 'allowed_tools', [])}"
            )
        else:
            logger.debug(
                f"[DirectSessionClient] Session initialized without MCP servers"
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context - disconnect and cleanup client."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.debug(
                    f"[DirectSessionClient] Disconnected session for phase '{self.execution_phase}'"
                )
            except Exception as e:
                logger.warning(
                    f"[DirectSessionClient] Error disconnecting session for phase '{self.execution_phase}': {e}"
                )
            finally:
                self.client = None

    async def query(self, prompt: str | AsyncIterator[dict[str, Any]]) -> AsyncIterator[Any]:
        """Execute query using the session.

        Args:
            prompt: The prompt to send (string or async iterable of message dicts)

        Yields:
            Messages from the query response
        """
        if not self.client:
            raise RuntimeError("DirectSessionClient not in context")

        try:
            # Send the query
            await self.client.query(prompt, session_id=self.session_id)

            # Stream responses
            message_count = 0
            async for message in self.client.receive_messages():
                message_count += 1

                # Track if session was forked
                new_session_id = getattr(message, "session_id", None)
                if new_session_id and new_session_id != self.session_id:
                    logger.debug(
                        f"[DirectSessionClient] Session forked from {self.session_id} to {new_session_id}"
                    )
                    self.session_id = new_session_id

                yield message

                # Check for completion
                if hasattr(message, "result"):
                    break

            logger.debug(
                f"[DirectSessionClient] Query completed for phase '{self.execution_phase}', "
                f"received {message_count} messages"
            )

        except Exception as e:
            logger.error(
                f"[DirectSessionClient] Query failed for phase '{self.execution_phase}': {e}"
            )
            raise