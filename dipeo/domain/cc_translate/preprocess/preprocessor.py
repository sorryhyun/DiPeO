"""Session-level preprocessing orchestrator for Claude Code translation.

This module handles the first phase of translation: preprocessing sessions
before conversion to diagrams. It orchestrates session event pruning, field pruning,
metadata extraction, and preparation of session data for the conversion phase.
"""

import time
from typing import Any, Optional

from dipeo.domain.cc_translate.models.preprocessed import PreprocessedData
from dipeo.domain.cc_translate.models.session import DomainSession

from .base import BasePreprocessor, SessionProcessingReport
from .config import PreprocessConfig
from .session_event_pruner import SessionEventPruner
from .session_field_pruner import SessionFieldPruner


class Preprocessor(BasePreprocessor):
    """Orchestrates session-level preprocessing for Claude Code translation."""

    def __init__(self, config: Optional[PreprocessConfig] = None):
        """Initialize the preprocessor.

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
        )

        # Set additional metadata and stats
        preprocessed_data.conversation_context = metadata
        preprocessed_data.stats.processing_time_ms = int((time.time() - start_time) * 1000)

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
        metadata["session_id"] = session.session_id
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
                processor_name = report.session_id.replace(session.session_id, "").strip("_")
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
        preprocessed_data = PreprocessedData(
            session=session,
        )

        # Mark as error
        preprocessed_data.errors.append(error_message)
        preprocessed_data.conversation_context = {
            "error": error_message,
            "preprocessing_failed": True,
        }

        return preprocessed_data, reports

    def process(
        self, session: DomainSession, config: Optional[Any] = None
    ) -> tuple[PreprocessedData, SessionProcessingReport]:
        """
        Standard interface: process a session and return preprocessed data with report.

        Args:
            session: The session to preprocess
            config: Optional preprocessing configuration

        Returns:
            Tuple of (preprocessed_data, processing_report)
        """
        # Use provided config or fall back to instance config
        if config and isinstance(config, PreprocessConfig):
            original_config = self.config
            self.config = config
            try:
                preprocessed_data, reports = self.preprocess(session)
            finally:
                self.config = original_config
        else:
            preprocessed_data, reports = self.preprocess(session)

        # Consolidate multiple reports into one
        consolidated_report = self._consolidate_reports(session.session_id, reports)

        return preprocessed_data, consolidated_report

    def _consolidate_reports(
        self, session_id: str, reports: list[SessionProcessingReport]
    ) -> SessionProcessingReport:
        """Consolidate multiple processing reports into one.

        Args:
            session_id: The session ID
            reports: List of individual processor reports

        Returns:
            Consolidated SessionProcessingReport
        """
        consolidated = SessionProcessingReport(session_id=session_id)

        for report in reports:
            # Merge changes
            consolidated.changes.extend(report.changes)

            # Merge errors and warnings
            consolidated.errors.extend(report.errors)
            consolidated.warnings.extend(report.warnings)

            # Update event counts
            if report.total_events_before > 0:
                consolidated.total_events_before = max(
                    consolidated.total_events_before, report.total_events_before
                )
            consolidated.total_events_after = report.total_events_after

            # Sum processing times
            consolidated.processing_time_ms += report.processing_time_ms

            # Merge metadata
            if report.metadata:
                consolidated.metadata.update(report.metadata)

        return consolidated
