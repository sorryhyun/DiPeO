"""Lifecycle protocol for services with initialization and shutdown.

This module defines a type-safe protocol for services that require
lifecycle management, replacing fragile hasattr() checks with
proper isinstance() type checking.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Lifecycle(Protocol):
    """Protocol for services that require lifecycle management.

    Services implementing this protocol can perform initialization
    and cleanup operations in a type-safe manner.
    """

    async def initialize(self) -> None:
        """Initialize the service.

        This method is called during service startup to perform
        any necessary initialization such as:
        - Establishing connections
        - Loading configuration
        - Warming up caches
        - Registering handlers
        """
        ...

    async def shutdown(self) -> None:
        """Shutdown the service gracefully.

        This method is called during service shutdown to perform
        cleanup operations such as:
        - Closing connections
        - Flushing buffers
        - Releasing resources
        - Saving state
        """
        ...


@runtime_checkable
class InitializeOnly(Protocol):
    """Protocol for services that only require initialization."""

    async def initialize(self) -> None:
        """Initialize the service."""
        ...


@runtime_checkable
class ShutdownOnly(Protocol):
    """Protocol for services that only require shutdown."""

    async def shutdown(self) -> None:
        """Shutdown the service gracefully."""
        ...


async def initialize_service(service: object) -> None:
    """Initialize a service if it implements the initialization protocol.

    Args:
        service: The service to potentially initialize
    """
    if isinstance(service, Lifecycle | InitializeOnly):
        await service.initialize()


async def shutdown_service(service: object) -> None:
    """Shutdown a service if it implements the shutdown protocol.

    Args:
        service: The service to potentially shutdown
    """
    if isinstance(service, Lifecycle | ShutdownOnly):
        await service.shutdown()


async def manage_service_lifecycle(service: object, phase: str) -> None:
    """Manage service lifecycle based on phase.

    Args:
        service: The service to manage
        phase: Either "initialize" or "shutdown"
    """
    if phase == "initialize":
        await initialize_service(service)
    elif phase == "shutdown":
        await shutdown_service(service)
    else:
        raise ValueError(f"Invalid lifecycle phase: {phase}")
