"""Execution module for DiPeO core."""

from .executor import BaseExecutor, ExecutorInterface
from .handlers import (
    BaseNodeHandler,
    HandlerRegistry,
    get_global_registry,
    register_handler,
    create_node_output,
)
from .types import (
    ExecutionContext,
    ExecutionOptions,
    NodeDefinition,
    NodeHandler,
)

__all__ = [
    # Types
    "ExecutionContext",
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
]
