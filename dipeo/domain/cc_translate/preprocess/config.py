"""Configuration classes for session preprocessing pipeline."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionEventPrunerConfig:
    """Configuration for SessionEventPruner processor.

    This processor removes unnecessary events from Claude Code sessions
    before they are converted to diagrams.
    """

    enabled: bool = True
    prune_no_matches: bool = True  # Remove "No matches found" tool results
    prune_errors: bool = False  # Remove error events (more aggressive)
    prune_empty_results: bool = True  # Remove tool results with empty content
    custom_prune_patterns: list[str] = field(
        default_factory=list
    )  # Custom content patterns to prune
    update_metadata: bool = True  # Add metadata about pruned events
    preserve_thinking_events: bool = True  # Keep thinking/reasoning events


@dataclass
class SessionFieldPrunerConfig:
    """Configuration for SessionFieldPruner processor.

    This processor removes unnecessary fields from session events
    to reduce noise and focus on essential content.
    """

    enabled: bool = True
    remove_empty_fields: bool = True  # Remove fields with empty/null values
    remove_metadata_fields: bool = False  # Remove non-essential metadata
    fields_to_remove: list[str] = field(
        default_factory=lambda: ["internal_id", "debug_info"]
    )  # Specific fields to always remove
    fields_to_keep: list[str] = field(
        default_factory=lambda: ["content", "tool_use", "role", "type"]
    )  # Fields to always preserve
    compact_mode: bool = False  # Aggressive field removal for minimal output
    update_metadata: bool = True  # Add metadata about removed fields


@dataclass
class PreprocessConfig:
    """Main configuration for the preprocessing pipeline.

    Combines all preprocessor configurations for session preparation
    before diagram conversion.
    """

    # Individual processor configs
    event_pruner: SessionEventPrunerConfig = field(default_factory=SessionEventPrunerConfig)
    field_pruner: SessionFieldPrunerConfig = field(default_factory=SessionFieldPrunerConfig)

    # Global preprocessing settings
    preserve_original: bool = False  # Keep copy of original session
    fail_on_error: bool = False  # Stop preprocessing on error
    verbose_reporting: bool = True  # Generate detailed reports
    max_processing_time_ms: float = 5000.0  # Max time for preprocessing

    @classmethod
    def minimal(cls) -> "PreprocessConfig":
        config = cls()
        config.event_pruner.enabled = False
        config.field_pruner.enabled = False
        config.verbose_reporting = False
        return config

    @classmethod
    def standard(cls) -> "PreprocessConfig":
        return cls()  # Use defaults

    @classmethod
    def aggressive(cls) -> "PreprocessConfig":
        config = cls()
        config.event_pruner.prune_errors = True
        config.event_pruner.prune_no_matches = True
        config.field_pruner.remove_metadata_fields = True
        config.field_pruner.compact_mode = True
        return config

    def to_dict(self) -> dict:
        return {
            "event_pruner": {
                "enabled": self.event_pruner.enabled,
                "prune_no_matches": self.event_pruner.prune_no_matches,
                "prune_errors": self.event_pruner.prune_errors,
                "prune_empty_results": self.event_pruner.prune_empty_results,
                "custom_prune_patterns": self.event_pruner.custom_prune_patterns,
            },
            "field_pruner": {
                "enabled": self.field_pruner.enabled,
                "remove_empty_fields": self.field_pruner.remove_empty_fields,
                "remove_metadata_fields": self.field_pruner.remove_metadata_fields,
                "fields_to_remove": self.field_pruner.fields_to_remove,
                "fields_to_keep": self.field_pruner.fields_to_keep,
                "compact_mode": self.field_pruner.compact_mode,
            },
            "global": {
                "preserve_original": self.preserve_original,
                "fail_on_error": self.fail_on_error,
                "verbose_reporting": self.verbose_reporting,
                "max_processing_time_ms": self.max_processing_time_ms,
            },
        }
