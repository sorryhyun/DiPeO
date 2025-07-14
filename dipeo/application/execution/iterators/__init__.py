"""Execution iterators for step-by-step diagram processing."""

# Compatibility imports for migration
from .simple_iterator import SimpleAsyncIterator, SimpleExecutionIterator, ExecutionStep
from typing import TYPE_CHECKING, Callable, Any
if TYPE_CHECKING:
    from dipeo.models import ExecutableNode


# Adapter classes for compatibility
class ExecutionIterator(SimpleExecutionIterator):
    """Compatibility wrapper for SimpleExecutionIterator."""
    pass


class AsyncExecutionIterator(SimpleAsyncIterator):
    """Compatibility wrapper for SimpleAsyncIterator."""
    
    def __init__(
        self,
        stateful_execution: Any,  # Will be SimpleExecution or TypedStatefulExecution
        max_parallel_nodes: int = 10,
        node_executor: Callable[["ExecutableNode"], Any] | None = None,
        node_ready_poll_interval: float = 0.01,
        max_poll_retries: int = 100
    ):
        # Just pass the execution and node_executor to the simple iterator
        super().__init__(stateful_execution, node_executor)
        self._current_step = 0
        self._running_tasks = []
        self._execution = stateful_execution
    
    def get_progress(self) -> dict[str, Any]:
        """Get execution progress information."""
        progress = self._execution.get_progress()
        progress.update({
            "current_step": self._current_step,
            "is_cancelled": self._cancelled,
            "running_tasks": len(self._running_tasks)
        })
        return progress


__all__ = ["AsyncExecutionIterator", "ExecutionIterator", "ExecutionStep"]