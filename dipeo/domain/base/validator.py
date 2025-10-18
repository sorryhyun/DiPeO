"""Base validation framework for the domain layer."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from dipeo.diagram_generated.enums import Severity
from dipeo.domain.base.exceptions import ValidationError


@dataclass
class ValidationWarning:
    message: str
    field_name: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    severity: Severity = Severity.WARNING


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def add_error(self, error: ValidationError) -> None:
        self.errors.append(error)

    def add_warning(self, warning: ValidationWarning) -> None:
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class Validator(Protocol):
    def validate(self, target: Any) -> ValidationResult: ...


class CompositeValidator:
    """Validator that runs multiple validators."""

    def __init__(self, validators: list[Validator]):
        self.validators = validators

    def validate(self, target: Any) -> ValidationResult:
        result = ValidationResult()
        for validator in self.validators:
            validator_result = validator.validate(target)
            result.merge(validator_result)
        return result


class BaseValidator:
    def validate(self, target: Any) -> ValidationResult:
        result = ValidationResult()
        self._perform_validation(target, result)
        return result

    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        raise NotImplementedError("Subclasses must implement _perform_validation")
