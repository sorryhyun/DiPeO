"""Adapters that bridge existing messaging infrastructure to new domain ports."""

from collections.abc import Callable
from typing import Any

from dipeo.core.bak.events import EventType, ExecutionEvent
from dipeo.application.migration.compat_imports import MessageRouterPort
from dipeo.domain.messaging import DomainEventBus, MessageBus
from dipeo.domain.messaging.events import DomainEvent
from dipeo.infrastructure.adapters.messaging import MessageRouter
from dipeo.infrastructure.adapters.events import AsyncEventBus


class MessageBusAdapter(MessageBus):
    """Adapter wrapping MessageRouter to implement domain MessageBus port."""

    def __init__(self, router: MessageRouterPort | None = None):
        self._router = router or MessageRouter()

    async def initialize(self) -> None:
        await self._router.initialize()

    async def cleanup(self) -> None:
        await self._router.cleanup()

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        await self._router.register_connection(connection_id, handler)

    async def unregister_connection(self, connection_id: str) -> None:
        await self._router.unregister_connection(connection_id)

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        await self._router.broadcast_to_execution(execution_id, message)

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        await self._router.subscribe_connection_to_execution(connection_id, execution_id)

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        await self._router.unsubscribe_connection_from_execution(connection_id, execution_id)

    def get_stats(self) -> dict:
        return self._router.get_stats()


class DomainEventBusAdapter(DomainEventBus):
    """Adapter that bridges domain events to the core event bus."""

    def __init__(self, event_bus: AsyncEventBus | None = None):
        self._event_bus = event_bus or AsyncEventBus()
        self._domain_handlers: dict[type[DomainEvent], list[Callable]] = {}

    async def initialize(self) -> None:
        """Initialize the event bus."""
        await self._event_bus.start()

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._event_bus.stop()

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event by converting it to core ExecutionEvent."""
        # Map domain events to core event types
        event_type_map = {
            "ExecutionStarted": EventType.EXECUTION_STARTED,
            "ExecutionCompleted": EventType.EXECUTION_COMPLETED,
            "ExecutionUpdated": EventType.EXECUTION_COMPLETED,  # Map to closest available
            "NodeExecutionStarted": EventType.NODE_STARTED,
            "NodeExecutionCompleted": EventType.NODE_COMPLETED,
            "NodeOutputAppended": EventType.NODE_COMPLETED,  # Map to closest available
        }
        
        event_class_name = event.__class__.__name__
        core_event_type = event_type_map.get(event_class_name, EventType.EXECUTION_STARTED)
        
        # Create ExecutionEvent from domain event
        # Try to get execution_id from either 'execution_id' or 'aggregate_id' (base DomainEvent)
        execution_id = getattr(event, 'execution_id', getattr(event, 'aggregate_id', ''))
        
        # Get timestamp from domain event or use current time
        import time
        if hasattr(event, 'timestamp'):
            timestamp = event.timestamp.timestamp() if hasattr(event.timestamp, 'timestamp') else time.time()
        else:
            timestamp = time.time()
        
        execution_event = ExecutionEvent(
            execution_id=execution_id,
            type=core_event_type,
            timestamp=timestamp,
            data={
                'domain_event': event_class_name,
                'payload': event.to_dict() if hasattr(event, 'to_dict') else vars(event),
            },
        )
        
        await self._event_bus.emit(execution_event)
        
        # Also call domain handlers directly
        handlers = self._domain_handlers.get(type(event), [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # Log but don't fail
                import logging
                logging.getLogger(__name__).error(f"Domain event handler failed: {e}")

    async def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], None]
    ) -> None:
        """Subscribe to a domain event type."""
        if event_type not in self._domain_handlers:
            self._domain_handlers[event_type] = []
        self._domain_handlers[event_type].append(handler)

    async def unsubscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], None]
    ) -> None:
        """Unsubscribe from a domain event type."""
        if event_type in self._domain_handlers:
            try:
                self._domain_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not in list