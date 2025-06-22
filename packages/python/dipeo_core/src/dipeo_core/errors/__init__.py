"""Error module for DiPeO core."""

from .taxonomy import (
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

__all__ = [
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