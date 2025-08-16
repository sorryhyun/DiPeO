"""DiPeO Core - Core abstractions and base classes for DiPeO."""

# use ApplicationExecutionContext
from .base.exceptions import (
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
)
from .base.service import BaseService
from .constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEOUT,
    MAX_EXECUTION_TIMEOUT,
    MAX_PAGE_SIZE,
    MAX_RETRIES,
    VALID_LLM_SERVICES,
    normalize_service_name,
)

# Execution framework has been moved to application layer
# Import from dipeo.application instead
from .type_defs import (
    Error,
    JsonDict,
    JsonList,
    JsonValue,
    Result,
)
from .utils import (
    # Conversation detection utilities
    contains_conversation,
    has_nested_conversation,
    is_conversation,
)

__version__ = "0.1.0"

__all__ = [
    # Base exceptions
    "DiPeOError",
    "ServiceError",
    "ExecutionError",
    "ValidationError",
    "ConfigurationError",
    # Base classes
    "BaseService",
    # Constants
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_TIMEOUT",
    "MAX_EXECUTION_TIMEOUT",
    "MAX_PAGE_SIZE",
    "MAX_RETRIES",
    "VALID_LLM_SERVICES",
    "normalize_service_name",
    # Error taxonomy
    "APIKeyError",
    "APIKeyNotFoundError",
    "DependencyError",
    "DiagramError",
    "DiagramNotFoundError",
    "FileOperationError",
    "InvalidDiagramError",
    "LLMServiceError",
    "MaxIterationsError",
    "NodeExecutionError",
    "StorageError",
    "TimeoutError",
    # Common types
    "Result",
    "Error",
    "JsonDict",
    "JsonList",
    "JsonValue",
    # Utilities
    # Conversation detection utilities
    "is_conversation",
    "has_nested_conversation",
    "contains_conversation",
]