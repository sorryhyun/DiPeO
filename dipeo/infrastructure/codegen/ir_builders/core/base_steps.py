"""Base step classes with template method pattern for common operations.

This module provides base classes that abstract common patterns across BuildStep
subclasses, reducing code duplication and improving maintainability.

Key Classes:
    BaseExtractionStep: Template method for AST extraction patterns
    BaseAssemblerStep: Dependency injection for assembly patterns
    BaseTransformStep: Common transformation patterns
    BaseValidatorStep: Validation framework with result tracking

Phase 1 Implementation - Part of codegen infrastructure refactoring.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional

from dipeo.config.base_logger import get_module_logger
from dipeo.infrastructure.codegen.ir_builders.core.context import BuildContext
from dipeo.infrastructure.codegen.ir_builders.core.steps import BuildStep, StepResult, StepType
from dipeo.infrastructure.codegen.ir_builders.utils import TypeConverter

logger = get_module_logger(__name__)


class BaseExtractionStep(BuildStep):
    """Base class for extraction steps using template method pattern.

    This class abstracts the common pattern found in extraction steps:
    1. Validate input is a dictionary of AST files
    2. Initialize type converter from context
    3. Iterate through AST files with optional filtering
    4. Extract data using subclass-specific logic
    5. Return StepResult with extracted data and metadata

    Subclasses must implement:
        - extract_from_file(): Extract data from a single AST file
        - get_metadata(): Generate metadata for the extraction result

    Optional overrides:
        - should_process_file(): Filter which files to process
        - pre_extraction_hook(): Setup before extraction begins
        - post_extraction_hook(): Cleanup or additional processing after extraction
    """

    def __init__(self, name: str, required: bool = True):
        """Initialize extraction step.

        Args:
            name: Unique name for the step
            required: Whether step must succeed for pipeline to continue
        """
        super().__init__(name=name, step_type=StepType.EXTRACT, required=required)

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Execute extraction using template method pattern.

        Args:
            context: Build context with utilities
            input_data: TypeScript AST data (dict of file_path -> file_data)

        Returns:
            StepResult with extracted data or error
        """
        # Validate input
        if not isinstance(input_data, dict):
            return StepResult(success=False, error="Input data must be a dictionary of AST files")

        # Get type converter from context
        type_converter = context.type_converter

        # Pre-extraction hook
        self.pre_extraction_hook(context, input_data)

        # Extract data from AST files
        extracted_data = []
        for file_path, file_data in input_data.items():
            if not self.should_process_file(file_path, file_data):
                continue

            result = self.extract_from_file(file_path, file_data, type_converter, context)
            if result is not None:
                # Handle both single items and lists
                if isinstance(result, list):
                    extracted_data.extend(result)
                else:
                    extracted_data.append(result)

        # Post-extraction hook
        extracted_data = self.post_extraction_hook(extracted_data, context)

        # Generate metadata
        metadata = self.get_metadata(extracted_data)

        return StepResult(success=True, data=extracted_data, metadata=metadata)

    @abstractmethod
    def extract_from_file(
        self,
        file_path: str,
        file_data: dict[str, Any],
        type_converter: TypeConverter,
        context: BuildContext,
    ) -> Any:
        """Extract data from a single AST file.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file
            type_converter: Type converter instance
            context: Build context

        Returns:
            Extracted data (can be None, single item, or list)
        """
        pass

    def should_process_file(self, file_path: str, file_data: dict[str, Any]) -> bool:
        """Determine if a file should be processed.

        Override this to filter files based on path or content.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file

        Returns:
            True if file should be processed
        """
        return True

    def pre_extraction_hook(self, context: BuildContext, input_data: dict[str, Any]) -> None:
        """Hook called before extraction begins.

        Override for initialization or setup logic.

        Args:
            context: Build context
            input_data: Full AST input data
        """
        pass

    def post_extraction_hook(self, extracted_data: list[Any], context: BuildContext) -> list[Any]:
        """Hook called after extraction completes.

        Override for cleanup or additional processing.

        Args:
            extracted_data: Data extracted from all files
            context: Build context

        Returns:
            Potentially modified extracted data
        """
        return extracted_data

    @abstractmethod
    def get_metadata(self, extracted_data: list[Any]) -> dict[str, Any]:
        """Generate metadata for extraction result.

        Args:
            extracted_data: Extracted data

        Returns:
            Metadata dictionary
        """
        pass


