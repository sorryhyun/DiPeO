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
from .context import ExecutionContext
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
    RuntimeContext,
)
from .types import Error, JsonDict, JsonList, JsonValue, Result
from .utils import (
    camel_to_snake,
    ensure_list,
    get_timestamp,
    merge_dicts,
    safe_json_dumps,
    safe_json_loads,
    snake_to_camel,
    truncate_string,
)

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "BaseService",
    "BaseExecutor",
    "BaseNodeHandler",
    # Core types
    "ExecutionContext",
    "RuntimeContext",
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
]
