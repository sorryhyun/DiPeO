"""Session field pruner for removing unnecessary fields from Claude Code sessions."""

import time
from copy import deepcopy
from typing import Optional

from dipeo.domain.cc_translate.models.event import DomainEvent
from dipeo.domain.cc_translate.models.session import DomainSession

from .base import BaseSessionProcessor, SessionChange, SessionChangeType, SessionProcessingReport
from .config import SessionFieldPrunerConfig


class SessionFieldPruner(BaseSessionProcessor):
    """Removes unnecessary fields from Claude Code session events to reduce noise and size."""

    # Fields to always preserve in events
    PRESERVED_FIELDS: set[str] = {
        "type",  # Event type (user/assistant/summary)
        "content",  # Core message content
        "timestamp",  # When the event occurred
        "isMeta",  # Indicates system/meta messages
        "id",  # Event identifier
        "role",  # Event role
    }

    # Fields to prune from all events
    PRUNED_FIELDS: set[str] = {
        "signature",  # Cryptographic signatures (large, not needed)
        "parentUuid",  # Reference to parent events (already parsed)
        "uuid",  # Event UUID (already parsed if needed)
        "sessionId",  # Same for all events in session
        "version",  # Claude Code version
        "gitBranch",  # Git branch info
        "isSidechain",  # Claude Code specific
        "userType",  # Not needed for DiPeO
        "requestId",  # Claude Code request tracking
        "cwd",  # Could be stored once in metadata instead
    }

    # Additional fields to prune from specific message types
    MESSAGE_PRUNED_FIELDS: set[str] = {
        "stop_reason",  # Not needed for diagrams
        "stop_sequence",  # Not needed for diagrams
        "model",  # Can be in metadata instead
    }

    def __init__(self, config: SessionFieldPrunerConfig | None = None):
        """Initialize the field pruner."""
        super().__init__(config)

    def _get_default_config(self) -> SessionFieldPrunerConfig:
        """Get default configuration for this processor."""
        return SessionFieldPrunerConfig()

    def process_session(
        self, session: DomainSession
    ) -> tuple[DomainSession, SessionProcessingReport]:
        """
        Process a session by removing unnecessary fields from events.

        Args:
            session: The session to process

        Returns:
            Tuple of (processed session, report)
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
        processed_session = deepcopy(session)

        # Process each event
        for event in processed_session.events:
            fields_removed = self._prune_event_fields(event, report)

            if fields_removed > 0:
                report.add_change(
                    SessionChange(
                        change_type=SessionChangeType.FIELD_REMOVED,
                        description=f"Removed {fields_removed} fields from {event.type} event",
                        target=f"event_{event.id}",
                        details={
                            "fields_removed_count": fields_removed,
                            "event_type": event.type,
                        },
                    )
                )

        # Update metadata with field pruning info
        if self.config.update_metadata and report.fields_removed_count > 0:
            if not hasattr(processed_session, "metadata") or processed_session.metadata is None:
                processed_session.metadata = {}

            if not isinstance(processed_session.metadata, dict):
                processed_session.metadata = {"original": processed_session.metadata}

            processed_session.metadata["preprocessing"] = processed_session.metadata.get(
                "preprocessing", {}
            )
            processed_session.metadata["preprocessing"]["session_field_pruning"] = {
                "fields_removed": report.fields_removed_count,
                "compact_mode": self.config.compact_mode,
                "fields_to_remove": self.config.fields_to_remove,
            }

        report.processing_time_ms = (time.time() - start_time) * 1000
        report.total_events_after = len(processed_session.events)

        return processed_session, report

    def _prune_event_fields(self, event: DomainEvent, report: SessionProcessingReport) -> int:
        """
        Remove unnecessary fields from a single event.

        Args:
            event: The event to prune fields from
            report: Report to add warnings/errors to

        Returns:
            Number of fields removed
        """
        fields_removed = 0

        # Handle compact mode - aggressive field removal
        if self.config.compact_mode:
            return self._prune_compact_mode(event, report)

        # Get event attributes as dict if possible
        event_dict = event.__dict__ if hasattr(event, "__dict__") else {}

        # Remove empty fields if configured
        if self.config.remove_empty_fields:
            empty_fields = []
            for key, value in list(event_dict.items()):
                if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
                    if key not in self.config.fields_to_keep:
                        empty_fields.append(key)

            for field in empty_fields:
                if hasattr(event, field):
                    delattr(event, field)
                    fields_removed += 1

        # Remove specific fields from config
        for field_name in self.config.fields_to_remove:
            if hasattr(event, field_name) and field_name not in self.config.fields_to_keep:
                try:
                    delattr(event, field_name)
                    fields_removed += 1
                except AttributeError:
                    report.add_warning(f"Could not remove field {field_name} from event {event.id}")

        # Remove metadata fields if configured
        if self.config.remove_metadata_fields:
            metadata_fields = ["debug_info", "internal_id", "trace_id", "parent_id"]
            for field in metadata_fields:
                if hasattr(event, field) and field not in self.config.fields_to_keep:
                    delattr(event, field)
                    fields_removed += 1

        # Process content field if it exists and is a list
        if hasattr(event, "content") and isinstance(event.content, list):
            fields_removed += self._prune_content_items(event.content)

        return fields_removed

    def _prune_compact_mode(self, event: DomainEvent, report: SessionProcessingReport) -> int:
        """
        Aggressively prune fields in compact mode, keeping only essential ones.

        Args:
            event: The event to prune
            report: Report to add warnings to

        Returns:
            Number of fields removed
        """
        fields_removed = 0
        essential_fields = {"id", "type", "content", "role", "timestamp"}

        # Get all current fields
        if hasattr(event, "__dict__"):
            current_fields = set(event.__dict__.keys())
            fields_to_remove = current_fields - essential_fields - set(self.config.fields_to_keep)

            for field in fields_to_remove:
                try:
                    delattr(event, field)
                    fields_removed += 1
                except AttributeError:
                    report.add_warning(f"Could not remove field {field} in compact mode")

        return fields_removed

    def _prune_content_items(self, content: list) -> int:
        """
        Prune unnecessary fields from content items.

        Args:
            content: List of content items

        Returns:
            Number of fields removed
        """
        fields_removed = 0

        for item in content:
            if isinstance(item, dict):
                # Remove signatures from thinking blocks
                if "signature" in item:
                    del item["signature"]
                    fields_removed += 1

                # Remove internal tracking fields
                internal_fields = ["internal_id", "trace_id", "debug_info"]
                for field in internal_fields:
                    if field in item:
                        del item[field]
                        fields_removed += 1

        return fields_removed
