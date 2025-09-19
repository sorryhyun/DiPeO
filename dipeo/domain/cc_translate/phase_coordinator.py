"""Phase coordinator for Claude Code translation.

This module coordinates all three phases of the translation process:
1. Preprocess - Session-level processing and preparation
2. Convert - Transform session into diagram structure
3. Post-process - Optimize and clean generated diagrams
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .convert import Converter
from .ports import SessionPort
from .post_processing import PipelineConfig, PostProcessor, ProcessingPreset
from .preprocess import Preprocessor


class PipelinePhase(Enum):
    """Enumeration of pipeline phases."""

    PREPROCESS = "preprocess"
    CONVERT = "convert"
    POST_PROCESS = "post_process"


@dataclass
class PhaseResult:
    """Result from a pipeline phase execution."""

    phase: PipelinePhase
    data: Any
    success: bool
    start_time: datetime
    end_time: datetime
    error: Optional[str] = None
    report: Optional[Any] = None

    @property
    def duration_ms(self) -> float:
        """Calculate phase duration in milliseconds."""
        delta = self.end_time - self.start_time
        return delta.total_seconds() * 1000


@dataclass
class PipelineMetrics:
    """Metrics for the entire pipeline execution."""

    total_duration_ms: float = 0.0
    phase_durations: dict[PipelinePhase, float] = field(default_factory=dict)
    phase_results: list[PhaseResult] = field(default_factory=list)
    success: bool = True
    errors: list[str] = field(default_factory=list)

    def add_phase_result(self, result: PhaseResult) -> None:
        """Add a phase result and update metrics."""
        self.phase_results.append(result)
        self.phase_durations[result.phase] = result.duration_ms
        self.total_duration_ms += result.duration_ms

        if not result.success:
            self.success = False
            if result.error:
                self.errors.append(f"{result.phase.value}: {result.error}")


class PhaseCoordinator:
    """Coordinates all phases of Claude Code to DiPeO diagram translation."""

    def __init__(self):
        """Initialize the phase coordinator."""
        self.preprocessor = Preprocessor()
        self.converter = Converter()

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

        # Convert SessionPort to DomainSession if needed
        if hasattr(session, "to_domain_session"):
            domain_session = session.to_domain_session()
        else:
            domain_session = session

        # Phase 1: Preprocess
        if PipelinePhase.PREPROCESS not in skip_phases:
            result = self.with_error_boundary(
                PipelinePhase.PREPROCESS,
                self.preprocessor.process,
                domain_session,
                kwargs.get("preprocess_config"),
            )
            metrics.add_phase_result(result)

            if not result.success:
                return {}, metrics

            preprocessed_data = result.data
        else:
            # If preprocessing is skipped, assume session is preprocessed data
            preprocessed_data = session

        # Phase 2: Convert
        if PipelinePhase.CONVERT not in skip_phases:
            result = self.with_error_boundary(
                PipelinePhase.CONVERT,
                self.converter.process,
                preprocessed_data,
                kwargs.get("convert_config"),
            )
            metrics.add_phase_result(result)

            if not result.success:
                return {}, metrics

            diagram = result.data
        else:
            # If conversion is skipped, assume preprocessed_data is already a diagram
            diagram = preprocessed_data if isinstance(preprocessed_data, dict) else {}

        # Phase 3: Post-process
        if PipelinePhase.POST_PROCESS not in skip_phases:
            # Check if post-processing should be applied
            should_post_process = kwargs.get("post_process", False)

            if should_post_process:
                config = kwargs.get("processing_config") or PipelineConfig.from_preset(
                    ProcessingPreset.STANDARD
                )
                pipeline = PostProcessor(config)

                result = self.with_error_boundary(
                    PipelinePhase.POST_PROCESS, pipeline.process, diagram, config
                )
                metrics.add_phase_result(result)

                if result.success:
                    diagram = result.data

                    # Add metrics to diagram metadata
                    if result.report and hasattr(result.report, "has_changes"):
                        if result.report.has_changes():
                            if "metadata" not in diagram:
                                diagram["metadata"] = {}
                            if "post_processing" not in diagram["metadata"]:
                                diagram["metadata"]["post_processing"] = {}

                            diagram["metadata"]["post_processing"]["optimization"] = {
                                "applied": True,
                                "total_changes": result.report.total_changes,
                                "nodes_removed": result.report.total_nodes_removed,
                                "connections_modified": result.report.total_connections_modified,
                            }

        return diagram, metrics

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
        # Convert SessionPort to DomainSession if needed
        if hasattr(session, "to_domain_session"):
            domain_session = session.to_domain_session()
        else:
            domain_session = session

        preprocessed_data, report = self.preprocessor.process(domain_session, processing_config)
        return preprocessed_data

    def convert_only(self, preprocessed_session) -> dict[str, Any]:
        """
        Run only the conversion phase.

        Useful when you already have preprocessed data or want to skip post-processing.

        Args:
            preprocessed_session: PreprocessedSession from preprocess phase

        Returns:
            Light format diagram dictionary (without post-processing)
        """
        diagram, report = self.converter.process(preprocessed_session)
        return diagram

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
        pipeline = PostProcessor(pipeline_config)
        return pipeline.process(diagram)

    def with_error_boundary(
        self, phase: PipelinePhase, func: callable, *args, **kwargs
    ) -> PhaseResult:
        """
        Execute a function within an error boundary.

        Args:
            phase: The phase being executed
            func: The function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            PhaseResult with success/failure information
        """
        start_time = datetime.now()

        try:
            result = func(*args, **kwargs)

            # Handle tuple returns (data, report)
            if isinstance(result, tuple) and len(result) == 2:
                data, report = result
            else:
                data = result
                report = None

            return PhaseResult(
                phase=phase,
                data=data,
                success=True,
                start_time=start_time,
                end_time=datetime.now(),
                report=report,
            )

        except Exception as e:
            return PhaseResult(
                phase=phase,
                data=None,
                success=False,
                start_time=start_time,
                end_time=datetime.now(),
                error=str(e),
            )
