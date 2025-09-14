"""In-memory implementation of EventBus for single-process applications."""

import asyncio
import contextlib
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from dipeo.domain.events import (
    DomainEvent,
    EventPriority,
    EventSubscription,
    EventType,
)
from dipeo.domain.events.unified_ports import (
    EventBus,
    EventFilter,
    EventHandler,
)

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """In-memory event bus for single-process applications.

    Features:
    - Zero network overhead
    - Priority-based processing
    - Event filter support
    - Bounded queues to prevent memory issues
    """

    def __init__(self, max_queue_size: int = 1000, enable_event_store: bool = False):
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

    async def _handle_legacy_event(self, event: Any) -> None:
        """Handle legacy event types."""
        for subscription in self._subscriptions.values():
            try:
                await subscription.handler.handle(event)
            except Exception as e:
                logger.error(f"Error handling legacy event: {e}")

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        if not self._running:
            logger.warning("Event bus not running, event dropped")
            return

        if self._enable_event_store:
            self._event_store.append(event)

        subscriptions = self._handlers_by_type.get(event.type, [])
        sorted_subs = sorted(subscriptions, key=lambda s: s.priority.value, reverse=True)

        for subscription in sorted_subs:
            if not subscription.active:
                continue

            if subscription.filter and not subscription.filter.matches(event):
                continue

            queue = self._queues.get(subscription.subscription_id)
            if queue:
                try:
                    if subscription.priority == EventPriority.CRITICAL:
                        await subscription.handler.handle(event)
                    else:
                        queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning(
                        f"Queue full for subscription {subscription.subscription_id}, "
                        f"dropping event {event.type}"
                    )
                except Exception as e:
                    logger.error(f"Error handling event {event.type}: {e}", exc_info=True)

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically."""
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
        filter: EventFilter | None = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> EventSubscription:
        """Subscribe to domain events."""
        subscription_id = str(uuid4())
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_types=event_types,
            handler=handler,
            filter=filter,
            priority=priority,
            active=True,
        )

        self._subscriptions[subscription_id] = subscription

        for event_type in event_types:
            self._handlers_by_type[event_type].append(subscription)

        if priority != EventPriority.CRITICAL:
            queue = asyncio.Queue(maxsize=self._max_queue_size)
            self._queues[subscription_id] = queue

            task = asyncio.create_task(self._process_queue(subscription, queue))
            self._tasks[subscription_id] = task

        return subscription

    async def unsubscribe(self, subscription: EventSubscription) -> None:
        """Unsubscribe from domain events."""
        subscription_id = subscription.subscription_id

        if subscription_id not in self._subscriptions:
            return

        subscription.active = False

        for event_type in subscription.event_types:
            if event_type in self._handlers_by_type:
                self._handlers_by_type[event_type] = [
                    s
                    for s in self._handlers_by_type[event_type]
                    if s.subscription_id != subscription_id
                ]

        if subscription_id in self._tasks:
            task = self._tasks[subscription_id]
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            del self._tasks[subscription_id]

        if subscription_id in self._queues:
            del self._queues[subscription_id]

        del self._subscriptions[subscription_id]

        logger.debug(f"Unsubscribed {subscription_id}")

    async def initialize(self) -> None:
        """Initialize the event bus."""
        self._running = True

    async def cleanup(self) -> None:
        """Stop the event bus and clean up resources."""
        self._running = False

        for task in self._tasks.values():
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)

        self._subscriptions.clear()
        self._handlers_by_type.clear()
        self._queues.clear()
        self._tasks.clear()

        if self._enable_event_store:
            logger.info(f"Event store contains {len(self._event_store)} events")

    async def _process_queue(self, subscription: EventSubscription, queue: asyncio.Queue) -> None:
        """Process events from a subscription's queue."""
        while True:
            try:
                event = await queue.get()

                if not subscription.active:
                    continue

                await subscription.handler.handle(event)

            except asyncio.CancelledError:
                # logger.debug(f"Queue processor cancelled for {subscription.subscription_id}")
                break
            except Exception as e:
                logger.error(
                    f"Error processing event for {subscription.subscription_id}: {e}", exc_info=True
                )

    def get_event_store(self) -> list[DomainEvent]:
        """Get all stored events (for testing/debugging)."""
        if not self._enable_event_store:
            return []
        return self._event_store.copy()

    def clear_event_store(self) -> None:
        """Clear the event store (for testing)."""
        self._event_store.clear()

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        """Register a connection handler for execution updates."""
        # Not needed for in-memory event bus
        pass

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection."""
        # Not needed for in-memory event bus
        pass

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast message to all connections subscribed to execution."""
        # Not needed for in-memory event bus
        pass

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe connection to execution updates."""
        # Not needed for in-memory event bus
        pass

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe connection from execution updates."""
        # Not needed for in-memory event bus
        pass
