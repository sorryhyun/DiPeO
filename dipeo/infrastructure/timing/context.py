import functools
import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from typing import Any, ParamSpec, TypeVar

from dipeo.infrastructure.timing.collector import timing_collector

logger = logging.getLogger("dipeo.timing")

P = ParamSpec("P")
T = TypeVar("T")

# ============================================================================
# Context Managers (for fine-grained timing within functions)
# ============================================================================


@contextmanager
def time_phase(exec_id: str, node_id: str, phase: str, **metadata: Any):
    """Context manager for timing synchronous phases.

    Usage:
        with time_phase(exec_id, node_id, "input_extraction"):
            result = extract_inputs(data)
    """
    if not exec_id:
        yield
        return

    start = time.perf_counter_ns()
    exception_occurred = False

    try:
        yield
    except Exception:
        exception_occurred = True
        raise
    finally:
        dur_ms = (time.perf_counter_ns() - start) / 1_000_000
        dur_ms_int = round(dur_ms)
        timing_collector.record(exec_id, node_id, phase, dur_ms_int, **metadata)

        # Only log timing entries with non-zero duration
        if logger.isEnabledFor(logging.DEBUG) and dur_ms_int > 0:
            logger.debug(
                "exec_id=%s node_id=%s phase=%s dur_ms=%dms status=%s",
                exec_id,
                node_id,
                phase,
                dur_ms_int,
                "error" if exception_occurred else "ok",
                extra={"timing": metadata},
            )


@asynccontextmanager
async def atime_phase(exec_id: str, node_id: str, phase: str, **metadata: Any):
    """Async context manager for timing async phases.

    Usage:
        async with atime_phase(exec_id, node_id, "llm_completion", model="gpt-4"):
            result = await llm_service.complete(...)
    """
    with time_phase(exec_id, node_id, phase, **metadata):
        yield


# ============================================================================
# Decorators (for timing entire functions - cleaner syntax)
# ============================================================================


def timed(
    phase: str | None = None, node_id_param: str = "node_id", exec_id_param: str = "execution_id"
):
    """Decorator for timing synchronous functions.

    Args:
        phase: Phase name (defaults to function name)
        node_id_param: Parameter name for node_id (default: "node_id")
        exec_id_param: Parameter name for execution_id (default: "execution_id")

    Usage:
        @timed("input_extraction")
        def extract_inputs(self, data, execution_id, node_id):
            ...

        # Or use defaults:
        @timed()
        def build_prompt(self, execution_id, node_id, ...):
            # Phase name = "build_prompt"
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        phase_name = phase or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Extract exec_id and node_id from kwargs or bound arguments
            import inspect

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            exec_id = bound.arguments.get(exec_id_param, "")
            node_id = bound.arguments.get(node_id_param, "unknown")

            with time_phase(exec_id, node_id, phase_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def atimed(
    phase: str | None = None, node_id_param: str = "node_id", exec_id_param: str = "execution_id"
):
    """Decorator for timing async functions.

    Usage:
        @atimed("memory_selection")
        async def select_memories(self, execution_id, node_id, ...):
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        phase_name = phase or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import inspect

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            exec_id = bound.arguments.get(exec_id_param, "")
            node_id = bound.arguments.get(node_id_param, "unknown")

            async with atime_phase(exec_id, node_id, phase_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
