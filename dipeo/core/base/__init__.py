"""Base module for DiPeO core abstractions."""

from .exceptions import (
    ConfigurationError,
    DiPeOError,
    ExecutionError,
    ServiceError,
    ValidationError,
)
from .protocols import (
    SupportsAPIKey,
    SupportsExecution,
    SupportsMemory,
)
from .service import BaseService
from .file_protocol import FileServiceProtocol

__all__ = [
    # Base classes
    "BaseService",
    # Exceptions
    "DiPeOError",
    "ValidationError",
    "ConfigurationError",
    "ServiceError",
    "ExecutionError",
    # Protocols
    "SupportsAPIKey",
    "SupportsExecution",
    "SupportsMemory",
    # New unified protocol
    "FileServiceProtocol",
]
