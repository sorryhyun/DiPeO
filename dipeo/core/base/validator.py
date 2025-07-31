"""Base validator for the core layer."""

import os
from pathlib import Path
from typing import Any

from .exceptions import ValidationError


class BaseValidator:
    
    def validate_required_fields(
        self, data: dict[str, Any], required_fields: list[str]
    ) -> None:
        errors = []

        for field in required_fields:
            value = data.get(field)
            if value is None:
                errors.append(f"Required field '{field}' is missing")
            elif isinstance(value, str) and not value.strip():
                errors.append(f"Required field '{field}' is empty")

        if errors:
            raise ValidationError(
                "Validation failed: " + "; ".join(errors),
                details={"errors": errors, "fields": required_fields}
            )

    def validate_operation(self, operation: str, allowed_operations: list[str]) -> None:
        if operation not in allowed_operations:
            raise ValidationError(
                f"Operation '{operation}' is not allowed. Must be one of: {', '.join(allowed_operations)}",
                details={"operation": operation, "allowed": allowed_operations}
            )

    def validate_file_exists(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(
                f"File '{file_path}' does not exist",
                details={"file_path": file_path}
            )

    def validate_file_writable(self, file_path: str) -> None:
        path = Path(file_path)
        parent = path.parent

        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(
                    f"Cannot create directory for file '{file_path}': {e!s}",
                    details={"file_path": file_path, "error": str(e)}
                )
        if not os.access(parent, os.W_OK):
            raise ValidationError(
                f"No write permission for directory '{parent}'",
                details={"directory": str(parent)}
            )

    def validate_input_value(
        self, value: Any, expected_type: type | None = None, context: str = ""
    ) -> Any:
        if value is None:
            raise ValidationError(
                f"Input value cannot be None{' for ' + context if context else ''}",
                details={"context": context}
            )

        if expected_type and not isinstance(value, expected_type):
            raise ValidationError(
                f"Expected {expected_type.__name__} but got {type(value).__name__}{' for ' + context if context else ''}",
                details={"expected": expected_type.__name__, "actual": type(value).__name__, "context": context}
            )

        return value

    def validate_batch_size(
        self, batch_size: int, min_size: int = 1, max_size: int = 1000
    ) -> None:
        if batch_size < min_size or batch_size > max_size:
            raise ValidationError(
                f"Batch size {batch_size} is out of range [{min_size}, {max_size}]",
                details={"batch_size": batch_size, "min": min_size, "max": max_size}
            )