class BaseAssemblerStep(BuildStep):
    """Base class for assembler steps with dependency injection.

    This class abstracts the common pattern found in assembler steps:
    1. Declare multiple dependencies on extraction/transform steps
    2. Execute method gathers data from context using get_step_data()
    3. Assemble final IR structure from gathered data
    4. Include error handling with try/except
    5. Return comprehensive data structure with metadata

    Subclasses must implement:
        - get_dependency_names(): List of required step dependencies
        - assemble_ir(): Assemble IR from gathered dependency data

    Optional overrides:
        - handle_missing_dependency(): Custom handling for missing dependencies
        - validate_dependencies(): Validate dependency data before assembly
    """

    def __init__(self, name: str, required: bool = True):
        """Initialize assembler step.

        Args:
            name: Unique name for the step
            required: Whether step must succeed for pipeline to continue
        """
        super().__init__(name=name, step_type=StepType.ASSEMBLE, required=required)
        # Set dependencies from subclass
        self._dependencies = self.get_dependency_names()

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Execute assembly with dependency injection and error handling.

        Args:
            context: Build context
            input_data: Input data (typically not used, dependencies fetched from context)

        Returns:
            StepResult with assembled IR or error
        """
        try:
            # Gather data from dependencies
            dependency_data = self._gather_dependency_data(context)

            # Validate dependencies
            validation_error = self.validate_dependencies(dependency_data)
            if validation_error:
                return StepResult(success=False, error=validation_error)

            # Assemble IR from dependency data
            assembled_ir = self.assemble_ir(dependency_data, context)

            # Generate metadata
            metadata = self._create_assembly_metadata(dependency_data, assembled_ir)

            return StepResult(success=True, data=assembled_ir, metadata=metadata)

        except Exception as e:
            logger.error(f"Failed to assemble IR in {self.name}: {e}", exc_info=True)
            return StepResult(
                success=False,
                error=str(e),
                metadata={"message": f"Assembly failed: {e}"},
            )

    def _gather_dependency_data(self, context: BuildContext) -> dict[str, Any]:
        """Gather data from all dependencies.

        Args:
            context: Build context with step data

        Returns:
            Dictionary mapping dependency names to their data
        """
        dependency_data = {}
        for dep_name in self._dependencies:
            data = context.get_step_data(dep_name)
            if data is None:
                data = self.handle_missing_dependency(dep_name)
            dependency_data[dep_name] = data
        return dependency_data

    @abstractmethod
    def get_dependency_names(self) -> list[str]:
        """Get list of required dependency step names.

        Returns:
            List of step names this assembler depends on
        """
        pass

    @abstractmethod
    def assemble_ir(self, dependency_data: dict[str, Any], context: BuildContext) -> dict[str, Any]:
        """Assemble final IR from dependency data.

        Args:
            dependency_data: Dictionary of data from dependencies
            context: Build context

        Returns:
            Assembled IR data dictionary
        """
        pass

    def handle_missing_dependency(self, dep_name: str) -> Any:
        """Handle missing dependency data.

        Override to provide default values or alternative handling.

        Args:
            dep_name: Name of missing dependency

        Returns:
            Default value for missing dependency (None, [], {}, etc.)
        """
        logger.warning(f"Dependency '{dep_name}' missing in {self.name}, using None")
        return None

    def validate_dependencies(self, dependency_data: dict[str, Any]) -> Optional[str]:
        """Validate dependency data before assembly.

        Override to add validation logic.

        Args:
            dependency_data: Dictionary of dependency data

        Returns:
            Error message if validation fails, None if valid
        """
        return None

    def _create_assembly_metadata(
        self, dependency_data: dict[str, Any], assembled_ir: dict[str, Any]
    ) -> dict[str, Any]:
        """Create metadata for assembly result.

        Args:
            dependency_data: Input dependency data
            assembled_ir: Assembled IR data

        Returns:
            Metadata dictionary
        """
        return {
            "message": f"Successfully assembled {self.name} IR data",
            "dependency_count": len(dependency_data),
            "generated_at": datetime.now().isoformat(),
        }


class BaseTransformStep(BuildStep):
    """Base class for transform steps with common patterns.

    This class abstracts the common pattern found in transform steps:
    1. Add dependencies on other steps
    2. Execute method handles input from dependencies
    3. Transform/convert/build data
    4. Return StepResult with transformed data

    Subclasses must implement:
        - get_dependency_names(): List of required dependencies
        - transform_data(): Transform the input data

    Optional overrides:
        - extract_input_from_dependencies(): Custom extraction of input from dependencies
        - validate_input(): Validate input before transformation
        - post_transform_hook(): Additional processing after transformation
    """

    def __init__(self, name: str, required: bool = True):
        """Initialize transform step.

        Args:
            name: Unique name for the step
            required: Whether step must succeed for pipeline to continue
        """
        super().__init__(name=name, step_type=StepType.TRANSFORM, required=required)
        # Set dependencies from subclass
        dependencies = self.get_dependency_names()
        for dep_name in dependencies:
            self.add_dependency(dep_name)

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Execute transformation.

        Args:
            context: Build context
            input_data: Input data from pipeline (may be dict with dependency data)

        Returns:
            StepResult with transformed data or error
        """
        # Extract input from dependencies if needed
        transform_input = self.extract_input_from_dependencies(input_data, context)

        # Validate input
        validation_error = self.validate_input(transform_input)
        if validation_error:
            return StepResult(success=False, error=validation_error)

        # Transform data
        try:
            transformed_data = self.transform_data(transform_input, context)

            # Post-transform hook
            transformed_data = self.post_transform_hook(transformed_data, context)

            # Generate metadata
            metadata = self.get_transform_metadata(transform_input, transformed_data)

            return StepResult(success=True, data=transformed_data, metadata=metadata)

        except Exception as e:
            logger.error(f"Transform failed in {self.name}: {e}", exc_info=True)
            return StepResult(success=False, error=str(e))

    @abstractmethod
    def get_dependency_names(self) -> list[str]:
        """Get list of required dependency step names.

        Returns:
            List of step names this transform depends on
        """
        pass

    @abstractmethod
    def transform_data(self, input_data: Any, context: BuildContext) -> Any:
        """Transform the input data.

        Args:
            input_data: Input data to transform
            context: Build context

        Returns:
            Transformed data
        """
        pass

    def extract_input_from_dependencies(
        self, input_data: Any, context: BuildContext
    ) -> Any:
        """Extract input from dependency data.

        Default implementation handles common pattern of dict with dependency names.
        Override for custom extraction logic.

        Args:
            input_data: Input data from pipeline
            context: Build context

        Returns:
            Extracted input for transformation
        """
        dependencies = self.get_dependency_names()

        # If input is dict with single dependency name, extract it
        if isinstance(input_data, dict) and len(dependencies) == 1:
            dep_name = dependencies[0]
            if dep_name in input_data:
                return input_data[dep_name]

        # If input is dict with multiple dependencies, gather all
        if isinstance(input_data, dict) and any(dep in input_data for dep in dependencies):
            return {dep: input_data.get(dep) for dep in dependencies}

        # Otherwise, return input as-is
        return input_data

    def validate_input(self, input_data: Any) -> Optional[str]:
        """Validate input data before transformation.

        Override to add validation logic.

        Args:
            input_data: Input data to validate

        Returns:
            Error message if validation fails, None if valid
        """
        if input_data is None:
            return "Input data is None"
        return None

    def post_transform_hook(self, transformed_data: Any, context: BuildContext) -> Any:
        """Hook called after transformation.

        Override for additional processing.

        Args:
            transformed_data: Transformed data
            context: Build context

        Returns:
            Potentially modified transformed data
        """
        return transformed_data

    def get_transform_metadata(self, input_data: Any, transformed_data: Any) -> dict[str, Any]:
        """Generate metadata for transformation result.

        Override to provide custom metadata.

        Args:
            input_data: Input data
            transformed_data: Transformed data

        Returns:
            Metadata dictionary
        """
        return {
            "transform": self.name,
            "generated_at": datetime.now().isoformat(),
        }


