"""Base module for DiPeO core abstractions."""

from .exceptions import (
    ERROR_CODE_MAP,
    APIKeyError,
    APIKeyNotFoundError,
    ConfigurationError,
    DependencyError,
    DiagramError,
    DiagramNotFoundError,
    DiPeOError,
    ExecutionError,
    FileOperationError,
    InvalidDiagramError,
    LLMServiceError,
    MaxIterationsError,
    NodeExecutionError,
    ServiceError,
    TimeoutError,
    ValidationError,
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
