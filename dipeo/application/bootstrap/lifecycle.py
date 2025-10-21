"""Lifecycle protocol for services with initialization and shutdown."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Lifecycle(Protocol):
    async def initialize(self) -> None: ...

    async def shutdown(self) -> None: ...


@runtime_checkable
class InitializeOnly(Protocol):
    async def initialize(self) -> None: ...


@runtime_checkable
class ShutdownOnly(Protocol):
    async def shutdown(self) -> None: ...


async def initialize_service(service: object) -> None:
    if isinstance(service, Lifecycle | InitializeOnly):
        await service.initialize()


async def shutdown_service(service: object) -> None:
    if isinstance(service, Lifecycle | ShutdownOnly):
        await service.shutdown()


async def manage_service_lifecycle(service: object, phase: str) -> None:
    if phase == "initialize":
        await initialize_service(service)
    elif phase == "shutdown":
        await shutdown_service(service)
    else:
        raise ValueError(f"Invalid lifecycle phase: {phase}")
