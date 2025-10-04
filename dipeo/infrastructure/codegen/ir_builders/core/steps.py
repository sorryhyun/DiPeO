"""Step interface and orchestration for IR build pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.core.context import BuildContext


class StepType(Enum):
    """Type of build step in the pipeline."""

    EXTRACT = "extract"
    TRANSFORM = "transform"
    ASSEMBLE = "assemble"
    VALIDATE = "validate"


class StepExecutionMode(Enum):
    """Execution mode for steps."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class StepResult:
    """Result from executing a build step.

    Attributes:
        success: Whether the step completed successfully
        data: Output data from the step
        error: Error message if step failed
        metadata: Additional metadata about execution
    """

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class BuildStep(ABC):
    """Abstract base class for build pipeline steps.

    Each step represents a discrete operation in the IR build process.
    Steps can extract data, transform it, assemble it, or validate it.
    """

    def __init__(self, name: str, step_type: StepType, required: bool = True):
        """Initialize build step.

        Args:
            name: Unique name for the step
            step_type: Type of step (extract, transform, etc.)
            required: Whether step must succeed for pipeline to continue
        """
        self.name = name
        self.step_type = step_type
        self.required = required
        self._dependencies: list[str] = []

    @abstractmethod
    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Execute the build step.

        Args:
            context: Build context with config and utilities
            input_data: Input data for the step

        Returns:
            StepResult with output data or error
        """
        pass

    def validate_input(self, input_data: Any) -> bool:
        """Validate input data before execution.

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid
        """
        return input_data is not None

    def add_dependency(self, step_name: str) -> None:
        """Add a dependency on another step.

        Args:
            step_name: Name of the step this depends on
        """
        if step_name not in self._dependencies:
            self._dependencies.append(step_name)

    @property
    def dependencies(self) -> list[str]:
        """Get list of step dependencies.

        Returns:
            List of step names this step depends on
        """
        return self._dependencies.copy()


class CompositeStep(BuildStep):
    """A step composed of multiple sub-steps."""

    def __init__(
        self,
        name: str,
        step_type: StepType,
        sub_steps: list[BuildStep],
        mode: StepExecutionMode = StepExecutionMode.SEQUENTIAL,
        required: bool = True,
    ):
        """Initialize composite step.

        Args:
            name: Unique name for the composite step
            step_type: Type of step
            sub_steps: List of sub-steps to execute
            mode: How to execute sub-steps (sequential or parallel)
            required: Whether step must succeed
        """
        super().__init__(name, step_type, required)
        self.sub_steps = sub_steps
        self.mode = mode

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Execute all sub-steps according to mode.

        Args:
            context: Build context
            input_data: Input data for the step

        Returns:
            Combined StepResult from all sub-steps
        """
        results = {}
        errors = []
        success = True

        if self.mode == StepExecutionMode.SEQUENTIAL:
            current_input = input_data
            for step in self.sub_steps:
                result = step.execute(context, current_input)
                results[step.name] = result.data
                if not result.success:
                    if step.required:
                        return StepResult(
                            success=False,
                            error=f"Required sub-step '{step.name}' failed: {result.error}",
                        )
                    errors.append(f"{step.name}: {result.error}")
                    success = False
                # Use output as input for next step in sequential mode
                current_input = result.data
        else:
            # Parallel execution (simplified - would use asyncio in practice)
            for step in self.sub_steps:
                result = step.execute(context, input_data)
                results[step.name] = result.data
                if not result.success:
                    if step.required:
                        errors.append(f"Required sub-step '{step.name}' failed: {result.error}")
                        success = False
                    else:
                        errors.append(f"{step.name}: {result.error}")

        return StepResult(
            success=success and not errors,
            data=results,
            error="; ".join(errors) if errors else None,
            metadata={"sub_step_count": len(self.sub_steps), "mode": self.mode.value},
        )


