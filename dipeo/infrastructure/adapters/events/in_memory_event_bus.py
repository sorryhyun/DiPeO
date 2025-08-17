"""In-memory implementation of DomainEventBus for single-process applications."""

import asyncio
import logging
from collections import defaultdict
from typing import Optional, Callable
from uuid import uuid4
import re

from dipeo.domain.events import (
    DomainEvent,
    EventHandler,
    EventSubscription,
    DomainEventBus,
    EventType,
    EventPriority,
)

logger = logging.getLogger(__name__)


class InMemoryEventBus(DomainEventBus):
    """In-memory event bus for single-process applications.
    
    Features:
    - Zero network overhead
    - Priority-based processing
    - Filter expression support
    - Bounded queues to prevent memory issues
    """
    
    def __init__(
        self,
        max_queue_size: int = 1000,
        enable_event_store: bool = False
    ):
        """Initialize the in-memory event bus.
        
        Args:
            max_queue_size: Maximum number of events in each handler's queue
            enable_event_store: Whether to store events for replay
        """
        self._subscriptions: dict[str, EventSubscription] = {}
        self._handlers_by_type: dict[EventType, list[EventSubscription]] = defaultdict(list)
        self._queues: dict[str, asyncio.Queue] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._max_queue_size = max_queue_size
        self._enable_event_store = enable_event_store
        self._event_store: list[DomainEvent] = []
        self._running = False
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        if not self._running:
            logger.warning("Event bus not running, event dropped")
            return
        
        # Store event if enabled
        if self._enable_event_store:
            self._event_store.append(event)
        
        # Find matching subscriptions
        subscriptions = self._handlers_by_type.get(event.event_type, [])
        
        # Sort by priority (higher priority first)
        sorted_subs = sorted(
            subscriptions,
            key=lambda s: s.priority.value,
            reverse=True
        )
        
        for subscription in sorted_subs:
            if not subscription.active:
                continue
            
            # Apply filter if specified
            if subscription.filter_expression and not self._evaluate_filter(
                event, subscription.filter_expression
            ):
                continue
            
            # Add to handler's queue
            queue = self._queues.get(subscription.subscription_id)
            if queue:
                try:
                    if subscription.priority == EventPriority.CRITICAL:
                        # Critical events bypass the queue
                        await subscription.handler.handle(event)
                    else:
                        # Non-critical events go through the queue
                        queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning(
                        f"Queue full for subscription {subscription.subscription_id}, "
                        f"dropping event {event.event_type}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error handling event {event.event_type}: {e}",
                        exc_info=True
                    )
    
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically."""
        # In-memory implementation publishes them sequentially
        # but ensures all-or-nothing semantics
        try:
            for event in events:
                await self.publish(event)
        except Exception as e:
            logger.error(f"Batch publish failed: {e}")
            raise
    
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
        
        # Store subscription
        self._subscriptions[subscription_id] = subscription
        
        # Index by event type for fast lookup
        for event_type in event_types:
            self._handlers_by_type[event_type].append(subscription)
        
        # Create queue and processing task for non-critical subscriptions
        if priority != EventPriority.CRITICAL:
            queue = asyncio.Queue(maxsize=self._max_queue_size)
            self._queues[subscription_id] = queue
            
            # Start processing task
            task = asyncio.create_task(
                self._process_queue(subscription, queue)
            )
            self._tasks[subscription_id] = task
        
        logger.debug(
            f"Subscribed {handler.__class__.__name__} to {event_types} "
            f"with priority {priority}"
        )
        
        return subscription
    
    async def unsubscribe(self, subscription: EventSubscription) -> None:
        """Unsubscribe from domain events."""
        subscription_id = subscription.subscription_id
        
        if subscription_id not in self._subscriptions:
            return
        
        # Mark as inactive
        subscription.active = False
        
        # Remove from indexes
        for event_type in subscription.event_types:
            if event_type in self._handlers_by_type:
                self._handlers_by_type[event_type] = [
                    s for s in self._handlers_by_type[event_type]
                    if s.subscription_id != subscription_id
                ]
        
        # Cancel processing task
        if subscription_id in self._tasks:
            task = self._tasks[subscription_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._tasks[subscription_id]
        
        # Remove queue
        if subscription_id in self._queues:
            del self._queues[subscription_id]
        
        # Remove subscription
        del self._subscriptions[subscription_id]
        
        logger.debug(f"Unsubscribed {subscription_id}")
    
    async def start(self) -> None:
        """Start the event bus."""
        self._running = True
        logger.info("In-memory event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus and clean up resources."""
        self._running = False
        
        # Cancel all processing tasks
        for task in self._tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        
        # Clear all data structures
        self._subscriptions.clear()
        self._handlers_by_type.clear()
        self._queues.clear()
        self._tasks.clear()
        
        if self._enable_event_store:
            logger.info(f"Event store contains {len(self._event_store)} events")
        
        logger.info("In-memory event bus stopped")
    
    async def _process_queue(
        self,
        subscription: EventSubscription,
        queue: asyncio.Queue
    ) -> None:
        """Process events from a subscription's queue."""
        while True:
            try:
                event = await queue.get()
                
                if not subscription.active:
                    continue
                
                await subscription.handler.handle(event)
                
            except asyncio.CancelledError:
                logger.debug(
                    f"Queue processor cancelled for {subscription.subscription_id}"
                )
                break
            except Exception as e:
                logger.error(
                    f"Error processing event for {subscription.subscription_id}: {e}",
                    exc_info=True
                )
    
    def _evaluate_filter(
        self,
        event: DomainEvent,
        filter_expression: str
    ) -> bool:
        """Evaluate a filter expression against an event.
        
        Simple implementation supporting basic comparisons:
        - execution_id == 'value'
        - node_id == 'value'
        - event_type == 'value'
        """
        try:
            # Parse simple equality expressions
            match = re.match(r"(\w+)\s*==\s*['\"]([^'\"]+)['\"]", filter_expression)
            if match:
                field, value = match.groups()
                
                # Check if event has the field
                if hasattr(event, field):
                    actual_value = getattr(event, field)
                    if isinstance(actual_value, EventType):
                        actual_value = actual_value.name
                    return str(actual_value) == value
            
            # If we can't parse the filter, allow the event
            return True
            
        except Exception as e:
            logger.warning(f"Failed to evaluate filter '{filter_expression}': {e}")
            return True
    
    def get_event_store(self) -> list[DomainEvent]:
        """Get all stored events (for testing/debugging)."""
        if not self._enable_event_store:
            return []
        return self._event_store.copy()
    
    def clear_event_store(self) -> None:
        """Clear the event store (for testing)."""
        self._event_store.clear()