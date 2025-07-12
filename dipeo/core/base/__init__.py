"""Base module for DiPeO core abstractions."""

from .exceptions import (
    ConfigurationError,
    DiPeOError,
    ExecutionError,
    ServiceError,
    ValidationError,
)
from .service import BaseService
from .validator import BaseValidator

__all__ = [
    # Base classes
    "BaseService",
    "BaseValidator",
    # Exceptions
    "DiPeOError",
    "ValidationError",
    "ConfigurationError",
    "ServiceError",
    "ExecutionError",
]
