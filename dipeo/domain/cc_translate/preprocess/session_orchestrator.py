"""Session-level preprocessing orchestrator for Claude Code translation.

This module handles the first phase of translation: preprocessing sessions
before conversion to diagrams. It orchestrates session event pruning, field pruning,
metadata extraction, and preparation of session data for the conversion phase.
"""

import time
from typing import Any, Optional

from dipeo.domain.cc_translate.models.preprocessed import PreprocessedData
from dipeo.domain.cc_translate.models.session import DomainSession

from .base import SessionProcessingReport
from .config import PreprocessConfig
from .session_event_pruner import SessionEventPruner
from .session_field_pruner import SessionFieldPruner


class SessionOrchestrator:
    """Orchestrates session-level preprocessing for Claude Code translation."""

    def __init__(self, config: Optional[PreprocessConfig] = None):
        """Initialize the session orchestrator.

        Args:
            config: Preprocessing configuration
        """
        self.config = config or PreprocessConfig.standard()

        # Initialize processors with their configs
        self.event_pruner = SessionEventPruner(self.config.event_pruner)
        self.field_pruner = SessionFieldPruner(self.config.field_pruner)

    def preprocess(
        self,
        session: DomainSession,
    ) -> tuple[PreprocessedData, list[SessionProcessingReport]]:
        """
        Preprocess a Claude Code session for diagram conversion.

        Args:
            session: Domain session to preprocess

        Returns:
            Tuple of (PreprocessedData, list of processing reports)
        """
        start_time = time.time()
        reports = []

        # Track original session for comparison
        original_session = session
        processed_session = session

        # Apply event pruning if enabled
        if self.config.event_pruner.enabled:
            processed_session, event_report = self.event_pruner.process_session(processed_session)
            reports.append(event_report)

            if self.config.fail_on_error and event_report.has_errors:
                # Stop processing on error
                return self._create_error_result(session, reports, "Event pruning failed")

        # Apply field pruning if enabled
        if self.config.field_pruner.enabled:
            processed_session, field_report = self.field_pruner.process_session(processed_session)
            reports.append(field_report)

            if self.config.fail_on_error and field_report.has_errors:
                # Stop processing on error
                return self._create_error_result(session, reports, "Field pruning failed")

        # Extract metadata and prepare preprocessed data
        metadata = self._extract_metadata(processed_session, reports)

        # Create preprocessed data container
        preprocessed_data = PreprocessedData(
            session=processed_session,
            original_session=original_session if self.config.preserve_original else None,
            metadata=metadata,
            processing_reports=reports if self.config.verbose_reporting else [],
            processing_time_ms=(time.time() - start_time) * 1000,
        )

        return preprocessed_data, reports

    def _extract_metadata(
        self, session: DomainSession, reports: list[SessionProcessingReport]
    ) -> dict[str, Any]:
        """Extract metadata from the session and processing reports.

        Args:
            session: The processed session
            reports: Processing reports from all preprocessors

        Returns:
            Metadata dictionary
        """
        metadata = {}

        # Basic session info
        metadata["session_id"] = session.id
        metadata["total_events"] = len(session.events)

        # Processing statistics
        if reports:
            total_changes = sum(r.total_changes for r in reports)
            total_errors = sum(len(r.errors) for r in reports)
            total_warnings = sum(len(r.warnings) for r in reports)

            metadata["preprocessing"] = {
                "total_changes": total_changes,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "reports_count": len(reports),
            }

            # Add individual processor stats
            for report in reports:
                processor_name = report.session_id.replace(session.id, "").strip("_")
                if not processor_name:
                    processor_name = "unknown"

                metadata["preprocessing"][f"{processor_name}_changes"] = report.total_changes

        # Extract initial user message if available
        first_user_content = self._get_first_user_message(session)
        if first_user_content:
            metadata["initial_prompt"] = first_user_content

        # Add configuration summary
        metadata["preprocessing_config"] = {
            "event_pruning": self.config.event_pruner.enabled,
            "field_pruning": self.config.field_pruner.enabled,
            "preserve_original": self.config.preserve_original,
        }

        return metadata

    def _get_first_user_message(self, session: DomainSession) -> Optional[str]:
        """Extract the first user message from the session.

        Args:
            session: The session to extract from

        Returns:
            First user message content or None
        """
        for event in session.events:
            if event.type == "user":
                # Extract text content
                content = event.content
                if isinstance(content, str):
                    # Skip command wrappers
                    if (
                        content.startswith("<command-name>")
                        or content.strip() == "<local-command-stdout></local-command-stdout>"
                    ):
                        continue
                    return content
                elif isinstance(content, list):
                    # Extract from list content
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and "content" in item:
                            text_parts.append(str(item["content"]))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    if text_parts:
                        combined = " ".join(text_parts)
                        # Skip command wrappers
                        if not (
                            combined.startswith("<command-name>")
                            or combined.strip() == "<local-command-stdout></local-command-stdout>"
                        ):
                            return combined

        return None

    def _create_error_result(
        self, session: DomainSession, reports: list[SessionProcessingReport], error_message: str
    ) -> tuple[PreprocessedData, list[SessionProcessingReport]]:
        """Create an error result when preprocessing fails.

        Args:
            session: Original session
            reports: Reports collected so far
            error_message: Error description

        Returns:
            Tuple of (PreprocessedData with error, reports)
        """
        metadata = {"error": error_message, "preprocessing_failed": True}

        preprocessed_data = PreprocessedData(
            session=session,
            original_session=session,
            metadata=metadata,
            processing_reports=reports,
            processing_time_ms=0.0,
        )

        return preprocessed_data, reports
