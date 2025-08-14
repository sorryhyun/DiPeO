"""Application execution services."""

from .handler_factory import (
    HandlerRegistry,
    get_global_registry,
    register_handler,
)
from .handler_base import TypedNodeHandler, EnvelopeNodeHandler
from dipeo.diagram_generated import ExecutionOptions
from dipeo.core.execution.execution_context import ExecutionContext
from .typed_engine import TypedExecutionEngine
from .use_cases import ExecuteDiagramUseCase

__all__ = [
    "TypedExecutionEngine",
    # Use cases
    "ExecuteDiagramUseCase",
    # Types
    "ExecutionContext",
    "ExecutionOptions",
    # Handlers
    "TypedNodeHandler",
    "EnvelopeNodeHandler",  # Backward compatibility alias
    "HandlerRegistry",
    "register_handler",
    "get_global_registry",
]