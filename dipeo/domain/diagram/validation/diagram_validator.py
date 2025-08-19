"""Unified diagram validation service - façade using the domain compiler."""

from typing import Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import BaseValidator, ValidationResult, ValidationWarning
from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.validation import validate_diagram as validate_via_compiler


class DiagramValidator(BaseValidator):
    """Unified diagram validator combining structural and business logic validation."""
    
    def __init__(self, api_key_service: Any | None = None):
        self.api_key_service = api_key_service
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform diagram validation using the domain compiler as source of truth."""
        if isinstance(target, DomainDiagram):
            self._validate_diagram(target, result)
        elif isinstance(target, dict):
            try:
                # Convert dict to DomainDiagram for validation
                diagram = DomainDiagram.model_validate(target)
                self._validate_diagram(diagram, result)
            except Exception as e:
                result.add_error(ValidationError(f"Invalid diagram format: {e!s}"))
        else:
            result.add_error(ValidationError("Target must be a DomainDiagram or dict"))
    
    def _validate_diagram(self, diagram: DomainDiagram, result: ValidationResult) -> None:
        """Validate a DomainDiagram object using the compiler.
        
        This is now a façade that delegates to the domain compiler for
        all validation logic, ensuring a single source of truth.
        """
        # Use the compiler for validation
        compilation_result = validate_via_compiler(diagram)
        
        # Convert compilation errors to validation errors
        for error in compilation_result.errors:
            result.add_error(error.to_validation_error())
        
        # Convert compilation warnings to validation warnings
        for warning in compilation_result.warnings:
            result.add_warning(warning.to_validation_warning())
        
        # Additional validations not covered by the compiler
        # (These are specific to runtime concerns like API keys)
        
        # Validate persons references
        person_ids = {person.id for person in diagram.persons} if diagram.persons else set()
        
        if diagram.nodes:
            for node in diagram.nodes:
                if node.type in ["person_job", "person_batch_job"] and node.data:
                    person_id = node.data.get("personId")
                    if person_id and person_id not in person_ids:
                        result.add_error(ValidationError(
                            f"Node '{node.id}' references non-existent person '{person_id}'"
                        ))
        
        # Validate API keys if service is available
        if self.api_key_service and diagram.persons:
            for person in diagram.persons:
                if person.api_key_id and not self.api_key_service.get_api_key(person.api_key_id):
                    result.add_error(ValidationError(
                        f"Person '{person.id}' references non-existent API key '{person.api_key_id}'"
                    ))


# Convenience methods for backward compatibility
def validate_or_raise(diagram: DomainDiagram | dict[str, Any], api_key_service: Any | None = None) -> None:
    """Validate diagram and raise ValidationError if invalid."""
    validator = DiagramValidator(api_key_service)
    result = validator.validate(diagram)
    if not result.is_valid:
        errors = [str(error) for error in result.errors]
        raise ValidationError("; ".join(errors))


def is_valid(diagram: DomainDiagram | dict[str, Any], api_key_service: Any | None = None) -> bool:
    """Check if diagram is valid."""
    validator = DiagramValidator(api_key_service)
    result = validator.validate(diagram)
    return result.is_valid