"""Application bootstrap module for dependency injection."""

from .containers import (
    ApplicationContainer,
    Container,
    InfrastructureContainer,
    init_resources,
    shutdown_resources,
)

__all__ = [
    "ApplicationContainer",
    "Container",
    "InfrastructureContainer",
    "init_resources",
    "shutdown_resources",
]
