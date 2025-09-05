"""Port interfaces for domain event handling.

DEPRECATED: This module provides backward compatibility for the old event protocols.
New code should use the unified EventBus protocol from unified_ports.py.

The protocols have been consolidated as follows:
- DomainEventBus → EventBus
- EventEmitter → EventBus
- EventConsumer → EventBus
- MessageBus → EventBus

These aliases will be removed in v1.0.
"""

from .contracts import DomainEvent
from .unified_ports import (
    EventBus,
    EventFilter,
    EventHandler,
    EventStore,
    EventSubscription,
)

# Re-export unified types
__all__ = [
    "DomainEventBus",
    "EventConsumer",
    "EventEmitter",
    "EventFilter",
    "EventHandler",
    "EventStore",
    "EventSubscription",
    "MessageBus",
]


# Backward Compatibility Protocol Wrappers
class DomainEventBus(EventBus):
    """Legacy DomainEventBus protocol.

    DEPRECATED: Use EventBus directly.
    This wrapper provides backward compatibility for the old DomainEventBus interface.
    """

    async def start(self) -> None:
        """Legacy start method - maps to initialize()."""
        await self.initialize()

    async def stop(self) -> None:
        """Legacy stop method - maps to cleanup()."""
        await self.cleanup()


class EventEmitter(EventBus):
    """Legacy EventEmitter protocol.

    DEPRECATED: Use EventBus.publish() directly.
    """

    async def emit(self, event: DomainEvent) -> None:
        """Legacy emit method - maps to publish()."""
        await self.publish(event)


class EventConsumer(EventBus):
    """Legacy EventConsumer protocol.

    DEPRECATED: Use EventBus.subscribe() with a handler instead.
    """

    async def consume(self, event: DomainEvent) -> None:
        """Legacy consume method.

        Note: This doesn't map cleanly to the new EventBus.
        Implementations should use subscribe() with appropriate handlers.
        """
        # This is a placeholder for backward compatibility
        # Real implementations should override this
        pass


# MessageBus is now just an alias to EventBus
MessageBus = EventBus
