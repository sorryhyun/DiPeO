"""Configuration classes for post-processing pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ProcessingPreset(Enum):
    """Pre-defined processing configurations."""

    NONE = "none"  # No processing
    OPTIMIZATION_ONLY = "optimization_only"  # Optimizations without structural changes
    GROUPING = "grouping"  # TODO subdiagram grouping with optimizations
    STANDARD = "standard"  # Recommended optimizations (for backward compatibility)
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
class To_Do_Subdiagram_Grouper_Config:
    """Configuration for To_Do_Subdiagram_Grouper processor."""

    enabled: bool = True  # Enabled by default for dipeocc
    output_subdirectory: str = "grouped"  # Directory name for sub-diagrams
    preserve_connections: bool = True  # Maintain inter-group connections
    naming_convention: str = "to_do"  # Naming pattern for sub-diagrams

    # New configuration options for TODO extraction
    extract_todos_to_main: bool = True  # Extract TODO nodes to main diagram
    min_nodes_for_subdiagram: int = 3  # Minimum nodes required to create sub-diagram
    skip_trivial_subdiagrams: bool = True  # Skip sub-diagrams with too few nodes


@dataclass
class PipelineConfig:
    """Main configuration for post-processing pipeline."""

    preset: ProcessingPreset = ProcessingPreset.STANDARD

    # Individual processor configs
    # Note: Session-level processors have been moved to preprocess phase
    read_deduplicator: ReadDeduplicatorConfig = field(default_factory=ReadDeduplicatorConfig)
    consecutive_merger: ConsecutiveMergerConfig = field(default_factory=ConsecutiveMergerConfig)
    connection_optimizer: ConnectionOptimizerConfig = field(
        default_factory=ConnectionOptimizerConfig
    )
    node_simplifier: NodeSimplifierConfig = field(default_factory=NodeSimplifierConfig)
    todo_subdiagram_grouper: To_Do_Subdiagram_Grouper_Config = field(
        default_factory=To_Do_Subdiagram_Grouper_Config
    )

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
            config.read_deduplicator.enabled = False
            config.consecutive_merger.enabled = False
            config.connection_optimizer.enabled = False
            config.node_simplifier.enabled = False
            config.todo_subdiagram_grouper.enabled = False

        elif preset in (ProcessingPreset.OPTIMIZATION_ONLY, ProcessingPreset.STANDARD):
            # Optimizations without structural changes
            config.read_deduplicator.enabled = True
            config.consecutive_merger.enabled = True
            config.consecutive_merger.merge_writes = False
            config.consecutive_merger.merge_edits = False
            config.connection_optimizer.enabled = True
            config.node_simplifier.enabled = False
            config.todo_subdiagram_grouper.enabled = False  # No structural changes

        elif preset == ProcessingPreset.GROUPING:
            # TODO subdiagram grouping WITH optimizations
            config.read_deduplicator.enabled = True  # Still want deduplication
            config.consecutive_merger.enabled = True
            config.consecutive_merger.merge_writes = False
            config.consecutive_merger.merge_edits = False
            config.connection_optimizer.enabled = True
            config.node_simplifier.enabled = False
            config.todo_subdiagram_grouper.enabled = True  # Enable grouping

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "preset": self.preset.value,
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
            "todo_subdiagram_grouper": {
                "enabled": self.todo_subdiagram_grouper.enabled,
                "output_subdirectory": self.todo_subdiagram_grouper.output_subdirectory,
                "preserve_connections": self.todo_subdiagram_grouper.preserve_connections,
                "naming_convention": self.todo_subdiagram_grouper.naming_convention,
                "extract_todos_to_main": self.todo_subdiagram_grouper.extract_todos_to_main,
                "min_nodes_for_subdiagram": self.todo_subdiagram_grouper.min_nodes_for_subdiagram,
                "skip_trivial_subdiagrams": self.todo_subdiagram_grouper.skip_trivial_subdiagrams,
            },
            "global": {
                "preserve_original": self.preserve_original,
                "fail_on_error": self.fail_on_error,
                "max_iterations": self.max_iterations,
            },
        }
