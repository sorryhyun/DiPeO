"""DiPeO Core - DEPRECATED: Use 'dipeo.core' or import from 'dipeo' directly.

This module is deprecated and will be removed in a future version.
Please update your imports:
  - Change 'from dipeo_core import X' to 'from dipeo.core import X'
  - Or preferably 'from dipeo import X' for commonly used exports
"""

import warnings

warnings.warn(
    "The 'dipeo_core' package is deprecated. "
    "Please use 'from dipeo.core import ...' or 'from dipeo import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the new location for backward compatibility
from dipeo.core.base.exceptions import (
    ConfigurationError,
    DiPeOError,
    ExecutionError,
    ServiceError,
    ValidationError,
)
from dipeo.core.base.protocols import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)
from dipeo.core.base.service import BaseService
from dipeo.core.constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEOUT,
    MAX_EXECUTION_TIMEOUT,
    MAX_PAGE_SIZE,
    MAX_RETRIES,
    VALID_LLM_SERVICES,
    normalize_service_name,
)
from dipeo.core.unified_context import UnifiedExecutionContext
from dipeo.core.errors.taxonomy import (
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
from dipeo.core.execution.executor import BaseExecutor
from dipeo.core.execution.handlers import (
    BaseNodeHandler,
    HandlerRegistry,
    get_global_registry,
    register_handler,
)
from dipeo.core.execution.types import (
    ExecutionOptions,
    NodeDefinition,
    NodeHandler,
)
from dipeo.core.types import (
    Error,
    JsonDict,
    JsonList,
    JsonValue,
    Result,
)
from dipeo.core.utils import (
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

# Re-export submodules
from dipeo.core import base
from dipeo.core import constants
from dipeo.core import errors
from dipeo.core import execution
from dipeo.core import types
from dipeo.core import unified_context
from dipeo.core import utils

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
    # Context
    "UnifiedExecutionContext",
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
    # Submodules
    "base",
    "constants",
    "errors",
    "execution",
    "types",
    "unified_context",
    "utils",
]