"""Base implementation for IR builders using the step-based pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from dipeo.domain.codegen.ir_builder_port import IRBuilderPort, IRData, IRMetadata
from dipeo.infrastructure.codegen.ir_builders.core.context import BuildContext
from dipeo.infrastructure.codegen.ir_builders.core.steps import (
    BuildStep,
    PipelineOrchestrator,
    StepResult,
    StepType,
)


class BaseIRBuilder(IRBuilderPort, ABC):
    """Base implementation for IR builders using step-based pipeline.

    This refactored base class orchestrates IR generation through a
    composable pipeline of steps (extract, transform, assemble, validate).
    """

    def __init__(self, config_path: str | None = None):
        """Initialize base IR builder with pipeline orchestration.

        Args:
            config_path: Optional path to configuration file
        """
        # Initialize build context
        self.context = BuildContext(config_path=Path(config_path) if config_path else None)

        # Initialize pipeline orchestrator
        self.orchestrator = PipelineOrchestrator(self.context)

        # Configure pipeline steps in subclasses
        self._configure_pipeline()

    @abstractmethod
    def _configure_pipeline(self) -> None:
        """Configure the pipeline steps for this builder.

        Subclasses should override this to add their specific steps
        using self.orchestrator.add_step() or add_steps().
        """
        pass

    @abstractmethod
    def get_builder_type(self) -> str:
        """Get the type identifier for this builder.

        Returns:
            Builder type string (e.g., 'backend', 'frontend', 'strawberry')
        """
        pass

    async def build_ir(
        self, source_data: dict[str, Any], config: dict[str, Any] | None = None
    ) -> IRData:
        """Build IR data from TypeScript AST data.

        Args:
            source_data: Input data to build IR from (TypeScript AST)
            config: Optional configuration parameters (unused for compatibility)

        Returns:
            IRData with generated content and metadata

        Raises:
            RuntimeError: If required pipeline step fails
        """
        # Execute the configured pipeline
        results = self.orchestrator.execute(source_data)

        # Assemble final IR data from pipeline results
        ir_data = self._assemble_ir_data(results)

        # Validate the assembled IR
        if not self.validate_ir(ir_data):
            raise ValueError("IR validation failed")

        return ir_data

    def _assemble_ir_data(self, results: dict[str, StepResult]) -> IRData:
        """Assemble final IR data from pipeline results.

        Args:
            results: Results from all pipeline steps

        Returns:
            Assembled IRData instance
        """
        # Get successful step outputs
        step_data = self.orchestrator.get_successful_results()

        # Look for assembled data from assemble steps
        assembled_data = {}
        for step_name, data in step_data.items():
            if "assemble" in step_name.lower():
                if isinstance(data, dict):
                    assembled_data.update(data)
                else:
                    assembled_data[step_name] = data

        # If no specific assembly, use all step outputs
        if not assembled_data:
            assembled_data = step_data

        # Create metadata
        metadata = self._create_metadata(results)

        return IRData(metadata=metadata, data=assembled_data)

    def _create_metadata(self, results: dict[str, StepResult]) -> IRMetadata:
        """Create metadata for IR output.

        Args:
            results: Pipeline execution results

        Returns:
            IRMetadata instance
        """
        # Count successful steps
        successful_steps = sum(1 for r in results.values() if r.success)
        total_steps = len(results)

        # Gather source info
        source_info = {
            "pipeline_steps": total_steps,
            "successful_steps": successful_steps,
            "builder_type": self.get_builder_type(),
        }

        # Use context to create standard metadata
        metadata_dict = self.context.create_metadata(source_info)

        return IRMetadata(
            version=metadata_dict["version"],
            generated_at=metadata_dict["generated_at"],
            source_files=total_steps,  # Using step count as proxy
            builder_type=self.get_builder_type(),
            # Additional metadata can be added here
        )

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate generated IR data.

        Can be overridden by subclasses for specific validation.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        if not ir_data.metadata:
            return False
        if not ir_data.data:
            return False
        if not ir_data.metadata.builder_type:
            return False

        # Run any validation steps in the pipeline
        for _step_name, step in self.orchestrator.steps.items():
            if step.step_type == StepType.VALIDATE:
                result = step.execute(self.context, ir_data)
                if not result.success:
                    return False

        return True

    def get_cache_key(self, source_data: dict[str, Any]) -> str:
        """Generate deterministic cache key.

        Args:
            source_data: Input data to generate cache key for

        Returns:
            SHA256 hash of the source data
        """
        return self.context.get_cache_key(source_data)

    def reset_pipeline(self) -> None:
        """Reset the pipeline for a fresh execution."""
        self.orchestrator.reset()

    def add_step(self, step: BuildStep) -> None:
        """Add a step to the pipeline.

        Convenience method for dynamic pipeline configuration.

        Args:
            step: Build step to add
        """
        self.orchestrator.add_step(step)

    def get_step_result(self, step_name: str) -> StepResult | None:
        """Get result for a specific step.

        Args:
            step_name: Name of the step

        Returns:
            StepResult or None if step hasn't been executed
        """
        return self.orchestrator.get_result(step_name)
