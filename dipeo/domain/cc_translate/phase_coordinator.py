"""Phase coordinator for Claude Code translation.

This module coordinates all three phases of the translation process:
1. Preprocess - Session-level processing and preparation
2. Convert - Transform session into diagram structure
3. Post-process - Optimize and clean generated diagrams
"""

from datetime import datetime
from typing import Any, Optional

from .convert import DiagramConverter
from .pipeline import (
    PhaseResult,
    PipelineMetrics,
    PipelinePhase,
    TranslationPipeline,
)
from .ports import SessionPort
from .post_processing import PipelineConfig, PostProcessingPipeline, ProcessingPreset
from .preprocess import SessionOrchestrator


class PhaseCoordinator(TranslationPipeline):
    """Coordinates all phases of Claude Code to DiPeO diagram translation."""

    def __init__(self):
        """Initialize the phase coordinator."""
        self.preprocessor = SessionOrchestrator()
        self.converter = DiagramConverter()

    def translate(
        self, session: SessionPort, skip_phases: Optional[list[PipelinePhase]] = None, **kwargs
    ) -> tuple[dict[str, Any], PipelineMetrics]:
        """
        Translate a Claude Code session into a light format diagram.

        This method orchestrates all three phases:
        1. Preprocess the session (pruning, metadata extraction)
        2. Convert to diagram structure (nodes, connections)
        3. Post-process the diagram (optimization, cleanup)

        Args:
            session: Session to translate via port interface
            skip_phases: Optional list of phases to skip
            **kwargs: Phase-specific configuration options
                - processing_config: PipelineConfig for post-processing
                - verbose: bool for verbose output

        Returns:
            Tuple of (diagram, pipeline_metrics)
        """
        skip_phases = skip_phases or []
        metrics = PipelineMetrics()

        # Phase 1: Preprocess
        if PipelinePhase.PREPROCESS not in skip_phases:
            preprocess_result = self.execute_phase(PipelinePhase.PREPROCESS, session, **kwargs)
            metrics.add_phase_result(preprocess_result)

            if not preprocess_result.success:
                return {}, metrics

            preprocessed_data = preprocess_result.data
        else:
            # If preprocessing is skipped, assume session is preprocessed data
            preprocessed_data = session

        # Phase 2: Convert
        if PipelinePhase.CONVERT not in skip_phases:
            convert_result = self.execute_phase(PipelinePhase.CONVERT, preprocessed_data, **kwargs)
            metrics.add_phase_result(convert_result)

            if not convert_result.success:
                return {}, metrics

            diagram = convert_result.data
        else:
            # If conversion is skipped, assume preprocessed_data is already a diagram
            diagram = preprocessed_data if isinstance(preprocessed_data, dict) else {}

        # Phase 3: Post-process
        if PipelinePhase.POST_PROCESS not in skip_phases:
            # Check if post-processing should be applied
            should_post_process = kwargs.get("post_process", False)

            if should_post_process:
                postprocess_result = self.execute_phase(
                    PipelinePhase.POST_PROCESS, diagram, **kwargs
                )
                metrics.add_phase_result(postprocess_result)

                if postprocess_result.success:
                    diagram = postprocess_result.data

                    # Add metrics to diagram metadata
                    if postprocess_result.report and hasattr(
                        postprocess_result.report, "has_changes"
                    ):
                        if postprocess_result.report.has_changes():
                            if "metadata" not in diagram:
                                diagram["metadata"] = {}
                            if "post_processing" not in diagram["metadata"]:
                                diagram["metadata"]["post_processing"] = {}

                            diagram["metadata"]["post_processing"]["optimization"] = {
                                "applied": True,
                                "total_changes": postprocess_result.report.total_changes,
                                "nodes_removed": postprocess_result.report.total_nodes_removed,
                                "connections_modified": postprocess_result.report.total_connections_modified,
                            }

        return diagram, metrics

    def execute_phase(self, phase: PipelinePhase, input_data: Any, **kwargs) -> PhaseResult:
        """
        Execute a single phase of the pipeline.

        Args:
            phase: The phase to execute
            input_data: Input data for the phase
            **kwargs: Phase-specific options

        Returns:
            PhaseResult containing output and metrics
        """
        if phase == PipelinePhase.PREPROCESS:
            return self.with_error_boundary(
                phase, self._execute_preprocess, input_data, kwargs.get("processing_config")
            )

        elif phase == PipelinePhase.CONVERT:
            return self.with_error_boundary(phase, self._execute_convert, input_data)

        elif phase == PipelinePhase.POST_PROCESS:
            return self.with_error_boundary(
                phase, self._execute_post_process, input_data, kwargs.get("processing_config")
            )

        else:
            return PhaseResult(
                phase=phase,
                data=None,
                success=False,
                start_time=datetime.now(),
                end_time=datetime.now(),
                error=f"Unknown phase: {phase}",
            )

    def _execute_preprocess(
        self, session: SessionPort, processing_config: Optional[PipelineConfig] = None
    ) -> tuple[Any, Optional[list]]:
        """Execute the preprocessing phase."""
        return self.preprocessor.preprocess(session)

    def _execute_convert(self, preprocessed_data: Any) -> tuple[dict, None]:
        """Execute the conversion phase."""
        diagram = self.converter.convert(preprocessed_data)
        return diagram, None

    def _execute_post_process(
        self, diagram: dict[str, Any], processing_config: Optional[PipelineConfig] = None
    ) -> tuple[dict, Any]:
        """Execute the post-processing phase."""
        pipeline_config = processing_config or PipelineConfig.from_preset(ProcessingPreset.STANDARD)
        pipeline = PostProcessingPipeline(pipeline_config)
        return pipeline.process(diagram)

    def preprocess_only(
        self, session: SessionPort, processing_config: Optional[PipelineConfig] = None
    ):
        """
        Run only the preprocessing phase.

        Useful for analyzing sessions or preparing them for custom conversion.

        Args:
            session: Session via port interface
            processing_config: Custom processing configuration

        Returns:
            PreprocessedData containing processed data
        """
        result = self.execute_phase(
            PipelinePhase.PREPROCESS, session, processing_config=processing_config
        )
        return result.data if result.success else None

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
