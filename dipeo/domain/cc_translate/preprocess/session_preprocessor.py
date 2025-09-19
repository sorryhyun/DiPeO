"""Session-level preprocessing for Claude Code translation.

This module handles the first phase of translation: preprocessing sessions
before conversion to diagrams. It includes session event pruning, metadata
extraction, and preparation of session data for the conversion phase.
"""

from typing import Any, Optional

from dipeo.infrastructure.claude_code import ClaudeCodeSession, ConversationTurn

from ..post_processing import PipelineConfig, ProcessingPreset
from ..shared import TextProcessor
from .session_event_pruner import SessionEventPruner


class PreprocessedSession:
    """Container for preprocessed session data."""

    def __init__(
        self,
        session: ClaudeCodeSession,
        system_messages: list[str],
        conversation_flow: list[ConversationTurn],
        metadata: dict[str, Any],
        pruning_report: Optional[Any] = None,
    ):
        self.session = session
        self.system_messages = system_messages
        self.conversation_flow = conversation_flow
        self.metadata = metadata
        self.pruning_report = pruning_report


class SessionPreprocessor:
    """Handles session-level preprocessing for Claude Code translation."""

    def __init__(self):
        """Initialize the session preprocessor."""
        self.text_processor = TextProcessor()

    def preprocess(
        self,
        session: ClaudeCodeSession,
        processing_config: Optional[PipelineConfig] = None,
    ) -> PreprocessedSession:
        """
        Preprocess a Claude Code session for diagram conversion.

        Args:
            session: Raw Claude Code session
            processing_config: Optional preprocessing configuration

        Returns:
            PreprocessedSession containing processed data
        """
        # Use default config if none provided
        pipeline_config = processing_config or PipelineConfig.from_preset(ProcessingPreset.STANDARD)

        # Apply session-level pruning if configured
        pruning_report = None
        if pipeline_config.session_event_pruner.enabled:
            session_pruner = SessionEventPruner(pipeline_config.session_event_pruner)
            session, pruning_report = session_pruner.process_session(session)

        # Extract system messages from meta/system events
        system_messages = self._extract_system_messages(session)

        # Get conversation flow
        conversation_flow = session.get_conversation_flow()

        # Extract session metadata
        metadata = self._extract_metadata(session)

        return PreprocessedSession(
            session=session,
            system_messages=system_messages,
            conversation_flow=conversation_flow,
            metadata=metadata,
            pruning_report=pruning_report,
        )

    def _extract_system_messages(self, session: ClaudeCodeSession) -> list[str]:
        """Extract all meta/system messages for Claude's system prompt."""
        system_messages = []

        # Get conversation flow to access meta events
        conversation_flow = session.get_conversation_flow()

        for turn in conversation_flow:
            # Collect meta events for system context
            for meta_event in turn.meta_events:
                meta_content = self.text_processor.extract_text_content(
                    meta_event.message.get("content", "")
                )
                if meta_content and meta_content.strip():
                    system_messages.append(meta_content)

        return system_messages

    def _extract_metadata(self, session: ClaudeCodeSession) -> dict[str, Any]:
        """Extract session metadata for diagram."""
        metadata = {}

        # Extract session ID
        if hasattr(session, "session_id"):
            metadata["session_id"] = session.session_id
        else:
            metadata["session_id"] = "unknown"

        # Extract first user message as initial prompt
        first_user_message = ""
        for event in session.events:
            if event.type == "user":
                if "content" in event.message:
                    first_user_message = self.text_processor.extract_text_content(
                        event.message["content"]
                    )
                    break

        metadata["initial_prompt"] = first_user_message
        metadata["total_events"] = len(session.events)

        # Add conversation flow statistics
        conversation_flow = session.get_conversation_flow()
        metadata["conversation_turns"] = len(conversation_flow)

        # Count tool events
        tool_event_count = 0
        for turn in conversation_flow:
            tool_event_count += len(turn.tool_events)
        metadata["tool_events"] = tool_event_count

        return metadata
