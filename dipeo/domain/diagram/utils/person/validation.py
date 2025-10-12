"""Person validation utilities.

This module provides validation logic for person-related operations:
- Validating person references in nodes
- Validating person API key references
"""

from __future__ import annotations

from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import ValidationResult


class PersonValidator:
    """Validates person-related constraints in diagrams."""

    @staticmethod
    def validate_person_references(diagram: DomainDiagram, result: ValidationResult) -> None:
        """Validate that all person references in nodes point to existing persons.

        Args:
            diagram: The diagram to validate
            result: ValidationResult to accumulate errors
        """
        person_ids = {person.id for person in diagram.persons} if diagram.persons else set()

        if diagram.nodes:
            for node in diagram.nodes:
                if node.type in ["person_job", "person_batch_job"] and node.data:
                    person_id = node.data.get("personId")
                    if person_id and person_id not in person_ids:
                        result.add_error(
                            ValidationError(
                                f"Node '{node.id}' references non-existent person '{person_id}'"
                            )
                        )

    @staticmethod
    def validate_person_api_keys(
        diagram: DomainDiagram, api_key_service: Any, result: ValidationResult
    ) -> None:
        """Validate that all person API key references exist in the service.

        Args:
            diagram: The diagram to validate
            api_key_service: Service to check API key existence
            result: ValidationResult to accumulate errors
        """
        if diagram.persons:
            for person in diagram.persons:
                if person.api_key_id and not api_key_service.get_api_key(person.api_key_id):
                    result.add_error(
                        ValidationError(
                            f"Person '{person.id}' references non-existent API key '{person.api_key_id}'"
                        )
                    )
