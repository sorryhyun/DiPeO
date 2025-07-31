"""DiPeO Dependency Injection Container."""

from .containers import (
    Container,
    init_resources,
    shutdown_resources,
)

__all__ = [
    "Container",
    "init_resources",
    "shutdown_resources",
]