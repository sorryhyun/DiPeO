"""Base module for DiPeO core abstractions."""

from .exceptions import (
    ConfigurationError,
    DiPeOError,
    ExecutionError,
    ServiceError,
    ValidationError,
    APIKeyError,
    APIKeyNotFoundError,
    DependencyError,
    DiagramError,
    DiagramNotFoundError,
    ERROR_CODE_MAP,
    FileOperationError,
    InvalidDiagramError,
    LLMServiceError,
    MaxIterationsError,
    NodeExecutionError,
    TimeoutError,
    get_exception_by_code,
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
    # Execution errors
    "NodeExecutionError",
    "DependencyError",
    "MaxIterationsError",
    "TimeoutError",
    # Service errors
    "APIKeyError",
    "APIKeyNotFoundError",
    "LLMServiceError",
    # File errors
    "FileOperationError",
    # Diagram errors
    "DiagramError",
    "DiagramNotFoundError",
    "InvalidDiagramError",
    # Utilities
    "ERROR_CODE_MAP",
    "get_exception_by_code",
]
