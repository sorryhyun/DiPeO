"""Application execution services."""

from .handler_factory import (
    HandlerRegistry,
    get_global_registry,
    register_handler,
)
from .types import TypedNodeHandler
from .use_cases import ExecuteDiagramUseCase
from .context import UnifiedExecutionContext
from .types import (
    ExecutionContext,
    ExecutionOptions,
)

__all__ = [
    # Use cases
    "ExecuteDiagramUseCase",
    # Context
    "UnifiedExecutionContext",
    # Types
    "ExecutionContext",
    "ExecutionOptions",
    # Handlers
    "TypedNodeHandler",
    "HandlerRegistry",
    "register_handler",
    "get_global_registry",
]