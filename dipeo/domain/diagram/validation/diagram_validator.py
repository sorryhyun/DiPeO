"""Unified diagram validation service - façade using the domain compiler."""

from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import BaseValidator, ValidationResult
from dipeo.domain.diagram.validation import validate_diagram as validate_via_compiler
from dipeo.domain.diagram.validation.business_validators import BusinessValidatorRegistry


class DiagramValidator(BaseValidator):
    """Unified diagram validator combining structural and business logic validation.

    This validator provides a clean separation of concerns:
    - Structural validation: Delegated to the compiler (schema, types, connections)
    - Business validation: Handled by business validators (person refs, API keys)
    """

    def __init__(self, api_key_service: Any | None = None):
        """Initialize the validator with optional business dependencies.

        Args:
            api_key_service: Optional service for validating API key references
        """
        self.business_validators = BusinessValidatorRegistry(api_key_service)

    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        if isinstance(target, DomainDiagram):
            self._validate_diagram(target, result)
        elif isinstance(target, dict):
            try:
                diagram = DomainDiagram.model_validate(target)
                self._validate_diagram(diagram, result)
            except Exception as e:
                result.add_error(ValidationError(f"Invalid diagram format: {e!s}"))
        else:
            result.add_error(ValidationError("Target must be a DomainDiagram or dict"))

    def _validate_diagram(self, diagram: DomainDiagram, result: ValidationResult) -> None:
        """Validate a DomainDiagram using both structural and business validators.

        This method:
        1. Delegates structural validation to the compiler (single source of truth)
        2. Runs business validation rules through the business validator registry
        """
        compilation_result = validate_via_compiler(diagram)

        for error in compilation_result.errors:
            result.add_error(error.to_validation_result(as_warning=False))

        for warning in compilation_result.warnings:
            result.add_warning(warning.to_validation_result(as_warning=True))

        business_errors = self.business_validators.validate(diagram)
        for error in business_errors:
            result.add_error(error)


def validate_or_raise(
    diagram: DomainDiagram | dict[str, Any], api_key_service: Any | None = None
) -> None:
    validator = DiagramValidator(api_key_service)
    result = validator.validate(diagram)
    if not result.is_valid:
        errors = [str(error) for error in result.errors]
        raise ValidationError("; ".join(errors))


def is_valid(diagram: DomainDiagram | dict[str, Any], api_key_service: Any | None = None) -> bool:
    validator = DiagramValidator(api_key_service)
    result = validator.validate(diagram)
    return result.is_valid
