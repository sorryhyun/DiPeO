"""Validation domain service for business rule validation."""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from dipeo_domain.models import DomainDiagram, DomainPerson

from .errors import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
    InputValidationError,
    BatchValidationError,
)


class ValidationDomainService:
    """Centralized validation service for business rules."""

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Validate that all required fields are present and non-empty."""
        errors = []

        for field in required_fields:
            value = data.get(field)
            if value is None:
                errors.append(
                    InputValidationError(
                        field, None, f"Required field '{field}' is missing"
                    )
                )
            elif isinstance(value, str) and not value.strip():
                errors.append(
                    InputValidationError(
                        field, value, f"Required field '{field}' is empty"
                    )
                )

        if errors:
            raise BatchValidationError(errors)

    def validate_operation(self, operation: str, allowed_operations: List[str]) -> None:
        """Validate that an operation is allowed."""
        if operation not in allowed_operations:
            raise BusinessRuleViolationError(
                rule="allowed_operations",
                message=f"Operation '{operation}' is not allowed. Must be one of: {', '.join(allowed_operations)}",
                context={"operation": operation, "allowed": allowed_operations},
            )

    def validate_file_exists(self, file_path: str) -> None:
        """Validate that a file exists."""
        path = Path(file_path)
        if not path.exists():
            raise ResourceNotFoundError(
                "file", file_path, f"File '{file_path}' does not exist"
            )

    def validate_file_writable(self, file_path: str) -> None:
        """Validate that a file path is writable."""
        path = Path(file_path)
        parent = path.parent

        # Check if parent directory exists
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise BusinessRuleViolationError(
                    rule="file_writable",
                    message=f"Cannot create directory for file '{file_path}': {str(e)}",
                    context={"file_path": file_path},
                )

        # Check if we can write to the directory
        if not os.access(parent, os.W_OK):
            raise BusinessRuleViolationError(
                rule="file_writable",
                message=f"No write permission for directory '{parent}'",
                context={"directory": str(parent)},
            )

    def validate_person_exists(
        self, diagram: DomainDiagram, person_id: str
    ) -> DomainPerson:
        """Validate that a person exists in the diagram."""
        if not diagram.persons:
            raise ResourceNotFoundError(
                "person", person_id, "No persons defined in diagram"
            )

        person = next((p for p in diagram.persons if p.id == person_id), None)
        if not person:
            available_ids = [p.id for p in diagram.persons]
            raise ResourceNotFoundError(
                "person",
                person_id,
                f"Person '{person_id}' not found. Available persons: {', '.join(available_ids)}",
            )

        return person

    def validate_diagram_not_none(
        self, diagram: Optional[DomainDiagram], context: str = ""
    ) -> DomainDiagram:
        """Validate that a diagram is not None."""
        if diagram is None:
            raise ResourceNotFoundError(
                "diagram",
                "current",
                f"No diagram available{' for ' + context if context else ''}",
            )
        return diagram

    def validate_interactive_handler(
        self, handler: Optional[Any], context: str = ""
    ) -> Any:
        """Validate that an interactive handler is available."""
        if handler is None:
            raise BusinessRuleViolationError(
                rule="interactive_handler_required",
                message=f"Interactive handler required{' for ' + context if context else ''} but not available",
                context={"context": context},
            )
        return handler

    def validate_input_value(
        self, value: Any, expected_type: Optional[type] = None, context: str = ""
    ) -> Any:
        """Validate input value and optionally check its type."""
        if value is None:
            raise InputValidationError(
                "value",
                value,
                f"Input value cannot be None{' for ' + context if context else ''}",
            )

        if expected_type and not isinstance(value, expected_type):
            raise InputValidationError(
                "value",
                value,
                f"Expected {expected_type.__name__} but got {type(value).__name__}{' for ' + context if context else ''}",
            )

        return value

    def validate_db_operation_input(self, operation: str, value: Any) -> None:
        """Validate input for database operations."""
        if operation in ["write", "append"] and not value:
            raise BusinessRuleViolationError(
                rule="db_operation_input",
                message=f"Operation '{operation}' requires non-empty input value",
                context={"operation": operation, "value": value},
            )

    def validate_file_operation_params(
        self, data: Dict[str, Any]
    ) -> tuple[str, Optional[str]]:
        """Validate and extract file operation parameters."""
        file_path = data.get("filePath", "").strip()
        file_name = data.get("fileName", "").strip()

        if not file_path and not file_name:
            raise InputValidationError(
                "file_params",
                {"filePath": file_path, "fileName": file_name},
                "Either 'filePath' or 'fileName' must be provided",
            )

        return file_path, file_name

    def validate_batch_size(
        self, batch_size: int, min_size: int = 1, max_size: int = 1000
    ) -> None:
        """Validate batch size is within acceptable range."""
        if batch_size < min_size or batch_size > max_size:
            raise BusinessRuleViolationError(
                rule="batch_size_range",
                message=f"Batch size {batch_size} is out of range [{min_size}, {max_size}]",
                context={"batch_size": batch_size, "min": min_size, "max": max_size},
            )
