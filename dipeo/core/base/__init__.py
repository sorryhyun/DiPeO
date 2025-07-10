"""Base module for DiPeO core abstractions."""

from .exceptions import (
    ConfigurationError,
    DiPeOError,
    ExecutionError,
    ServiceError,
    ValidationError,
)
from .service import BaseService

__all__ = [
    # Base classes
    "BaseService",
    # Exceptions
    "DiPeOError",
    "ValidationError",
    "ConfigurationError",
    "ServiceError",
    "ExecutionError",
]
