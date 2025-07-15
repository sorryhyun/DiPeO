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
    # Dynamic registry utilities
    DynamicRegistry,
    # Error handling utilities
    ErrorResponse,
    TypedDynamicRegistry,
    contains_conversation,
    format_error_response,
    handle_api_errors,
    handle_exceptions,
    handle_file_operation,
    has_nested_conversation,
    # Conversation detection utilities
    is_conversation,
    retry_with_backoff,
    safe_parse,
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
    "TimeoutError",
    # Common types
    "Result",
    "Error",
    "JsonDict",
    "JsonList",
    "JsonValue",
    # Utilities
    # Error handling utilities
    "ErrorResponse",
    "handle_exceptions",
    "handle_file_operation",
    "handle_api_errors",
    "retry_with_backoff",
    "safe_parse",
    "format_error_response",
    # Dynamic registry utilities
    "DynamicRegistry",
    "TypedDynamicRegistry",
    # Conversation detection utilities
    "is_conversation",
    "has_nested_conversation",
    "contains_conversation",
]