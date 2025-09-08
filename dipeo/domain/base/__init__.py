"""Base module for DiPeO domain abstractions."""

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
    StorageError,
    TimeoutError,
    ValidationError,
    get_exception_by_code,
)
from .validator import BaseValidator

__all__ = [
    # Utilities
    "ERROR_CODE_MAP",
    # Service errors
    "APIKeyError",
    "APIKeyNotFoundError",
    # Base classes
    "BaseValidator",
    "ConfigurationError",
    "DependencyError",
    # Exceptions
    "DiPeOError",
    # Diagram errors
    "DiagramError",
    "DiagramNotFoundError",
    "ExecutionError",
    # File errors
    "FileOperationError",
    "InvalidDiagramError",
    "LLMServiceError",
    "MaxIterationsError",
    # Execution errors
    "NodeExecutionError",
    "ServiceError",
    # Storage errors
    "StorageError",
    "TimeoutError",
    "ValidationError",
    "get_exception_by_code",
]
