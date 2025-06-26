"""Event bus abstraction for pub/sub pattern."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EventBus(ABC):
    """Abstract base class for event bus implementations."""

    @abstractmethod
    async def publish(self, channel: str, event: Dict[str, Any]) -> None:
        """Publish an event to a channel."""
        pass

    @abstractmethod
    async def subscribe(
        self, channel: str, handler: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to events on a channel. Returns subscription ID."""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close all connections and clean up resources."""
        pass
    
    async def get_last_event(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get the last event published to a channel (optional implementation)."""
        return None


class InMemoryEventBus(EventBus):
    """In-memory event bus implementation for single-instance deployments."""

    def __init__(self):
        self._subscribers: Dict[str, Dict[str, Callable]] = {}
        self._subscription_to_channel: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._subscription_counter = 0

    async def publish(self, channel: str, event: Dict[str, Any]) -> None:
        """Publish an event to all subscribers of a channel."""
        async with self._lock:
            subscribers = self._subscribers.get(channel, {}).copy()

        if not subscribers:
            logger.debug(f"No subscribers for channel {channel}")
            return

        # Call handlers concurrently
        tasks = []
        for sub_id, handler in subscribers.items():
            tasks.append(self._call_handler(sub_id, handler, event))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in event handler: {result}")

    async def subscribe(
        self, channel: str, handler: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to events on a channel."""
        async with self._lock:
            self._subscription_counter += 1
            subscription_id = f"sub_{self._subscription_counter}"

            if channel not in self._subscribers:
                self._subscribers[channel] = {}

            self._subscribers[channel][subscription_id] = handler
            self._subscription_to_channel[subscription_id] = channel

            logger.debug(f"Subscribed {subscription_id} to channel {channel}")
            return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        async with self._lock:
            channel = self._subscription_to_channel.get(subscription_id)
            if not channel:
                logger.warning(f"Unknown subscription {subscription_id}")
                return

            if channel in self._subscribers:
                self._subscribers[channel].pop(subscription_id, None)
                if not self._subscribers[channel]:
                    del self._subscribers[channel]

            del self._subscription_to_channel[subscription_id]
            logger.debug(f"Unsubscribed {subscription_id} from channel {channel}")

    async def close(self) -> None:
        """Clear all subscriptions."""
        async with self._lock:
            self._subscribers.clear()
            self._subscription_to_channel.clear()

    async def _call_handler(
        self, sub_id: str, handler: Callable, event: Dict[str, Any]
    ) -> None:
        """Call an event handler safely."""
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Error in handler {sub_id}: {e}")
            # Consider unsubscribing failed handlers
            await self.unsubscribe(sub_id)


class MessageRouterEventBus(EventBus):
    """Event bus implementation that integrates with MessageRouter for WebSocket support."""

    def __init__(self, message_router):
        self.message_router = message_router
        self._local_subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
        self._last_event_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 60  # Cache events for 60 seconds

    async def publish(self, channel: str, event: Dict[str, Any]) -> None:
        """Publish event to both local subscribers and WebSocket connections."""
        # Cache the event for fallback
        event_with_timestamp = {
            **event,
            "_timestamp": asyncio.get_event_loop().time()
        }
        self._last_event_cache[channel] = event_with_timestamp
        
        # Publish to local subscribers
        async with self._lock:
            local_handlers = self._local_subscribers.get(channel, []).copy()

        for handler in local_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in local handler: {e}")

        # If channel is an execution ID, broadcast via MessageRouter
        if channel.startswith("execution:"):
            execution_id = channel.replace("execution:", "")
            await self.message_router.broadcast_to_execution(execution_id, event)

    async def subscribe(
        self, channel: str, handler: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to events on a channel."""
        async with self._lock:
            if channel not in self._local_subscribers:
                self._local_subscribers[channel] = []
            self._local_subscribers[channel].append(handler)

        # Generate a unique subscription ID
        return f"local_{id(handler)}"

    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        # For local subscriptions, we'd need to track handler references
        # This is simplified for now
        pass

    async def close(self) -> None:
        """Clear all subscriptions."""
        async with self._lock:
            self._local_subscribers.clear()
            self._last_event_cache.clear()
    
    async def get_last_event(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get the last event published to a channel (if still in cache)."""
        cached_event = self._last_event_cache.get(channel)
        if cached_event:
            # Check if event is still within TTL
            current_time = asyncio.get_event_loop().time()
            event_time = cached_event.get("_timestamp", 0)
            if current_time - event_time < self._cache_ttl:
                # Return event without internal timestamp
                return {k: v for k, v in cached_event.items() if k != "_timestamp"}
        return None