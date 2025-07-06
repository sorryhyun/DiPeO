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
# Legacy ExecutionContext removed - use UnifiedExecutionContext instead
from .unified_context import UnifiedExecutionContext
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

# Type aliases removed - use UnifiedExecutionContext directly
from .types import Error, JsonDict, JsonList, JsonValue, Result
# Import utility functions directly from utils.py
# We need to use importlib to specifically load the .py file
# because Python prioritizes the utils/ package over utils.py
import importlib.util
import os
_utils_spec = importlib.util.spec_from_file_location(
    "dipeo_core_utils_file", 
    os.path.join(os.path.dirname(__file__), "utils.py")
)
_utils_file = importlib.util.module_from_spec(_utils_spec)
_utils_spec.loader.exec_module(_utils_file)

# Re-export the functions
camel_to_snake = _utils_file.camel_to_snake
ensure_list = _utils_file.ensure_list
get_timestamp = _utils_file.get_timestamp
merge_dicts = _utils_file.merge_dicts
safe_json_dumps = _utils_file.safe_json_dumps
safe_json_loads = _utils_file.safe_json_loads
snake_to_camel = _utils_file.snake_to_camel
truncate_string = _utils_file.truncate_string
from .utils.error_handling import (
    ErrorResponse,
    format_error_response,
    handle_api_errors,
    handle_exceptions,
    handle_file_operation,
    retry_with_backoff,
    safe_parse,
)
from .utils.dynamic_registry import DynamicRegistry, TypedDynamicRegistry

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "BaseService",
    "BaseExecutor",
    "BaseNodeHandler",
    # Core types
    "UnifiedExecutionContext",
    "ExecutionOptions",
    "NodeDefinition",
    "NodeHandler",
    # Shared types
    "Result",
    "Error",
    "JsonDict",
    "JsonList",
    "JsonValue",
    # Base exceptions
    "DiPeOError",
    "ValidationError",
    "ConfigurationError",
    "ServiceError",
    "ExecutionError",
    # Specific exceptions
    "NodeExecutionError",
    "DependencyError",
    "MaxIterationsError",
    "TimeoutError",
    "APIKeyError",
    "APIKeyNotFoundError",
    "LLMServiceError",
    "FileOperationError",
    "DiagramError",
    "DiagramNotFoundError",
    "InvalidDiagramError",
    # Protocols
    "SupportsAPIKey",
    "SupportsDiagram",
    "SupportsExecution",
    "SupportsFile",
    "SupportsLLM",
    "SupportsMemory",
    "SupportsNotion",
    # Utilities
    "HandlerRegistry",
    "register_handler",
    "get_global_registry",
    "ensure_list",
    "safe_json_loads",
    "safe_json_dumps",
    "get_timestamp",
    "truncate_string",
    "snake_to_camel",
    "camel_to_snake",
    "merge_dicts",
    # Constants
    "VALID_LLM_SERVICES",
    "normalize_service_name",
    "DEFAULT_TIMEOUT",
    "MAX_EXECUTION_TIMEOUT",
    "MAX_RETRIES",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
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
]
