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
from dipeo.infrastructure.adapters.events.legacy import AsyncEventBus
from dipeo.core.events import ExecutionEvent, EventType as CoreEventType

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
            # Convert domain event to core execution event
            core_event = self._convert_to_core_event(event)
            if core_event:
                await self._event_bus.emit(core_event)
            else:
                # For events that don't map to core events,
                # handle them directly with subscribers
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
            
            # Subscribe to corresponding core event types
            for event_type in event_types:
                core_type = self._map_to_core_event_type(event_type)
                if core_type:
                    self._event_bus.subscribe(core_type, consumer_adapter)
        
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
                # Unsubscribe from core event bus
                consumer_adapter = self._handlers[handler]
                for event_type in subscription.event_types:
                    core_type = self._map_to_core_event_type(event_type)
                    if core_type:
                        self._event_bus.unsubscribe(core_type, consumer_adapter)
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
    
    def _convert_to_core_event(self, event: DomainEvent) -> Optional[ExecutionEvent]:
        """Convert a domain event to a core execution event."""
        from dipeo.domain.events import (
            ExecutionStartedEvent,
            NodeStartedEvent,
            NodeCompletedEvent,
            NodeErrorEvent,
            ExecutionCompletedEvent,
            MetricsCollectedEvent,
            OptimizationSuggestedEvent,
            WebhookReceivedEvent,
        )
        
        # Map domain events to core events
        if isinstance(event, ExecutionStartedEvent):
            return ExecutionEvent(
                type=CoreEventType.EXECUTION_STARTED,
                execution_id=event.execution_id,
                timestamp=event.timestamp.timestamp(),
                data={
                    "diagram_id": event.diagram_id,
                    "variables": event.variables,
                    "parent_execution_id": event.parent_execution_id,
                }
            )
        elif isinstance(event, NodeStartedEvent):
            return ExecutionEvent(
                type=CoreEventType.NODE_STARTED,
                execution_id=event.execution_id,
                timestamp=event.timestamp.timestamp(),
                data={
                    "node_id": event.node_id,
                    "node_type": event.node_type,
                    "inputs": event.inputs,
                    "iteration": event.iteration,
                }
            )
        elif isinstance(event, NodeCompletedEvent):
            return ExecutionEvent(
                type=CoreEventType.NODE_COMPLETED,
                execution_id=event.execution_id,
                timestamp=event.timestamp.timestamp(),
                data={
                    "node_id": event.node_id,
                    "state": event.state,
                    "duration_ms": event.duration_ms,
                    "token_usage": event.token_usage,
                }
            )
        elif isinstance(event, NodeErrorEvent):
            return ExecutionEvent(
                type=CoreEventType.NODE_FAILED,
                execution_id=event.execution_id,
                timestamp=event.timestamp.timestamp(),
                data={
                    "node_id": event.node_id,
                    "error": event.error,
                    "error_type": event.error_type,
                    "retryable": event.retryable,
                }
            )
        elif isinstance(event, ExecutionCompletedEvent):
            return ExecutionEvent(
                type=CoreEventType.EXECUTION_COMPLETED,
                execution_id=event.execution_id,
                timestamp=event.timestamp.timestamp(),
                data={
                    "status": event.status.value,
                    "total_duration_ms": event.total_duration_ms,
                    "total_tokens_used": event.total_tokens_used,
                }
            )
        elif isinstance(event, MetricsCollectedEvent):
            return ExecutionEvent(
                type=CoreEventType.METRICS_COLLECTED,
                execution_id=event.execution_id,
                timestamp=event.timestamp.timestamp(),
                data=event.metrics
            )
        elif isinstance(event, OptimizationSuggestedEvent):
            return ExecutionEvent(
                type=CoreEventType.OPTIMIZATION_SUGGESTED,
                execution_id=event.execution_id,
                timestamp=event.timestamp.timestamp(),
                data={
                    "suggestion_type": event.suggestion_type,
                    "affected_nodes": event.affected_nodes,
                    "expected_improvement": event.expected_improvement,
                    "description": event.description,
                }
            )
        elif isinstance(event, WebhookReceivedEvent):
            return ExecutionEvent(
                type=CoreEventType.WEBHOOK_RECEIVED,
                execution_id=event.execution_id or "",
                timestamp=event.timestamp.timestamp(),
                data={
                    "webhook_id": event.webhook_id,
                    "source": event.source,
                    "payload": event.payload,
                }
            )
        
        return None
    
    def _map_to_core_event_type(self, event_type: EventType) -> Optional[CoreEventType]:
        """Map domain event type to core event type."""
        mapping = {
            EventType.EXECUTION_STARTED: CoreEventType.EXECUTION_STARTED,
            EventType.EXECUTION_COMPLETED: CoreEventType.EXECUTION_COMPLETED,
            EventType.NODE_STARTED: CoreEventType.NODE_STARTED,
            EventType.NODE_COMPLETED: CoreEventType.NODE_COMPLETED,
            EventType.NODE_ERROR: CoreEventType.NODE_FAILED,
            EventType.METRICS_COLLECTED: CoreEventType.METRICS_COLLECTED,
            EventType.OPTIMIZATION_SUGGESTED: CoreEventType.OPTIMIZATION_SUGGESTED,
            EventType.WEBHOOK_RECEIVED: CoreEventType.WEBHOOK_RECEIVED,
        }
        return mapping.get(event_type)
    
    async def _handle_domain_only_event(self, event: DomainEvent) -> None:
        """Handle events that don't map to core events."""
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
    
    async def consume(self, event: ExecutionEvent) -> None:
        """Consume a core event and convert to domain event."""
        # This is called when core events are emitted
        # We need to convert them back to domain events for the handler
        # For now, just log - the actual conversion happens in the bus
        logger.debug(f"Consumer adapter received event: {event.type}")
        # The handler will be called directly by the bus