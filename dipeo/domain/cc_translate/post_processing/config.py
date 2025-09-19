"""Configuration classes for post-processing pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ProcessingPreset(Enum):
    """Pre-defined processing configurations."""

    NONE = "none"  # No processing
    MINIMAL = "minimal"  # Only essential optimizations
    STANDARD = "standard"  # Recommended optimizations
    AGGRESSIVE = "aggressive"  # All optimizations
    CUSTOM = "custom"  # User-defined configuration


@dataclass
class ReadDeduplicatorConfig:
    """Configuration for ReadNodeDeduplicator processor."""

    enabled: bool = True
    merge_distance: int = -1  # -1 means unlimited distance
    preserve_first: bool = True  # Keep first occurrence vs last
    update_metadata: bool = True  # Add metadata about merged nodes


@dataclass
class ConsecutiveMergerConfig:
    """Configuration for ConsecutiveNodeMerger processor."""

    enabled: bool = True
    max_merge_distance: int = 3  # Max nodes between mergeable operations
    merge_same_type_only: bool = True  # Only merge nodes of exact same type
    merge_reads: bool = True
    merge_writes: bool = False  # Usually don't want to merge writes
    merge_edits: bool = False  # Usually don't want to merge edits
    merge_searches: bool = True  # Merge consecutive grep/glob operations


@dataclass
class ConnectionOptimizerConfig:
    """Configuration for ConnectionOptimizer processor."""

    enabled: bool = True
    remove_redundant: bool = True  # Remove duplicate connections
    simplify_paths: bool = True  # Simplify multi-hop connections when possible
    remove_self_loops: bool = True  # Remove node->node connections
    preserve_labels: bool = True  # Keep connection labels during optimization


@dataclass
class NodeSimplifierConfig:
    """Configuration for NodeSimplifier processor."""

    enabled: bool = False  # Disabled by default as it's more aggressive
    remove_empty_nodes: bool = True  # Remove nodes with no meaningful content
    merge_single_use_nodes: bool = True  # Merge nodes with single input/output
    simplify_tool_chains: bool = True  # Simplify chains of tool operations


@dataclass
class SessionEventPrunerConfig:
    """Configuration for SessionEventPruner processor.

    Note: SessionEventPruner has been moved to preprocess phase but
    config remains here since it's used by PipelineConfig.
    """

    enabled: bool = False  # Disabled by default for backward compatibility
    prune_no_matches: bool = True  # Remove "No matches found" tool results
    prune_errors: bool = False  # Remove error events (more aggressive)
    prune_empty_results: bool = True  # Remove tool results with empty content
    custom_prune_patterns: list[str] = field(
        default_factory=list
    )  # Custom content patterns to prune
    update_metadata: bool = True  # Add metadata about pruned events


@dataclass
class PipelineConfig:
    """Main configuration for post-processing pipeline."""

    preset: ProcessingPreset = ProcessingPreset.STANDARD

    # Individual processor configs
    session_event_pruner: SessionEventPrunerConfig = field(default_factory=SessionEventPrunerConfig)
    read_deduplicator: ReadDeduplicatorConfig = field(default_factory=ReadDeduplicatorConfig)
    consecutive_merger: ConsecutiveMergerConfig = field(default_factory=ConsecutiveMergerConfig)
    connection_optimizer: ConnectionOptimizerConfig = field(
        default_factory=ConnectionOptimizerConfig
    )
    node_simplifier: NodeSimplifierConfig = field(default_factory=NodeSimplifierConfig)

    # Global settings
    preserve_original: bool = False  # Keep copy of original diagram
    fail_on_error: bool = False  # Stop pipeline on processor error
    verbose_reporting: bool = True  # Detailed change reporting
    max_iterations: int = 1  # How many times to run pipeline (for iterative improvements)

    @classmethod
    def from_preset(cls, preset: ProcessingPreset) -> "PipelineConfig":
        """Create configuration from a preset."""
        config = cls(preset=preset)

        if preset == ProcessingPreset.NONE:
            # Disable all processors
            config.session_event_pruner.enabled = False
            config.read_deduplicator.enabled = False
            config.consecutive_merger.enabled = False
            config.connection_optimizer.enabled = False
            config.node_simplifier.enabled = False

        elif preset == ProcessingPreset.MINIMAL:
            # Only essential optimizations
            config.session_event_pruner.enabled = False  # Preserve existing behavior in minimal
            config.read_deduplicator.enabled = True
            config.consecutive_merger.enabled = False
            config.connection_optimizer.enabled = True
            config.node_simplifier.enabled = False

        elif preset == ProcessingPreset.STANDARD:
            # Recommended optimizations (default)
            config.session_event_pruner.enabled = True
            config.session_event_pruner.prune_no_matches = True
            config.session_event_pruner.prune_errors = False  # Conservative approach
            config.read_deduplicator.enabled = True
            config.consecutive_merger.enabled = True
            config.consecutive_merger.merge_writes = False
            config.consecutive_merger.merge_edits = False
            config.connection_optimizer.enabled = True
            config.node_simplifier.enabled = False

        elif preset == ProcessingPreset.AGGRESSIVE:
            # All optimizations enabled
            config.session_event_pruner.enabled = True
            config.session_event_pruner.prune_no_matches = True
            config.session_event_pruner.prune_errors = True  # Aggressive: also prune errors
            config.read_deduplicator.enabled = True
            config.consecutive_merger.enabled = True
            config.consecutive_merger.merge_writes = True
            config.consecutive_merger.merge_edits = True
            config.connection_optimizer.enabled = True
            config.node_simplifier.enabled = True
            config.max_iterations = 2  # Run twice for maximum optimization

        # CUSTOM preset uses whatever settings are provided

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "preset": self.preset.value,
            "session_event_pruner": {
                "enabled": self.session_event_pruner.enabled,
                "prune_no_matches": self.session_event_pruner.prune_no_matches,
                "prune_errors": self.session_event_pruner.prune_errors,
                "prune_empty_results": self.session_event_pruner.prune_empty_results,
                "custom_prune_patterns": self.session_event_pruner.custom_prune_patterns,
            },
            "read_deduplicator": {
                "enabled": self.read_deduplicator.enabled,
                "merge_distance": self.read_deduplicator.merge_distance,
                "preserve_first": self.read_deduplicator.preserve_first,
            },
            "consecutive_merger": {
                "enabled": self.consecutive_merger.enabled,
                "max_merge_distance": self.consecutive_merger.max_merge_distance,
                "merge_reads": self.consecutive_merger.merge_reads,
                "merge_writes": self.consecutive_merger.merge_writes,
                "merge_edits": self.consecutive_merger.merge_edits,
                "merge_searches": self.consecutive_merger.merge_searches,
            },
            "connection_optimizer": {
                "enabled": self.connection_optimizer.enabled,
                "remove_redundant": self.connection_optimizer.remove_redundant,
                "simplify_paths": self.connection_optimizer.simplify_paths,
            },
            "node_simplifier": {
                "enabled": self.node_simplifier.enabled,
                "remove_empty_nodes": self.node_simplifier.remove_empty_nodes,
            },
            "global": {
                "preserve_original": self.preserve_original,
                "fail_on_error": self.fail_on_error,
                "max_iterations": self.max_iterations,
            },
        }
