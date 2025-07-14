"""Application orchestration layer."""

# Avoid circular imports by deferring imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app_context import get_container, initialize_container
    from .container import ServerContainer

__all__ = [
    "ServerContainer",
    "get_container",
    "initialize_container",
]


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "get_container":
        from .app_context import get_container

        return get_container
    if name == "initialize_container":
        from .app_context import initialize_container

        return initialize_container
    if name == "ServerContainer":
        from .container import ServerContainer

        return ServerContainer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
