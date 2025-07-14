"""Unified validation framework for the domain layer."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from dipeo.core.base.exceptions import ValidationError


class Severity(Enum):
    """Validation issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationWarning:
    """Represents a validation warning."""
    message: str
    field_name: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    severity: Severity = Severity.WARNING


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def add_error(self, error: ValidationError) -> None:
        """Add an error to the result."""
        self.errors.append(error)
    
    def add_warning(self, warning: ValidationWarning) -> None:
        """Add a warning to the result."""
        self.warnings.append(warning)
    
    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class Validator(Protocol):
    """Protocol for all validators."""
    
    def validate(self, target: Any) -> ValidationResult:
        """Validate the target and return a result."""
        ...


class CompositeValidator:
    """Validator that runs multiple validators."""
    
    def __init__(self, validators: list[Validator]):
        self.validators = validators
    
    def validate(self, target: Any) -> ValidationResult:
        """Run all validators and merge results."""
        result = ValidationResult()
        for validator in self.validators:
            validator_result = validator.validate(target)
            result.merge(validator_result)
        return result


class BaseValidator:
    """Base class for validators with common functionality."""
    
    def validate(self, target: Any) -> ValidationResult:
        """Validate the target."""
        result = ValidationResult()
        self._perform_validation(target, result)
        return result
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Override this method to implement validation logic."""
        raise NotImplementedError("Subclasses must implement _perform_validation")