class BaseValidatorStep(BuildStep):
    """Base class for validation steps with result tracking.

    This class provides a framework for validation steps:
    1. Execute validation checks
    2. Track validation results (errors, warnings, info)
    3. Determine success based on error severity
    4. Return detailed validation report

    Subclasses must implement:
        - perform_validation(): Execute validation checks

    Validation tracking:
        - add_error(): Add critical error (fails validation)
        - add_warning(): Add warning (doesn't fail validation)
        - add_info(): Add informational message
    """

    def __init__(self, name: str, required: bool = True, fail_on_warnings: bool = False):
        """Initialize validator step.

        Args:
            name: Unique name for the step
            required: Whether step must succeed for pipeline to continue
            fail_on_warnings: Whether warnings should fail validation
        """
        super().__init__(name=name, step_type=StepType.VALIDATE, required=required)
        self.fail_on_warnings = fail_on_warnings
        self._errors: list[str] = []
        self._warnings: list[str] = []
        self._info: list[str] = []

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Execute validation.

        Args:
            context: Build context
            input_data: Data to validate

        Returns:
            StepResult with validation results
        """
        # Reset validation state
        self._errors = []
        self._warnings = []
        self._info = []

        try:
            # Perform validation
            self.perform_validation(input_data, context)

            # Determine success
            has_errors = len(self._errors) > 0
            has_warnings = len(self._warnings) > 0
            success = not has_errors and (not self.fail_on_warnings or not has_warnings)

            # Build validation report
            report = self._build_validation_report()

            return StepResult(
                success=success,
                data=report,
                error=None if success else f"Validation failed with {len(self._errors)} errors",
                metadata={
                    "error_count": len(self._errors),
                    "warning_count": len(self._warnings),
                    "info_count": len(self._info),
                },
            )

        except Exception as e:
            logger.error(f"Validation exception in {self.name}: {e}", exc_info=True)
            return StepResult(
                success=False,
                error=f"Validation exception: {e}",
                metadata={"exception": str(e)},
            )

    @abstractmethod
    def perform_validation(self, input_data: Any, context: BuildContext) -> None:
        """Perform validation checks.

        Use add_error(), add_warning(), add_info() to record results.

        Args:
            input_data: Data to validate
            context: Build context
        """
        pass

    def add_error(self, message: str) -> None:
        """Add critical error (will fail validation).

        Args:
            message: Error message
        """
        self._errors.append(message)
        logger.error(f"[{self.name}] ERROR: {message}")

    def add_warning(self, message: str) -> None:
        """Add warning (won't fail validation unless fail_on_warnings=True).

        Args:
            message: Warning message
        """
        self._warnings.append(message)
        logger.warning(f"[{self.name}] WARNING: {message}")

    def add_info(self, message: str) -> None:
        """Add informational message.

        Args:
            message: Info message
        """
        self._info.append(message)
        logger.info(f"[{self.name}] INFO: {message}")

    def _build_validation_report(self) -> dict[str, Any]:
        """Build detailed validation report.

        Returns:
            Validation report dictionary
        """
        return {
            "validator": self.name,
            "errors": self._errors.copy(),
            "warnings": self._warnings.copy(),
            "info": self._info.copy(),
            "passed": len(self._errors) == 0,
            "timestamp": datetime.now().isoformat(),
        }