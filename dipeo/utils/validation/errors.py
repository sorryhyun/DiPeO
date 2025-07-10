"""Validation error types."""

from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Base validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ResourceNotFoundError(ValidationError):
    """Error when a required resource is not found."""

    def __init__(
        self, resource_type: str, resource_id: str, message: Optional[str] = None
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        msg = message or f"{resource_type} '{resource_id}' not found"
        super().__init__(
            msg, {"resource_type": resource_type, "resource_id": resource_id}
        )


class BusinessRuleViolationError(ValidationError):
    """Error when a business rule is violated."""

    def __init__(
        self, rule: str, message: str, context: Optional[Dict[str, Any]] = None
    ):
        self.rule = rule
        details = {"rule": rule}
        if context:
            details.update(context)
        super().__init__(message, details)


class InputValidationError(ValidationError):
    """Error for invalid input data."""

    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        super().__init__(message, {"field": field, "value": value})


class BatchValidationError(ValidationError):
    """Error containing multiple validation errors."""

    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        messages = [str(e) for e in errors]
        super().__init__(f"Multiple validation errors: {'; '.join(messages)}")
        self.details = {"errors": [e.details for e in errors]}
