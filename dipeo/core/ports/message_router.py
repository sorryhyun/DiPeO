"""Messaging port for domain layer."""

from collections.abc import Callable
from typing import Protocol, runtime_checkable


@runtime_checkable
class MessageRouterPort(Protocol):

    async def initialize(self) -> None:
        ...

    async def cleanup(self) -> None:
        ...

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        ...

    async def unregister_connection(self, connection_id: str) -> None:
        ...

    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        ...

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        ...

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        ...

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        ...

    def get_stats(self) -> dict:
        ...