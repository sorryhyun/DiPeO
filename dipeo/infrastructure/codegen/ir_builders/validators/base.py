"""Base validator for IR data validation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)

class ValidationError:
    """Represents a validation error."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        """Initialize validation error.

        Args:
            field: Field or path where error occurred
            message: Error message
            severity: Error severity (error, warning, info)
        """
        self.field = field
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.message}"

class ValidationResult:
    """Result of validation check."""

    def __init__(self):
        """Initialize validation result."""
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors).

        Returns:
            True if no errors, False otherwise
        """
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings.

        Returns:
            True if warnings exist
        """
        return len(self.warnings) > 0

    def add_error(self, field: str, message: str) -> None:
        """Add an error to the result.

        Args:
            field: Field where error occurred
            message: Error message
        """
        self.errors.append(ValidationError(field, message, "error"))

    def add_warning(self, field: str, message: str) -> None:
        """Add a warning to the result.

        Args:
            field: Field where warning occurred
            message: Warning message
        """
        self.warnings.append(ValidationError(field, message, "warning"))

    def merge(self, other: ValidationResult) -> None:
        """Merge another validation result into this one.

        Args:
            other: Another validation result to merge
        """
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def get_summary(self) -> str:
        """Get a summary of validation results.

        Returns:
            Summary string
        """
        if self.is_valid:
            if self.has_warnings:
                return f"Validation passed with {len(self.warnings)} warning(s)"
            return "Validation passed"
        return f"Validation failed with {len(self.errors)} error(s) and {len(self.warnings)} warning(s)"

class BaseValidator(ABC):
    """Base class for IR validators."""

    def __init__(self, name: str | None = None):
        """Initialize validator.

        Args:
            name: Validator name for logging
        """
        self.name = name or self.__class__.__name__
        # Use module logger with class name for context
        self.logger = get_module_logger(f"{__name__}.{self.name}")

    @abstractmethod
    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate IR data.

        Args:
            data: IR data to validate

        Returns:
            ValidationResult with errors and warnings
        """
        pass

    def check_required_fields(
        self, data: dict[str, Any], required_fields: list[str]
    ) -> ValidationResult:
        """Check for required fields in data.

        Args:
            data: Data to check
            required_fields: List of required field names

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        for field in required_fields:
            if field not in data:
                result.add_error(field, f"Required field '{field}' is missing")
            elif data[field] is None:
                result.add_error(field, f"Required field '{field}' is None")
            elif isinstance(data[field], list | dict) and len(data[field]) == 0:
                result.add_warning(field, f"Required field '{field}' is empty")

        return result

    def check_field_types(
        self, data: dict[str, Any], field_types: dict[str, type]
    ) -> ValidationResult:
        """Check field types in data.

        Args:
            data: Data to check
            field_types: Mapping of field names to expected types

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        for field, expected_type in field_types.items():
            if field in data:
                value = data[field]
                if value is not None and not isinstance(value, expected_type):
                    actual_type = type(value).__name__
                    expected_name = expected_type.__name__
                    result.add_error(
                        field, f"Field has wrong type: expected {expected_name}, got {actual_type}"
                    )

        return result

    def check_consistency(
        self, data: dict[str, Any], checks: list[tuple[str, callable]]
    ) -> ValidationResult:
        """Run consistency checks on data.

        Args:
            data: Data to check
            checks: List of (name, check_function) tuples

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        for check_name, check_func in checks:
            try:
                check_result = check_func(data)
                if isinstance(check_result, bool):
                    if not check_result:
                        result.add_error(check_name, f"Consistency check '{check_name}' failed")
                elif isinstance(check_result, str):
                    # Check function returned an error message
                    result.add_error(check_name, check_result)
                elif isinstance(check_result, tuple):
                    # Check function returned (success, message)
                    success, message = check_result
                    if not success:
                        result.add_error(check_name, message)
            except Exception as e:
                result.add_error(check_name, f"Consistency check raised exception: {e}")

        return result

class CompositeValidator(BaseValidator):
    """Validator that combines multiple validators."""

    def __init__(self, validators: list[BaseValidator], name: str = "CompositeValidator"):
        """Initialize composite validator.

        Args:
            validators: List of validators to combine
            name: Name for the composite validator
        """
        super().__init__(name)
        self.validators = validators

    def add_validator(self, validator: BaseValidator) -> None:
        """Add a validator to the composite.

        Args:
            validator: Validator to add
        """
        self.validators.append(validator)

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Run all validators and combine results.

        Args:
            data: Data to validate

        Returns:
            Combined ValidationResult
        """
        combined_result = ValidationResult()

        for validator in self.validators:
            try:
                result = validator.validate(data)
                combined_result.merge(result)
            except Exception as e:
                combined_result.add_error(
                    validator.name, f"Validator '{validator.name}' raised exception: {e}"
                )

        return combined_result
