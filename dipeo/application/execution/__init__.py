"""Application execution services."""

from .handler_factory import (
    HandlerRegistry,
    get_global_registry,
    register_handler,
)
from .types import (
    ExecutionContext,
    ExecutionOptions,
    TypedNodeHandler,
)
from .execution_runtime import ExecutionRuntime
from .use_cases import ExecuteDiagramUseCase

# Compatibility imports for migration
from .execution_runtime import ExecutionRuntime as SimpleExecution
from .execution_runtime import ExecutionRuntime as TypedStatefulExecution
from .execution_runtime import ExecutionRuntime as StatefulExecution

__all__ = [
    "ExecutionRuntime",
    # Use cases
    "ExecuteDiagramUseCase",
    # Types
    "ExecutionContext",
    "ExecutionOptions",
    # Handlers
    "TypedNodeHandler",
    "HandlerRegistry",
    "register_handler",
    "get_global_registry",
    # Compatibility exports during migration
    "SimpleExecution",
    "TypedStatefulExecution",
    "StatefulExecution",
]