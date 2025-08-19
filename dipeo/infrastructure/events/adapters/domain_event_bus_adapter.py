"""Adapter that bridges domain events with existing AsyncEventBus."""

import asyncio
import logging
from typing import Optional
from uuid import uuid4

from dipeo.domain.events import (
    DomainEvent,
    EventHandler,
    EventSubscription,
    DomainEventBus,
    EventType,
    EventPriority,
)
from dipeo.infrastructure.events.adapters.legacy import AsyncEventBus

logger = logging.getLogger(__name__)


class DomainEventBusAdapter(DomainEventBus):
    """Adapter that bridges domain events with the existing AsyncEventBus.
    
    This adapter provides backward compatibility during the migration
    from the observer pattern to domain events.
    """
    
    def __init__(self, async_event_bus: Optional[AsyncEventBus] = None):
        """Initialize the adapter.
        
        Args:
            async_event_bus: Existing event bus to bridge with.
                            If not provided, creates a new one.
        """
        self._event_bus = async_event_bus or AsyncEventBus()
        self._subscriptions: dict[str, EventSubscription] = {}
        self._handlers: dict[EventHandler, "EventConsumerAdapter"] = {}
        self._running = False
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        try:
            # Emit the domain event directly through the async event bus
            await self._event_bus.emit(event)
            
            # Also handle domain-only subscribers directly
            await self._handle_domain_only_event(event)
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
    
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically."""
        # For now, publish them sequentially
        # TODO: Implement atomic batch publishing
        for event in events:
            await self.publish(event)
    
    async def subscribe(
        self,
        event_types: list[EventType],
        handler: EventHandler,
        filter_expression: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL
    ) -> EventSubscription:
        """Subscribe to domain events."""
        subscription_id = str(uuid4())
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_types=event_types,
            handler=handler,
            filter_expression=filter_expression,
            priority=priority,
            active=True
        )
        
        self._subscriptions[subscription_id] = subscription
        
        # Create adapter for the handler if needed
        if handler not in self._handlers:
            consumer_adapter = EventConsumerAdapter(handler, self)
            self._handlers[handler] = consumer_adapter
            
            # Subscribe to event types in the async bus
            for event_type in event_types:
                self._event_bus.subscribe(event_type, consumer_adapter)
        
        return subscription
    
    async def unsubscribe(self, subscription: EventSubscription) -> None:
        """Unsubscribe from domain events."""
        if subscription.subscription_id in self._subscriptions:
            del self._subscriptions[subscription.subscription_id]
            subscription.active = False
            
            # Check if handler has any other active subscriptions
            handler = subscription.handler
            has_other_subs = any(
                sub.handler == handler and sub.active
                for sub in self._subscriptions.values()
            )
            
            if not has_other_subs and handler in self._handlers:
                # Unsubscribe from async event bus
                consumer_adapter = self._handlers[handler]
                for event_type in subscription.event_types:
                    self._event_bus.unsubscribe(event_type, consumer_adapter)
                del self._handlers[handler]
    
    async def start(self) -> None:
        """Start the event bus."""
        self._running = True
        await self._event_bus.start()
    
    async def stop(self) -> None:
        """Stop the event bus and clean up resources."""
        self._running = False
        await self._event_bus.stop()
        self._subscriptions.clear()
        self._handlers.clear()
    
    async def _handle_domain_only_event(self, event: DomainEvent) -> None:
        """Handle events directly with domain subscribers."""
        # Find matching subscriptions
        for subscription in self._subscriptions.values():
            if not subscription.active:
                continue
            
            if event.event_type in subscription.event_types:
                # Apply filter if specified
                if subscription.filter_expression:
                    # TODO: Implement filter expression evaluation
                    pass
                
                # Handle based on priority
                if subscription.priority == EventPriority.CRITICAL:
                    # Handle immediately
                    await subscription.handler.handle(event)
                else:
                    # Handle asynchronously
                    asyncio.create_task(subscription.handler.handle(event))


class EventConsumerAdapter:
    """Adapter that converts EventConsumer protocol to EventHandler."""
    
    def __init__(self, handler: EventHandler, bus: DomainEventBusAdapter):
        self.handler = handler
        self.bus = bus
    
    async def consume(self, event: DomainEvent) -> None:
        """Consume a domain event and pass to handler."""
        # Pass the domain event directly to the handler
        await self.handler.handle(event)