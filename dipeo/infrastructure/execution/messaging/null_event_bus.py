"""Null event bus implementation for cases where event emission is not needed."""

from collections.abc import Callable
from typing import Any

from dipeo.domain.events import EventBus
from dipeo.domain.events.contracts import DomainEvent


class NullEventBus(EventBus):
    """A no-op event bus that discards all events.

    Used in scenarios where event emission is not needed,
    such as sub-diagram execution in isolation.
    """

    async def initialize(self) -> None:
        """No initialization needed for null event bus."""
        pass

    async def cleanup(self) -> None:
        """No cleanup needed for null event bus."""
        pass

    async def publish(self, event: DomainEvent) -> None:
        """Discard the event without processing."""
        pass

    async def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], None]
    ) -> None:
        """Ignore subscription requests."""
        pass

    async def unsubscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], None]
    ) -> None:
        """Ignore unsubscription requests."""
        pass
