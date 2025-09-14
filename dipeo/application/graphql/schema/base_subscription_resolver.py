"""Base class for GraphQL subscription resolvers with common functionality."""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from typing import Any, Protocol, TypeVar

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import MESSAGE_ROUTER, STATE_STORE
from dipeo.config.settings import get_settings
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import EventType

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def __call__(self, message: dict[str, Any]) -> None:
        """Handle an incoming event message."""
        ...


class BaseSubscriptionResolver:
    """Base class for subscription resolvers with common functionality."""

    def __init__(self, registry: ServiceRegistry):
        """Initialize the subscription resolver."""
        self.registry = registry
        self.message_router = registry.get(MESSAGE_ROUTER)
        self.state_store = registry.get(STATE_STORE)
        self.settings = get_settings()
        self.keepalive_interval = self.settings.messaging.ws_keepalive_sec

    async def _verify_execution_exists(self, execution_id: ExecutionID) -> bool:
        """Verify that an execution exists."""
        if not self.state_store:
            return True  # Assume it exists if we can't verify

        execution = await self.state_store.get_state(str(execution_id))
        if not execution:
            logger.warning(f"Execution not found: {execution_id}")
            return False
        return True

    async def _create_subscription_context(
        self,
        execution_id: ExecutionID,
        subscription_type: str = "generic",
    ) -> tuple[asyncio.Queue, str]:
        """Create a subscription context with queue and connection ID."""
        if not self.message_router:
            raise RuntimeError("Message router not available for subscriptions")

        # Create event queue
        event_queue: asyncio.Queue = asyncio.Queue()
        connection_id = f"graphql-{subscription_type}-subscription-{id(event_queue)}"

        # Define handler to put events in queue
        async def event_handler(message: dict[str, Any]) -> None:
            await event_queue.put(message)

        # Register and subscribe
        await self.message_router.register_connection(connection_id, event_handler)
        await self.message_router.subscribe_connection_to_execution(
            connection_id, str(execution_id)
        )

        return event_queue, connection_id

    async def _cleanup_subscription(self, connection_id: str, execution_id: ExecutionID) -> None:
        """Clean up a subscription."""
        if self.message_router:
            await self.message_router.unsubscribe_connection_from_execution(
                connection_id, str(execution_id)
            )
            await self.message_router.unregister_connection(connection_id)

    def _should_send_keepalive(self, last_keepalive: float) -> bool:
        """Check if a keepalive should be sent."""
        if self.keepalive_interval <= 0:
            return False

        current_time = time.time()
        return (current_time - last_keepalive) >= self.keepalive_interval

    def _create_keepalive_payload(self) -> dict[str, Any]:
        """Create a keepalive payload."""
        return {
            "type": EventType.KEEPALIVE,
            "timestamp": datetime.now().isoformat(),
        }

    async def _check_execution_completion(self, execution_id: ExecutionID) -> tuple[bool, Any]:
        """Check if execution is complete and return status."""
        if not self.state_store:
            return False, None

        execution = await self.state_store.get_state(str(execution_id))
        if not execution:
            return True, None  # Execution no longer exists

        # Check if execution is complete
        from dipeo.diagram_generated import Status

        # Check if execution status indicates completion
        if execution.status in (
            Status.COMPLETED,
            Status.FAILED,
            Status.ABORTED,
            Status.MAXITER_REACHED,
        ):
            return True, execution.status

        return False, None

    async def _process_event_queue(
        self,
        event_queue: asyncio.Queue,
        execution_id: ExecutionID,
        event_filter: Callable[[dict[str, Any]], bool] | None = None,
        event_transformer: Callable[[dict[str, Any]], Any] | None = None,
    ) -> AsyncGenerator[Any]:
        """Process events from the queue with optional filtering and transformation."""
        last_keepalive = time.time()

        while True:
            try:
                # Wait for events with timeout
                event = await asyncio.wait_for(event_queue.get(), timeout=30.0)

                # Apply filter if provided
                if event_filter and not event_filter(event):
                    continue

                # Apply transformation if provided
                if event_transformer:
                    transformed = event_transformer(event)
                    if transformed is not None:
                        yield transformed
                        last_keepalive = time.time()
                else:
                    yield event
                    last_keepalive = time.time()

            except TimeoutError:
                # Send keepalive if needed
                if self._should_send_keepalive(last_keepalive):
                    yield self._create_keepalive_payload()
                    last_keepalive = time.time()
                    logger.debug(f"Sent keepalive for {execution_id}")

                # Check if execution is complete
                is_complete, status = await self._check_execution_completion(execution_id)
                if is_complete:
                    if status:
                        # Send final status update
                        yield {
                            "execution_id": str(execution_id),
                            "event_type": "EXECUTION_STATUS_CHANGED",
                            "data": {"status": status, "is_final": True},
                            "timestamp": datetime.now().isoformat(),
                        }
                    break

    async def subscribe(
        self,
        execution_id: str,
        subscription_type: str = "generic",
        event_filter: Callable[[dict[str, Any]], bool] | None = None,
        event_transformer: Callable[[dict[str, Any]], Any] | None = None,
    ) -> AsyncGenerator[Any]:
        """Generic subscription method for all subscription types."""
        exec_id = ExecutionID(str(execution_id))

        try:
            # Verify execution exists
            if not await self._verify_execution_exists(exec_id):
                return

            # Create subscription context
            event_queue, connection_id = await self._create_subscription_context(
                exec_id, subscription_type
            )

            try:
                # Process events
                async for event in self._process_event_queue(
                    event_queue, exec_id, event_filter, event_transformer
                ):
                    yield event

            finally:
                # Clean up
                await self._cleanup_subscription(connection_id, exec_id)

        except asyncio.CancelledError:
            logger.info(f"{subscription_type} subscription cancelled for execution: {exec_id}")
            raise
        except Exception as e:
            logger.error(f"Error in {subscription_type} subscription: {e}")
            raise
