"""Application execution services."""

from .handler_factory import (
    HandlerRegistry,
    get_global_registry,
    register_handler,
)
from .handler_base import TypedNodeHandler
from dipeo.diagram_generated import ExecutionOptions
from dipeo.core.dynamic.execution_context import ExecutionContext
from .execution_runtime import ExecutionRuntime
from .engine import TypedExecutionEngine
from .use_cases import ExecuteDiagramUseCase

# Compatibility imports for migration
from .execution_runtime import ExecutionRuntime as SimpleExecution
from .execution_runtime import ExecutionRuntime as TypedStatefulExecution
from .execution_runtime import ExecutionRuntime as StatefulExecution

__all__ = [
    "ExecutionRuntime",
    "TypedExecutionEngine",
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