class PipelineOrchestrator:
    """Orchestrates the execution of build pipeline steps."""

    def __init__(self, context: BuildContext):
        """Initialize pipeline orchestrator.

        Args:
            context: Build context for the pipeline
        """
        self.context = context
        self.steps: dict[str, BuildStep] = {}
        self.execution_order: list[str] = []
        self._results: dict[str, StepResult] = {}

    def add_step(self, step: BuildStep) -> None:
        """Add a step to the pipeline.

        Args:
            step: Build step to add
        """
        if step.name in self.steps:
            raise ValueError(f"Step '{step.name}' already exists in pipeline")
        self.steps[step.name] = step

    def add_steps(self, steps: list[BuildStep]) -> None:
        """Add multiple steps to the pipeline.

        Args:
            steps: List of build steps to add
        """
        for step in steps:
            self.add_step(step)

    def _resolve_execution_order(self) -> list[str]:
        """Resolve execution order based on dependencies.

        Returns:
            Ordered list of step names

        Raises:
            ValueError: If circular dependencies detected
        """
        visited = set()
        temp_visited = set()
        order = []

        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving step '{name}'")
            if name in visited:
                return

            temp_visited.add(name)
            step = self.steps.get(name)
            if step:
                for dep in step._dependencies:
                    if dep in self.steps:
                        visit(dep)
            temp_visited.remove(name)
            visited.add(name)
            order.append(name)

        for step_name in self.steps:
            if step_name not in visited:
                visit(step_name)

        return order

    def execute(self, input_data: Any = None) -> dict[str, StepResult]:
        """Execute the pipeline with given input data.

        Args:
            input_data: Initial input data for the pipeline

        Returns:
            Dictionary mapping step names to their results

        Raises:
            RuntimeError: If required step fails
        """
        self.execution_order = self._resolve_execution_order()
        self._results = {}

        current_data = input_data
        original_input = input_data  # Keep reference to original input

        for step_name in self.execution_order:
            step = self.steps[step_name]

            # EXTRACT steps always get the original input data (AST)
            # Other steps can use dependency data
            if step.step_type == StepType.EXTRACT:
                step_input = original_input
            elif step._dependencies:
                # Collect outputs from dependencies
                dep_data = {}
                for dep_name in step._dependencies:
                    if dep_name in self._results:
                        dep_data[dep_name] = self._results[dep_name].data
                step_input = dep_data if dep_data else current_data
            else:
                step_input = current_data

            # Execute step
            result = step.execute(self.context, step_input)
            self._results[step_name] = result

            # Store result in context for inter-step access
            if result.success and result.data is not None:
                self.context.set_step_data(step_name, result.data)

            # Handle failure
            if not result.success and step.required:
                raise RuntimeError(f"Required step '{step_name}' failed: {result.error}")

            # Update current data for next step
            if result.success and result.data is not None:
                current_data = result.data

        return self._results

    def get_result(self, step_name: str) -> StepResult | None:
        """Get result for a specific step.

        Args:
            step_name: Name of the step

        Returns:
            StepResult or None if step hasn't been executed
        """
        return self._results.get(step_name)

    def get_successful_results(self) -> dict[str, Any]:
        """Get data from all successful steps.

        Returns:
            Dictionary mapping step names to their output data
        """
        return {
            name: result.data
            for name, result in self._results.items()
            if result.success and result.data is not None
        }

    def reset(self) -> None:
        """Reset the pipeline for a fresh execution."""
        self._results = {}
        self.execution_order = []


class StepRegistry:
    """Registry for reusable build steps."""

    _steps: dict[str, type[BuildStep]] = {}

    @classmethod
    def register(cls, name: str, step_class: type[BuildStep]) -> None:
        """Register a step class for reuse.

        Args:
            name: Name to register step under
            step_class: Step class to register
        """
        cls._steps[name] = step_class

    @classmethod
    def get(cls, name: str) -> type[BuildStep] | None:
        """Get registered step class by name.

        Args:
            name: Name of registered step

        Returns:
            Step class or None if not found
        """
        return cls._steps.get(name)

    @classmethod
    def create(cls, name: str, **kwargs) -> BuildStep | None:
        """Create instance of registered step.

        Args:
            name: Name of registered step
            **kwargs: Arguments for step constructor

        Returns:
            Step instance or None if not found
        """
        step_class = cls.get(name)
        if step_class:
            return step_class(**kwargs)
        return None
