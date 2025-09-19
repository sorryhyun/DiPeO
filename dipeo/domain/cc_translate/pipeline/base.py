"""Base abstractions for the translation pipeline.

This module provides the core interfaces and abstractions for the
Claude Code to DiPeO diagram translation pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Protocol

from ..ports import SessionPort


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


class PhaseInterface(Protocol):
    """Protocol for individual pipeline phases."""

    @property
    def phase_name(self) -> PipelinePhase:
        """Get the name of this phase."""
        ...

    def execute(self, input_data: Any, **kwargs) -> tuple[Any, Optional[Any]]:
        """
        Execute the phase.

        Args:
            input_data: Input data for the phase
            **kwargs: Additional phase-specific options

        Returns:
            Tuple of (output_data, optional_report)
        """
        ...


class PreprocessPhase(PhaseInterface, Protocol):
    """Interface for the preprocessing phase."""

    def execute(self, session: SessionPort, **kwargs) -> tuple[Any, Optional[list]]:
        """
        Preprocess a session.

        Args:
            session: Session to preprocess via port interface
            **kwargs: Preprocessing options

        Returns:
            Tuple of (preprocessed_data, optional_reports_list)
        """
        ...


class ConvertPhase(PhaseInterface, Protocol):
    """Interface for the conversion phase."""

    def execute(self, preprocessed_data: Any, **kwargs) -> tuple[dict, Optional[Any]]:
        """
        Convert preprocessed data to diagram.

        Args:
            preprocessed_data: Preprocessed session data
            **kwargs: Conversion options

        Returns:
            Tuple of (diagram_dict, optional_conversion_report)
        """
        ...


class PostProcessPhase(PhaseInterface, Protocol):
    """Interface for the post-processing phase."""

    def execute(self, diagram: dict, **kwargs) -> tuple[dict, Optional[Any]]:
        """
        Post-process a diagram.

        Args:
            diagram: Diagram to optimize
            **kwargs: Post-processing options

        Returns:
            Tuple of (optimized_diagram, optional_processing_report)
        """
        ...


class TranslationPipeline(ABC):
    """Abstract base class for the translation pipeline."""

    @abstractmethod
    def translate(
        self, session: SessionPort, skip_phases: Optional[list[PipelinePhase]] = None, **kwargs
    ) -> tuple[dict[str, Any], PipelineMetrics]:
        """
        Execute the full translation pipeline.

        Args:
            session: Session to translate via port interface
            skip_phases: Optional list of phases to skip
            **kwargs: Phase-specific configuration options

        Returns:
            Tuple of (diagram, pipeline_metrics)
        """
        pass

    @abstractmethod
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
        pass

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
