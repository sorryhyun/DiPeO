"""Core execution engine components."""

from typing import TYPE_CHECKING

# Lazy imports to avoid circular dependencies
# The engine module should not eagerly import everything at startup

if TYPE_CHECKING:
    from dipeo.application.execution.engine.context import TypedExecutionContext
    from dipeo.application.execution.engine.dependency_tracker import DependencyTracker
    from dipeo.application.execution.engine.helpers import (
        extract_llm_usage,
        format_node_result,
        get_handler,
    )
    from dipeo.application.execution.engine.node_executor import execute_single_node
    from dipeo.application.execution.engine.ready_queue import ReadyQueue
    from dipeo.application.execution.engine.reporting import calculate_progress
    from dipeo.application.execution.engine.request import ExecutionRequest
    from dipeo.application.execution.engine.scheduler import NodeScheduler
    from dipeo.application.execution.engine.typed_engine import TypedExecutionEngine

__all__ = [
    "DependencyTracker",
    "ExecutionRequest",
    "NodeScheduler",
    "ReadyQueue",
    "TypedExecutionContext",
    "TypedExecutionEngine",
    "calculate_progress",
    "execute_single_node",
    "extract_llm_usage",
    "format_node_result",
    "get_handler",
]


def __getattr__(name: str):
    """Lazy import mechanism to avoid circular dependencies."""
    if name == "TypedExecutionEngine":
        from dipeo.application.execution.engine.typed_engine import TypedExecutionEngine

        return TypedExecutionEngine
    elif name == "TypedExecutionContext":
        from dipeo.application.execution.engine.context import TypedExecutionContext

        return TypedExecutionContext
    elif name == "NodeScheduler":
        from dipeo.application.execution.engine.scheduler import NodeScheduler

        return NodeScheduler
    elif name == "DependencyTracker":
        from dipeo.application.execution.engine.dependency_tracker import DependencyTracker

        return DependencyTracker
    elif name == "ReadyQueue":
        from dipeo.application.execution.engine.ready_queue import ReadyQueue

        return ReadyQueue
    elif name == "ExecutionRequest":
        from dipeo.application.execution.engine.request import ExecutionRequest

        return ExecutionRequest
    elif name == "execute_single_node":
        from dipeo.application.execution.engine.node_executor import execute_single_node

        return execute_single_node
    elif name == "extract_llm_usage":
        from dipeo.application.execution.engine.helpers import extract_llm_usage

        return extract_llm_usage
    elif name == "format_node_result":
        from dipeo.application.execution.engine.helpers import format_node_result

        return format_node_result
    elif name == "get_handler":
        from dipeo.application.execution.engine.helpers import get_handler

        return get_handler
    elif name == "calculate_progress":
        from dipeo.application.execution.engine.reporting import calculate_progress

        return calculate_progress
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
