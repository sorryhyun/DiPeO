"""Phase coordinator for Claude Code translation.

This module coordinates all three phases of the translation process:
1. Preprocess - Session-level processing and preparation
2. Convert - Transform session into diagram structure
3. Post-process - Optimize and clean generated diagrams
"""

from typing import Any, Optional

from dipeo.infrastructure.claude_code import ClaudeCodeSession

from .convert import DiagramConverter
from .post_processing import PipelineConfig, PostProcessingPipeline, ProcessingPreset
from .preprocess import SessionPreprocessor


class PhaseCoordinator:
    """Coordinates all phases of Claude Code to DiPeO diagram translation."""

    def __init__(self):
        """Initialize the phase coordinator."""
        self.preprocessor = SessionPreprocessor()
        self.converter = DiagramConverter()

    def translate(
        self,
        session: ClaudeCodeSession,
        post_process: bool = False,
        processing_config: Optional[PipelineConfig] = None,
    ) -> dict[str, Any]:
        """
        Translate a Claude Code session into a light format diagram.

        This method orchestrates all three phases:
        1. Preprocess the session (pruning, metadata extraction)
        2. Convert to diagram structure (nodes, connections)
        3. Post-process the diagram (optimization, cleanup)

        Args:
            session: Parsed Claude Code session
            post_process: Whether to apply post-processing optimizations
            processing_config: Custom processing configuration

        Returns:
            Light format diagram dictionary
        """
        # Phase 1: Preprocess
        preprocessed_session = self.preprocessor.preprocess(session, processing_config)

        # Phase 2: Convert
        diagram = self.converter.convert(preprocessed_session)

        # Phase 3: Post-process (if requested)
        if post_process:
            pipeline_config = processing_config or PipelineConfig.from_preset(
                ProcessingPreset.STANDARD
            )
            pipeline = PostProcessingPipeline(pipeline_config)
            diagram, post_processing_report = pipeline.process(diagram)

            # Add post-processing report to metadata if it had changes
            if post_processing_report.has_changes():
                if "metadata" not in diagram:
                    diagram["metadata"] = {}
                if "post_processing" not in diagram["metadata"]:
                    diagram["metadata"]["post_processing"] = {}

                diagram["metadata"]["post_processing"]["optimization"] = {
                    "applied": True,
                    "total_changes": post_processing_report.total_changes,
                    "nodes_removed": post_processing_report.total_nodes_removed,
                    "connections_modified": post_processing_report.total_connections_modified,
                }

                # Print summary if verbose
                if pipeline_config.verbose_reporting:
                    print(f"\nPost-processing: {post_processing_report.get_summary()}\n")

        return diagram

    def preprocess_only(
        self, session: ClaudeCodeSession, processing_config: Optional[PipelineConfig] = None
    ):
        """
        Run only the preprocessing phase.

        Useful for analyzing sessions or preparing them for custom conversion.

        Args:
            session: Parsed Claude Code session
            processing_config: Custom processing configuration

        Returns:
            PreprocessedSession containing processed data
        """
        return self.preprocessor.preprocess(session, processing_config)

    def convert_only(self, preprocessed_session) -> dict[str, Any]:
        """
        Run only the conversion phase.

        Useful when you already have preprocessed data or want to skip post-processing.

        Args:
            preprocessed_session: PreprocessedSession from preprocess phase

        Returns:
            Light format diagram dictionary (without post-processing)
        """
        return self.converter.convert(preprocessed_session)

    def post_process_only(
        self,
        diagram: dict[str, Any],
        processing_config: Optional[PipelineConfig] = None,
    ) -> tuple[dict[str, Any], Any]:
        """
        Run only the post-processing phase.

        Useful for optimizing existing diagrams.

        Args:
            diagram: Light format diagram to optimize
            processing_config: Custom processing configuration

        Returns:
            Tuple of (optimized diagram, processing report)
        """
        pipeline_config = processing_config or PipelineConfig.from_preset(ProcessingPreset.STANDARD)
        pipeline = PostProcessingPipeline(pipeline_config)
        return pipeline.process(diagram)
