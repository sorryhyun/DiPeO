"""Execution module for DiPeO core."""

from .executor import BaseExecutor, ExecutorInterface
from .handlers import (
    BaseNodeHandler,
    HandlerRegistry,
    create_node_output,
    get_global_registry,
    register_handler,
)
from .types import (
    ExecutionContext,
    ExecutionOptions,
    NodeDefinition,
    NodeHandler,
    RuntimeContext,
    execution_to_runtime_context,
    runtime_to_execution_context,
)

__all__ = [
    # Types
    "ExecutionContext",
    "RuntimeContext",
    "ExecutionOptions",
    "NodeDefinition",
    "NodeHandler",
    # Executors
    "BaseExecutor",
    "ExecutorInterface",
    # Handlers
    "BaseNodeHandler",
    "HandlerRegistry",
    "register_handler",
    "get_global_registry",
    "create_node_output",
    # Utilities
    "runtime_to_execution_context",
    "execution_to_runtime_context",
]