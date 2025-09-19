"""Session-level event pruning processor for removing noisy/unhelpful events."""

import re
import time
from typing import Any, Optional

from dipeo.infrastructure.claude_code import ClaudeCodeSession, SessionEvent

from ..post_processing.base import BaseProcessor, ChangeType, ProcessingChange, ProcessingReport
from ..post_processing.config import SessionEventPrunerConfig


class SessionEventPruner(BaseProcessor):
    """
    Processor that removes noisy session events before they become diagram nodes.

    This processor operates at the session level, filtering out events like:
    - "No matches found" tool results
    - Error events (configurable)
    - Empty tool results
    - Custom pattern matches

    Unlike other processors that work on diagram dictionaries, this processor
    modifies the session object before translation to nodes occurs.
    """

    def __init__(self, config: SessionEventPrunerConfig):
        """Initialize the session event pruner."""
        super().__init__()
        self.config = config
        self.enabled = config.enabled

    @property
    def name(self) -> str:
        """Return processor name for reporting."""
        return "SessionEventPruner"

    def process(self, diagram: dict[str, Any]) -> tuple[dict[str, Any], ProcessingReport]:
        """
        Process the diagram by filtering session events.

        Note: This processor is designed to be called before diagram creation,
        but follows the BaseProcessor interface for consistency. When used in
        the pipeline, the session should be passed via metadata.
        """
        start_time = time.time()
        report = ProcessingReport(processor_name=self.name)

        # This processor doesn't modify the diagram directly
        # It's designed to work on session objects before translation
        # For now, return the diagram unchanged with a note

        if not self.enabled:
            return diagram, report

        # Add note that this processor needs to be called at session level
        report.add_change(
            ProcessingChange(
                change_type=ChangeType.METADATA_UPDATED,
                description="Session event pruning should be applied at session level, not diagram level",
                target="session_metadata",
                details={"note": "This processor modifies session events before diagram creation"},
            )
        )

        report.processing_time_ms = (time.time() - start_time) * 1000
        return diagram, report

    def process_session(
        self, session: ClaudeCodeSession
    ) -> tuple[ClaudeCodeSession, ProcessingReport]:
        """
        Process a Claude Code session by filtering out noisy events.

        Args:
            session: The session to process

        Returns:
            Tuple of (filtered session, report)
        """
        start_time = time.time()
        report = ProcessingReport(processor_name=self.name)

        if not self.enabled:
            return session, report

        # Get original event count
        original_count = len(session.events)

        # Filter events
        filtered_events = []
        pruned_count = 0

        for event in session.events:
            if self._should_prune_event(event):
                pruned_count += 1
                # Add change record
                report.add_change(
                    ProcessingChange(
                        change_type=ChangeType.NODE_REMOVED,  # Conceptually removing a future node
                        description=f"Pruned {event.type} event: {self._get_prune_reason(event)}",
                        target=event.uuid,
                        details={
                            "event_type": event.type,
                            "prune_reason": self._get_prune_reason(event),
                            "timestamp": event.timestamp.isoformat(),
                        },
                    )
                )
            else:
                filtered_events.append(event)

        # Create new session with filtered events
        filtered_session = ClaudeCodeSession(session_id=session.session_id)
        filtered_session.events = filtered_events
        filtered_session.metadata = session.metadata

        # Update metadata with pruning info
        if self.config.update_metadata and pruned_count > 0:
            if not hasattr(filtered_session.metadata, "post_processing"):
                filtered_session.metadata.post_processing = {}
            filtered_session.metadata.post_processing["session_event_pruning"] = {
                "events_pruned": pruned_count,
                "events_remaining": len(filtered_events),
                "pruning_config": {
                    "prune_no_matches": self.config.prune_no_matches,
                    "prune_errors": self.config.prune_errors,
                    "prune_empty_results": self.config.prune_empty_results,
                },
            }

        report.processing_time_ms = (time.time() - start_time) * 1000

        # Update report counters
        report.nodes_removed = pruned_count  # Conceptually, these would have become nodes

        return filtered_session, report

    def _should_prune_event(self, event: SessionEvent) -> bool:
        """
        Determine if an event should be pruned.

        Args:
            event: The session event to check

        Returns:
            True if the event should be pruned
        """
        # Check for "No matches found" tool results
        if self.config.prune_no_matches and self._is_no_matches_event(event):
            return True

        # Check for error events
        if self.config.prune_errors and self._is_error_event(event):
            return True

        # Check for empty results
        if self.config.prune_empty_results and self._is_empty_result_event(event):
            return True

        # Check custom patterns
        if self.config.custom_prune_patterns and self._matches_custom_patterns(event):
            return True

        return False

    def _is_no_matches_event(self, event: SessionEvent) -> bool:
        """Check if event is a 'No matches found' tool result."""
        if event.type != "user":
            return False

        message = event.message
        if "content" not in message:
            return False

        content = message["content"]
        if not isinstance(content, list):
            return False

        for item in content:
            if (
                isinstance(item, dict)
                and item.get("type") == "tool_result"
                and item.get("content") == "No matches found"
            ):
                return True

        return False

    def _is_error_event(self, event: SessionEvent) -> bool:
        """Check if event is an error event."""
        message = event.message
        if "content" not in message:
            return False

        content = message["content"]
        if not isinstance(content, list):
            return False

        return any(isinstance(item, dict) and item.get("is_error") is True for item in content)

    def _is_empty_result_event(self, event: SessionEvent) -> bool:
        """Check if event is a tool result with empty/whitespace-only content."""
        if event.type != "user":
            return False

        message = event.message
        if "content" not in message:
            return False

        content = message["content"]
        if not isinstance(content, list):
            return False

        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                tool_content = item.get("content", "")
                if isinstance(tool_content, str) and not tool_content.strip():
                    return True

        return False

    def _matches_custom_patterns(self, event: SessionEvent) -> bool:
        """Check if event content matches any custom prune patterns."""
        if not self.config.custom_prune_patterns:
            return False

        # Extract text content from event
        content_text = self._extract_event_text(event)
        if not content_text:
            return False

        # Check against patterns
        for pattern in self.config.custom_prune_patterns:
            try:
                if re.search(pattern, content_text, re.IGNORECASE):
                    return True
            except re.error:
                # Invalid regex pattern, skip
                continue

        return False

    def _extract_event_text(self, event: SessionEvent) -> str:
        """Extract text content from an event for pattern matching."""
        message = event.message
        if "content" not in message:
            return ""

        content = message["content"]

        # Handle string content
        if isinstance(content, str):
            return content

        # Handle list content (tool results, etc.)
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    # Extract content from tool results
                    if "content" in item:
                        item_content = item["content"]
                        if isinstance(item_content, str):
                            text_parts.append(item_content)
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts)

        return ""

    def _get_prune_reason(self, event: SessionEvent) -> str:
        """Get human-readable reason why an event was pruned."""
        if self._is_no_matches_event(event):
            return "No matches found result"
        elif self._is_error_event(event):
            return "Error event"
        elif self._is_empty_result_event(event):
            return "Empty tool result"
        elif self._matches_custom_patterns(event):
            return "Custom pattern match"
        else:
            return "Unknown reason"

    def is_applicable(self, diagram: dict[str, Any]) -> bool:
        """
        Check if this processor is applicable.

        Note: This processor is designed to work on sessions, not diagrams.
        """
        return self.enabled
