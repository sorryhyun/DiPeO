"""Messaging port for domain layer.

DEPRECATED: This module re-exports domain types for backward compatibility.
Use dipeo.domain.messaging directly for new code.
"""

import warnings
from collections.abc import Callable
from typing import Protocol, runtime_checkable

# Re-export domain types
from dipeo.domain.messaging import DomainEventBus, MessageBus

warnings.warn(
    "dipeo.core.ports.message_router is deprecated. "
    "Use dipeo.domain.messaging instead.",
    DeprecationWarning,
    stacklevel=2,
)


@runtime_checkable
class MessageRouterPort(Protocol):
    """Legacy message router port - wraps new domain MessageBus for backward compatibility."""

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


# Export domain types for backward compatibility
__all__ = [
    "MessageRouterPort",
    "MessageBus",
    "DomainEventBus",
]