"""DiPeO Core - Core abstractions and base classes for DiPeO."""

from .base.exceptions import (
    ConfigurationError,
    DiPeOError,
    ExecutionError,
    ServiceError,
    ValidationError,
)
from .base.protocols import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
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
# Legacy ExecutionContext removed - use ApplicationExecutionContext instead
# UnifiedExecutionContext moved to application.compatibility for architectural compliance
from .errors.taxonomy import (
    APIKeyError,
    APIKeyNotFoundError,
    DependencyError,
    DiagramError,
    DiagramNotFoundError,
    FileOperationError,
    InvalidDiagramError,
    LLMServiceError,
    MaxIterationsError,
    NodeExecutionError,
    TimeoutError,
)
from .execution.executor import BaseExecutor
from .execution.handlers import (
    BaseNodeHandler,
    HandlerRegistry,
    get_global_registry,
    register_handler,
)
from .execution.types import (
    ExecutionOptions,
    NodeDefinition,
    NodeHandler,
)
from .types import (
    Error,
    JsonDict,
    JsonList,
    JsonValue,
    Result,
)
from .utils import (
    # Error handling utilities
    ErrorResponse,
    handle_exceptions,
    handle_file_operation,
    handle_api_errors,
    retry_with_backoff,
    safe_parse,
    format_error_response,
    # Dynamic registry utilities
    DynamicRegistry,
    TypedDynamicRegistry,
    # Conversation detection utilities
    is_conversation,
    has_nested_conversation,
    contains_conversation,
)

__version__ = "0.1.0"

__all__ = [
    # Base exceptions
    "DiPeOError",
    "ServiceError",
    "ExecutionError",
    "ValidationError",
    "ConfigurationError",
    # Protocols
    "SupportsAPIKey",
    "SupportsDiagram",
    "SupportsExecution",
    "SupportsFile",
    "SupportsLLM",
    "SupportsMemory",
    "SupportsNotion",
    # Base classes
    "BaseService",
    "BaseExecutor",
    "BaseNodeHandler",
    # Context (UnifiedExecutionContext moved to application.compatibility)
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
    # Handler registration
    "HandlerRegistry",
    "get_global_registry",
    "register_handler",
    # Execution types
    "ExecutionOptions",
    "NodeDefinition",
    "NodeHandler",
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