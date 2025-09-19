"""Post-processing pipeline for diagram optimization."""

import time
from typing import Any, Optional

from .base import BaseProcessor, PipelineReport, ProcessingReport
from .config import PipelineConfig, ProcessingPreset
from .processors import ReadNodeDeduplicator


class PostProcessingPipeline:
    """
    Orchestrates multiple post-processing steps on diagrams.

    The pipeline runs configured processors in sequence, collecting
    reports and handling errors according to configuration.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize pipeline with configuration."""
        self.config = config or PipelineConfig.from_preset(ProcessingPreset.STANDARD)
        self._processors: list[BaseProcessor] = []
        self._setup_processors()

    def _setup_processors(self) -> None:
        """Initialize and configure processors based on config."""
        # Add ReadNodeDeduplicator if enabled
        if self.config.read_deduplicator.enabled:
            self._processors.append(ReadNodeDeduplicator(self.config.read_deduplicator))

        # Other processors would be added here as they're implemented
        # if self.config.consecutive_merger.enabled:
        #     self._processors.append(ConsecutiveNodeMerger(self.config.consecutive_merger))
        # etc.

    def process(self, diagram: dict[str, Any]) -> tuple[dict[str, Any], PipelineReport]:
        """
        Process diagram through all configured processors.

        Args:
            diagram: The diagram to process

        Returns:
            Tuple of (processed diagram, pipeline report)
        """
        start_time = time.time()
        report = PipelineReport()

        # Store original if configured
        original_diagram = diagram.copy() if self.config.preserve_original else None

        # Calculate initial statistics
        report.diagram_stats["initial"] = self._calculate_diagram_stats(diagram)

        # Process through each processor
        processed_diagram = diagram
        for iteration in range(self.config.max_iterations):
            if iteration > 0 and not report.has_changes():
                # No changes in last iteration, stop
                break

            iteration_had_changes = False

            for processor in self._processors:
                if not processor.is_applicable(processed_diagram):
                    continue

                try:
                    # Run processor
                    processed_diagram, processor_report = processor.process(processed_diagram)

                    # Add report
                    report.add_processor_report(processor_report)

                    if processor_report.has_changes():
                        iteration_had_changes = True

                    # Check for errors
                    if processor_report.error and self.config.fail_on_error:
                        # Stop pipeline on error
                        break

                except Exception as e:
                    # Create error report
                    error_report = ProcessingReport(processor_name=processor.name, error=str(e))
                    report.add_processor_report(error_report)

                    if self.config.fail_on_error:
                        # Stop pipeline on exception
                        break

            if not iteration_had_changes:
                # No changes in this iteration, stop
                break

        # Calculate final statistics
        report.diagram_stats["final"] = self._calculate_diagram_stats(processed_diagram)

        # Add original if preserved
        if original_diagram:
            report.diagram_stats["original_preserved"] = True

        # Calculate total time
        report.total_time_ms = (time.time() - start_time) * 1000

        return processed_diagram, report

    def process_with_summary(self, diagram: dict[str, Any]) -> tuple[dict[str, Any], str]:
        """
        Process diagram and return summary string.

        Convenience method for CLI usage.

        Args:
            diagram: The diagram to process

        Returns:
            Tuple of (processed diagram, summary string)
        """
        processed_diagram, report = self.process(diagram)

        if self.config.verbose_reporting:
            summary = report.get_summary()
        else:
            # Simple summary
            if report.has_changes():
                summary = f"Applied {report.total_changes} optimizations"
            else:
                summary = "No optimizations applied"

        return processed_diagram, summary

    def _calculate_diagram_stats(self, diagram: dict[str, Any]) -> dict[str, Any]:
        """Calculate statistics about the diagram."""
        stats = {
            "node_count": len(diagram.get("nodes", [])),
            "connection_count": len(diagram.get("connections", [])),
            "person_count": len(diagram.get("persons", {})),
        }

        # Count node types
        node_types = {}
        for node in diagram.get("nodes", []):
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        stats["node_types"] = node_types

        return stats

    @classmethod
    def create_minimal(cls) -> "PostProcessingPipeline":
        """Create pipeline with minimal optimizations."""
        return cls(PipelineConfig.from_preset(ProcessingPreset.MINIMAL))

    @classmethod
    def create_standard(cls) -> "PostProcessingPipeline":
        """Create pipeline with standard optimizations."""
        return cls(PipelineConfig.from_preset(ProcessingPreset.STANDARD))

    @classmethod
    def create_aggressive(cls) -> "PostProcessingPipeline":
        """Create pipeline with aggressive optimizations."""
        return cls(PipelineConfig.from_preset(ProcessingPreset.AGGRESSIVE))

    @classmethod
    def create_deduplication_only(cls) -> "PostProcessingPipeline":
        """Create pipeline with only read deduplication enabled."""
        config = PipelineConfig.from_preset(ProcessingPreset.NONE)
        config.read_deduplicator.enabled = True
        return cls(config)
