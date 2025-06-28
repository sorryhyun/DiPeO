"""Application orchestration layer."""

# Avoid circular imports by deferring imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app_context import AppContext
    from .execution_context import ExecutionContext

__all__ = [
    "AppContext",
    "ExecutionContext",
    "get_app_context",
    "lifespan",
]


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "AppContext":
        from .app_context import AppContext

        return AppContext
    if name == "ExecutionContext":
        from .execution_context import ExecutionContext

        return ExecutionContext
    if name == "get_app_context":
        from .app_context import get_app_context

        return get_app_context
    if name == "lifespan":
        from .app_context import lifespan

        return lifespan
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
