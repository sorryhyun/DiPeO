"""DiPeO Dependency Injection Container."""

from .container import (
    Container,
    init_resources,
    shutdown_resources,
    validate_protocol_compliance,
)

__all__ = [
    "Container",
    "init_resources",
    "shutdown_resources",
    "validate_protocol_compliance",
]