"""Lifecycle protocol for services with initialization and shutdown."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Lifecycle(Protocol):
    """Protocol for services that require lifecycle management."""

    async def initialize(self) -> None:
        """Initialize the service."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the service gracefully."""
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
    """Initialize a service if it implements the initialization protocol."""
    if isinstance(service, Lifecycle | InitializeOnly):
        await service.initialize()


async def shutdown_service(service: object) -> None:
    """Shutdown a service if it implements the shutdown protocol."""
    if isinstance(service, Lifecycle | ShutdownOnly):
        await service.shutdown()


async def manage_service_lifecycle(service: object, phase: str) -> None:
    """Manage service lifecycle based on phase."""
    if phase == "initialize":
        await initialize_service(service)
    elif phase == "shutdown":
        await shutdown_service(service)
    else:
        raise ValueError(f"Invalid lifecycle phase: {phase}")
