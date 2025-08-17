"""Legacy AsyncEventBus implementation for backward compatibility.

This module contains the original event bus implementation that uses
the core events system. It's being kept for backward compatibility
during the migration to domain events.
"""

import asyncio
import logging
from collections import defaultdict

from dipeo.core.events import EventConsumer, EventEmitter, EventType, ExecutionEvent

logger = logging.getLogger(__name__)


class AsyncEventBus(EventEmitter):
    """Legacy event bus implementation using core events.
    
    This class is being phased out in favor of the domain event bus.
    It's kept for backward compatibility during the migration.
    """
    
    def __init__(self, queue_size: int = 1000):
        self._subscribers: dict[EventType, set[EventConsumer]] = defaultdict(set)
        self._queues: dict[EventConsumer, asyncio.Queue] = {}
        self._tasks: list[asyncio.Task] = []
        self._queue_size = queue_size
        self._running = False
    
    def subscribe(self, event_type: EventType, consumer: EventConsumer) -> None:
        self._subscribers[event_type].add(consumer)
        if consumer not in self._queues:
            self._queues[consumer] = asyncio.Queue(maxsize=self._queue_size)
            # Start consumer task
            task = asyncio.create_task(self._consume_loop(consumer))
            self._tasks.append(task)
    
    def unsubscribe(self, event_type: EventType, consumer: EventConsumer) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(consumer)
    
    async def emit(self, event: ExecutionEvent) -> None:
        """Fire-and-forget emission"""
        subscribers = self._subscribers.get(event.type, set())
        
        for consumer in subscribers:
            try:
                # Non-blocking put
                self._queues[consumer].put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    f"Queue full for consumer {consumer.__class__.__name__}, "
                    f"dropping event {event.type.value} for execution {event.execution_id}"
                )
    
    async def _consume_loop(self, consumer: EventConsumer) -> None:
        queue = self._queues[consumer]
        
        while True:
            try:
                event = await queue.get()
                await consumer.consume(event)
            except asyncio.CancelledError:
                logger.debug(f"Consumer loop cancelled for {consumer.__class__.__name__}")
                break
            except Exception as e:
                logger.error(
                    f"Error in consumer {consumer.__class__.__name__}: {e}",
                    exc_info=True
                )
    
    async def start(self) -> None:
        """Start the event bus"""
        self._running = True
    
    async def stop(self) -> None:
        """Stop the event bus and clean up resources"""
        self._running = False
        
        # Cancel all consumer tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for all tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Clear all data structures
        self._tasks.clear()
        self._subscribers.clear()
        self._queues.clear()


class NullEventBus(EventEmitter):
    """No-op event bus for testing or when events are disabled"""
    
    async def emit(self, event: ExecutionEvent) -> None:
        pass