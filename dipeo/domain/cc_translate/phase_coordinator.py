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
from .post_processing import PipelineConfig, PostProcessor, ProcessingPreset
from .preprocess import Preprocessor


class PipelinePhase(Enum):
    PREPROCESS = "preprocess"
    CONVERT = "convert"
    POST_PROCESS = "post_process"


@dataclass
class PhaseResult:
    phase: PipelinePhase
    data: Any
    success: bool
    start_time: datetime
    end_time: datetime
    error: str | None = None
    report: Any | None = None

    @property
    def duration_ms(self) -> float:
        delta = self.end_time - self.start_time
        return delta.total_seconds() * 1000


@dataclass
class PipelineMetrics:
    total_duration_ms: float = 0.0
    phase_durations: dict[PipelinePhase, float] = field(default_factory=dict)
    phase_results: list[PhaseResult] = field(default_factory=list)
    success: bool = True
    errors: list[str] = field(default_factory=list)

    def add_phase_result(self, result: PhaseResult) -> None:
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
        self.preprocessor = Preprocessor()
        self.converter = Converter()

    def translate(
        self, session: Any, skip_phases: list[PipelinePhase] | None = None, **kwargs
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

        # Convert session to DomainSession if needed
        if hasattr(session, "to_domain_session"):
            domain_session = session.to_domain_session()
        else:
            domain_session = session

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

        if PipelinePhase.POST_PROCESS not in skip_phases:
            should_post_process = kwargs.get("post_process", False)

            if should_post_process:
                config = kwargs.get("processing_config") or PipelineConfig.from_preset(
                    ProcessingPreset.STANDARD
                )
                pipeline = PostProcessor(config)

                post_process_kwargs = {}
                if "output_base_path" in kwargs:
                    post_process_kwargs["output_base_path"] = kwargs["output_base_path"]

                result = self.with_error_boundary(
                    PipelinePhase.POST_PROCESS,
                    pipeline.process,
                    diagram,
                    config,
                    **post_process_kwargs,
                )
                metrics.add_phase_result(result)

                if result.success:
                    diagram = result.data

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

    def preprocess_only(self, session: Any, processing_config: PipelineConfig | None = None):
        """Run only the preprocessing phase, useful for analyzing sessions or preparing for custom conversion."""
        # Convert session to DomainSession if needed
        if hasattr(session, "to_domain_session"):
            domain_session = session.to_domain_session()
        else:
            domain_session = session

        preprocessed_data, report = self.preprocessor.process(domain_session, processing_config)
        return preprocessed_data

    def convert_only(self, preprocessed_session) -> dict[str, Any]:
        """Run only conversion, useful when you already have preprocessed data or want to skip post-processing."""
        diagram, report = self.converter.process(preprocessed_session)
        return diagram

    def post_process_only(
        self,
        diagram: dict[str, Any],
        processing_config: PipelineConfig | None = None,
    ) -> tuple[dict[str, Any], Any]:
        """Run only post-processing, useful for optimizing existing diagrams."""
        pipeline_config = processing_config or PipelineConfig.from_preset(ProcessingPreset.STANDARD)
        pipeline = PostProcessor(pipeline_config)
        return pipeline.process(diagram)

    def with_error_boundary(
        self, phase: PipelinePhase, func: callable, *args, **kwargs
    ) -> PhaseResult:
        """Execute a function within an error boundary, returning PhaseResult with success/failure information."""
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
