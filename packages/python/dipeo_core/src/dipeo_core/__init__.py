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
from .execution.handlers import BaseNodeHandler, HandlerRegistry, register_handler, get_global_registry
from .execution.types import (
    ExecutionContext,
    ExecutionOptions,
    NodeDefinition,
    NodeHandler,
    RuntimeContext,
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
]