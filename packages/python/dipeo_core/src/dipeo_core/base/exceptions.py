"""Base exception classes for DiPeO core."""

from typing import Any, Optional


class DiPeOError(Exception):
    """Base exception class for all DiPeO errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = self.__class__.__name__

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ValidationError(DiPeOError):
    """Raised when input validation fails."""

    error_code = "VALIDATION_ERROR"


class ConfigurationError(DiPeOError):
    """Raised when configuration is invalid."""

    error_code = "CONFIGURATION_ERROR"


class ServiceError(DiPeOError):
    """Base class for service-related errors."""

    error_code = "SERVICE_ERROR"


class ExecutionError(DiPeOError):
    """Base class for execution-related errors."""

    error_code = "EXECUTION_ERROR"