"""Application bootstrap module for dependency injection."""

from .containers import (
    ApplicationContainer,
    Container,
    CoreContainer,
    InfrastructureContainer,
    init_resources,
    shutdown_resources,
)

__all__ = [
    "ApplicationContainer",
    "Container",
    "CoreContainer",
    "InfrastructureContainer",
    "init_resources",
    "shutdown_resources",
]