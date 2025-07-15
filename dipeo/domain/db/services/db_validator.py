# Database operation validation service

from typing import Any

from dipeo.core.base import BaseValidator, ValidationError


class DBValidator(BaseValidator):
    """Validates database operations."""
    
    ALLOWED_OPERATIONS = ["prompt", "read", "write", "append"]
    
    def validate_db_operation_input(self, operation: str, value: Any) -> None:
        """Validate input for database operations."""
        if operation in ["write", "append"] and not value:
            raise ValidationError(
                f"Operation '{operation}' requires non-empty input value",
                details={"operation": operation, "value": value}
            )