"""Session-level event pruning processor for removing noisy/unhelpful events."""

import re
import time
from copy import deepcopy
from typing import Optional

from dipeo.domain.cc_translate.models.event import DomainEvent
from dipeo.domain.cc_translate.models.session import DomainSession

from .base import BaseSessionProcessor, SessionChange, SessionChangeType, SessionProcessingReport
from .config import SessionEventPrunerConfig


class SessionEventPruner(BaseSessionProcessor):
    """
    Processor that removes noisy session events before they become diagram nodes.

    This processor operates at the session level, filtering out events like:
    - "No matches found" tool results
    - Error events (configurable)
    - Empty tool results
    - Custom pattern matches
    """

    def __init__(self, config: SessionEventPrunerConfig | None = None):
        """Initialize the session event pruner."""
        super().__init__(config)

    def _get_default_config(self) -> SessionEventPrunerConfig:
        """Get default configuration for this processor."""
        return SessionEventPrunerConfig()

    def process_session(
        self, session: DomainSession
    ) -> tuple[DomainSession, SessionProcessingReport]:
        """
        Process a Claude Code session by filtering out noisy events.

        Args:
            session: The session to process

        Returns:
            Tuple of (filtered session, report)
        """
        start_time = time.time()
        report = self._create_report(session)

        if not self.config.enabled:
            report.total_events_after = report.total_events_before
            return session, report

        # Validate session
        errors = self.validate_session(session)
        if errors:
            for error in errors:
                report.add_error(error)
            return session, report

        # Deep copy the session to avoid modifying the original
        filtered_session = deepcopy(session)

        # Filter events
        filtered_events = []

        for event in filtered_session.events:
            if self._should_prune_event(event):
                # Add change record
                report.add_change(
                    SessionChange(
                        change_type=SessionChangeType.EVENT_PRUNED,
                        description=f"Pruned {event.type} event: {self._get_prune_reason(event)}",
                        target=f"event_{event.id}",
                        details={
                            "event_type": event.type,
                            "prune_reason": self._get_prune_reason(event),
                            "timestamp": event.timestamp.isoformat()
                            if hasattr(event, "timestamp")
                            else None,
                        },
                    )
                )
            else:
                filtered_events.append(event)

        # Update session with filtered events
        filtered_session.events = filtered_events

        # Update metadata with pruning info
        if self.config.update_metadata and report.events_pruned_count > 0:
            if not hasattr(filtered_session, "metadata") or filtered_session.metadata is None:
                filtered_session.metadata = {}

            if not isinstance(filtered_session.metadata, dict):
                # Convert to dict if it's another type
                filtered_session.metadata = {"original": filtered_session.metadata}

            filtered_session.metadata["preprocessing"] = {
                "session_event_pruning": {
                    "events_pruned": report.events_pruned_count,
                    "events_remaining": len(filtered_events),
                    "pruning_config": {
                        "prune_no_matches": self.config.prune_no_matches,
                        "prune_errors": self.config.prune_errors,
                        "prune_empty_results": self.config.prune_empty_results,
                    },
                }
            }

        report.processing_time_ms = (time.time() - start_time) * 1000
        report.total_events_after = len(filtered_events)

        return filtered_session, report

    def _should_prune_event(self, event: DomainEvent) -> bool:
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

    def _is_no_matches_event(self, event: DomainEvent) -> bool:
        """Check if event is a 'No matches found' tool result."""
        if event.type != "user":
            return False

        content = event.content
        if not isinstance(content, list):
            return False

        for item in content:
            if (
                isinstance(item, dict)
                and item.get("type") == "tool_result"
                and item.get("content") in ["No matches found", "Error: File does not exist."]
            ):
                return True

        return False

    def _is_error_event(self, event: DomainEvent) -> bool:
        """Check if event is an error event."""
        content = event.content
        if not isinstance(content, list):
            return False

        return any(isinstance(item, dict) and item.get("is_error") is True for item in content)

    def _is_empty_result_event(self, event: DomainEvent) -> bool:
        """Check if event is a tool result with empty/whitespace-only content."""
        if event.type != "user":
            return False

        content = event.content
        if not isinstance(content, list):
            return False

        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                tool_content = item.get("content", "")
                if isinstance(tool_content, str) and not tool_content.strip():
                    return True

        return False

    def _matches_custom_patterns(self, event: DomainEvent) -> bool:
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

    def _extract_event_text(self, event: DomainEvent) -> str:
        """Extract text content from an event for pattern matching."""
        content = event.content

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

    def _get_prune_reason(self, event: DomainEvent) -> str:
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
