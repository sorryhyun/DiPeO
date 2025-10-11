"""Business validation rules for diagrams.

This module contains domain-specific business validation logic, separate from
structural validation performed by the compiler.

Business validation includes:
- Person reference validation (person nodes reference valid persons)
- API key validation (persons reference valid API keys)
- Other domain-specific business rules

Structural validation (schema, node types, connections) is handled by
the compilation phases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import ValidationResult
from dipeo.domain.diagram.utils import PersonValidator

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram


class PersonReferenceValidator:
    """Validates that person_job and person_batch_job nodes reference valid persons."""

    def validate(self, diagram: DomainDiagram) -> list[ValidationError]:
        """Validate person references in diagram nodes.

        Args:
            diagram: The diagram to validate

        Returns:
            List of validation errors (empty if valid)
        """
        result = ValidationResult()
        PersonValidator.validate_person_references(diagram, result)
        return result.errors


class APIKeyValidator:
    """Validates that persons reference valid API keys."""

    def __init__(self, api_key_service: Any | None = None):
        """Initialize the validator with an API key service.

        Args:
            api_key_service: Service for looking up API keys
        """
        self.api_key_service = api_key_service

    def validate(self, diagram: DomainDiagram) -> list[ValidationError]:
        """Validate API key references in diagram persons.

        Args:
            diagram: The diagram to validate

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.api_key_service:
            return []

        result = ValidationResult()
        PersonValidator.validate_person_api_keys(diagram, self.api_key_service, result)
        return result.errors


class BusinessValidatorRegistry:
    """Registry for business validators with optional dependencies."""

    def __init__(self, api_key_service: Any | None = None):
        """Initialize the registry with optional dependencies.

        Args:
            api_key_service: Optional API key service for API key validation
        """
        self.validators: list[Any] = [
            PersonReferenceValidator(),
        ]

        if api_key_service:
            self.validators.append(APIKeyValidator(api_key_service))

    def validate(self, diagram: DomainDiagram) -> list[ValidationError]:
        """Run all registered business validators.

        Args:
            diagram: The diagram to validate

        Returns:
            List of all validation errors from all validators
        """
        all_errors = []

        for validator in self.validators:
            errors = validator.validate(diagram)
            all_errors.extend(errors)

        return all_errors
