"""GraphQL subscriptions for real-time updates."""

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import strawberry
from strawberry.scalars import JSON

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import MESSAGE_ROUTER, STATE_STORE
from dipeo.config.settings import get_settings
from dipeo.diagram_generated import Status
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import EventType

logger = logging.getLogger(__name__)


def serialize_for_json(obj: Any, seen: set | None = None, max_depth: int = 10) -> Any:
    """Recursively serialize objects for JSON encoding with circular reference protection."""
    import types

    if seen is None:
        seen = set()

    # Check recursion depth
    if max_depth <= 0:
        return str(obj)  # Fallback to string representation

    # Check for circular references
    obj_id = id(obj)
    if obj_id in seen:
        return f"<circular reference to {type(obj).__name__}>"

    # Handle basic types that don't need recursion
    if obj is None or isinstance(obj, bool | int | float | str):
        return obj

    if isinstance(obj, datetime):
        return obj.isoformat()

    # Add to seen set for complex objects
    seen.add(obj_id)

    try:
        if isinstance(obj, types.MappingProxyType):
            # Convert mappingproxy to regular dict
            return {k: serialize_for_json(v, seen, max_depth - 1) for k, v in obj.items()}
        elif isinstance(obj, dict):
            return {k: serialize_for_json(v, seen, max_depth - 1) for k, v in obj.items()}
        elif isinstance(obj, list | tuple | set | frozenset):
            return [serialize_for_json(item, seen, max_depth - 1) for item in obj]
        elif hasattr(obj, "__dict__"):
            # Handle Pydantic models or other objects with __dict__
            # Skip private attributes to avoid internal state
            return {
                k: serialize_for_json(v, seen, max_depth - 1)
                for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
        else:
            return str(obj)  # Fallback to string representation
    finally:
        # Remove from seen set when done
        seen.discard(obj_id)


@strawberry.type
class ExecutionUpdate:
    """Real-time execution update."""

    execution_id: str
    event_type: str
    data: JSON
    timestamp: str


def create_subscription_type(registry: ServiceRegistry) -> type:
    """Create a Subscription type with injected service registry."""

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def execution_updates(
            self, execution_id: strawberry.ID
        ) -> AsyncGenerator[ExecutionUpdate]:
            """Subscribe to real-time updates for an execution."""
            message_router = registry.get(MESSAGE_ROUTER)
            state_store = registry.get(STATE_STORE)

            if not message_router:
                logger.error("Message router not available for subscriptions")
                return

            exec_id = ExecutionID(str(execution_id))

            try:
                # Verify execution exists
                if state_store:
                    execution = await state_store.get_state(str(exec_id))
                    if not execution:
                        logger.warning(f"Execution not found: {exec_id}")
                        return

                # Create a queue for receiving events
                event_queue = asyncio.Queue()
                connection_id = f"graphql-subscription-{id(event_queue)}"

                # Define handler to put events in queue
                async def event_handler(message):
                    # Serialize the entire message to ensure all nested objects are JSON-safe
                    serialized_message = serialize_for_json(message)
                    await event_queue.put(serialized_message)

                # Register connection and subscribe to execution
                await message_router.register_connection(connection_id, event_handler)
                await message_router.subscribe_connection_to_execution(connection_id, str(exec_id))

                # Get keepalive settings
                settings = get_settings()
                keepalive_interval = settings.messaging.ws_keepalive_sec
                last_keepalive = time.time()

                try:
                    # Yield events from queue
                    while True:
                        try:
                            # Wait for events with timeout to allow periodic checks
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            # Normalize timestamp to string
                            timestamp = event.get("timestamp")
                            if isinstance(timestamp, datetime):
                                timestamp = timestamp.isoformat()
                            elif isinstance(timestamp, int | float):
                                # Convert numeric epoch timestamp to ISO string
                                timestamp = datetime.fromtimestamp(timestamp).isoformat()
                            elif timestamp is None or timestamp == "":
                                timestamp = datetime.now().isoformat()
                            else:
                                # Ensure it's a string
                                timestamp = str(timestamp)

                            # Extract the event type, preferring UI event_type over raw type
                            event_type = event.get("event_type") or event.get("type", "unknown")

                            # Normalize execution_id key (handle both executionId and execution_id)
                            exec_id_str = (
                                event.get("execution_id")
                                or event.get("executionId")
                                or str(exec_id)
                            )

                            # For node events, restructure the data to match frontend expectations
                            if event_type in ["NODE_STARTED", "NODE_COMPLETED", "NODE_FAILED"]:
                                # node_id is at the top level of the event, not in data
                                # data field contains the payload (node_type, output, etc.)
                                event_data = event.get("data", {})

                                # Handle None case explicitly
                                if event_data is None:
                                    event_data = {}
                                elif isinstance(event_data, str):
                                    try:
                                        event_data = json.loads(event_data)
                                    except Exception:
                                        event_data = {}

                                # Extract node_id from top level, other fields from data payload
                                data = {
                                    "node_id": event.get("node_id"),  # From top level
                                    "node_type": event_data.get("node_type"),  # From data payload
                                    "status": "RUNNING"
                                    if event_type == "NODE_STARTED"
                                    else "COMPLETED"
                                    if event_type == "NODE_COMPLETED"
                                    else "FAILED",
                                    "output": event_data.get("output"),
                                    "metrics": event_data.get("metrics"),
                                    "error": event_data.get("error"),
                                }
                                # Remove None values
                                data = {k: v for k, v in data.items() if v is not None}
                            elif event_type == "NODE_STATUS_CHANGED":
                                # Handle NODE_STATUS_CHANGED events
                                # node_id is at top level, status and other data in payload
                                event_data = event.get("data", {})
                                if event_data is None:
                                    event_data = {}
                                elif isinstance(event_data, str):
                                    try:
                                        event_data = json.loads(event_data)
                                    except Exception:
                                        event_data = {}

                                # Combine top-level node_id with data payload
                                data = {
                                    "node_id": event.get("node_id"),  # From top level
                                    "status": event_data.get("status"),
                                    "timestamp": event_data.get("timestamp")
                                    or event.get("timestamp"),
                                    **{
                                        k: v
                                        for k, v in event_data.items()
                                        if k not in ["node_id", "status", "timestamp"]
                                    },
                                }
                            elif event_type == "EXECUTION_STATUS_CHANGED":
                                # Handle EXECUTION_STATUS_CHANGED events for execution start/stop
                                data = event.get("data", {})
                                if data is None:
                                    data = {}
                                elif isinstance(data, str):
                                    try:
                                        data = json.loads(data)
                                    except Exception:
                                        data = {}
                            else:
                                # For other events, pass through the data as-is
                                data = {
                                    k: v
                                    for k, v in event.items()
                                    if k not in ["type", "timestamp", "executionId"]
                                }

                            yield ExecutionUpdate(
                                execution_id=exec_id_str,
                                event_type=event_type,
                                data=serialize_for_json(data),
                                timestamp=str(timestamp),
                            )
                            # Update last keepalive time after sending an event
                            last_keepalive = time.time()
                        except TimeoutError:
                            # Send keepalive if configured and interval has passed
                            current_time = time.time()
                            if (
                                keepalive_interval > 0
                                and (current_time - last_keepalive) >= keepalive_interval
                            ):
                                yield ExecutionUpdate(
                                    execution_id=str(exec_id),
                                    event_type=EventType.KEEPALIVE.value,
                                    data={"type": "keepalive"},
                                    timestamp=datetime.now().isoformat(),
                                )
                                last_keepalive = current_time
                                logger.debug(f"Sent keepalive for execution {exec_id}")

                            # Check if execution still exists periodically
                            if state_store:
                                execution = await state_store.get_state(str(exec_id))
                                # Don't break immediately when execution becomes inactive
                                # Allow time for final events to be sent
                                if not execution:
                                    break
                                # If execution is complete, yield one more update then break
                                if not execution.is_active and execution.status in (
                                    Status.COMPLETED,
                                    Status.FAILED,
                                    Status.ABORTED,
                                    Status.MAXITER_REACHED,
                                ):
                                    # Send final status update
                                    yield ExecutionUpdate(
                                        execution_id=str(exec_id),
                                        event_type="EXECUTION_STATUS_CHANGED",
                                        data={"status": execution.status, "is_final": True},
                                        timestamp=datetime.now().isoformat(),
                                    )
                                    break
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(
                        connection_id, str(exec_id)
                    )
                    await message_router.unregister_connection(connection_id)

            except asyncio.CancelledError:
                logger.info(f"Subscription cancelled for execution: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in execution subscription: {e}")
                raise

        @strawberry.subscription
        async def node_updates(
            self, execution_id: strawberry.ID, node_id: str | None = None
        ) -> AsyncGenerator[JSON]:
            """Subscribe to node-specific updates within an execution."""
            message_router = registry.get(MESSAGE_ROUTER)

            if not message_router:
                logger.error("Message router not available for subscriptions")
                return

            exec_id = ExecutionID(str(execution_id))

            try:
                # Create a queue for receiving events
                event_queue = asyncio.Queue()
                connection_id = f"graphql-node-subscription-{id(event_queue)}"

                # Define handler to put events in queue
                async def event_handler(message):
                    # Serialize the entire message to ensure all nested objects are JSON-safe
                    serialized_message = serialize_for_json(message)
                    await event_queue.put(serialized_message)

                # Register connection and subscribe to execution
                await message_router.register_connection(connection_id, event_handler)
                await message_router.subscribe_connection_to_execution(connection_id, str(exec_id))

                # Get keepalive settings
                settings = get_settings()
                keepalive_interval = settings.messaging.ws_keepalive_sec
                last_keepalive = time.time()

                try:
                    # Yield node update events from queue
                    while True:
                        try:
                            # Wait for events with timeout
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            # Filter for node updates
                            if event.get("type") in [
                                EventType.NODE_STATUS_CHANGED.value,
                                EventType.NODE_PROGRESS.value,
                            ]:
                                data = event.get("data", {})
                                # If node_id specified, filter for that node
                                if node_id and data.get("node_id") != node_id:
                                    continue
                                # Yield the data in the format expected by the frontend
                                yield serialize_for_json(data)
                                last_keepalive = time.time()
                        except TimeoutError:
                            # Send keepalive if configured and interval has passed
                            current_time = time.time()
                            if (
                                keepalive_interval > 0
                                and (current_time - last_keepalive) >= keepalive_interval
                            ):
                                yield serialize_for_json(
                                    {"type": "keepalive", "timestamp": datetime.now().isoformat()}
                                )
                                last_keepalive = current_time
                                logger.debug(f"Sent keepalive for node updates {exec_id}")
                            # Continue waiting for events
                            continue
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(
                        connection_id, str(exec_id)
                    )
                    await message_router.unregister_connection(connection_id)

            except asyncio.CancelledError:
                logger.info(f"Node subscription cancelled for execution: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in node subscription: {e}")
                raise

        @strawberry.subscription
        async def interactive_prompts(self, execution_id: strawberry.ID) -> AsyncGenerator[JSON]:
            """Subscribe to interactive prompt requests."""
            message_router = registry.get(MESSAGE_ROUTER)

            if not message_router:
                logger.error("Message router not available for subscriptions")
                return

            exec_id = ExecutionID(str(execution_id))

            try:
                # Create a queue for receiving events
                event_queue = asyncio.Queue()
                connection_id = f"graphql-prompt-subscription-{id(event_queue)}"

                # Define handler to put events in queue
                async def event_handler(message):
                    # Serialize the entire message to ensure all nested objects are JSON-safe
                    serialized_message = serialize_for_json(message)
                    await event_queue.put(serialized_message)

                # Register connection and subscribe to execution
                await message_router.register_connection(connection_id, event_handler)
                await message_router.subscribe_connection_to_execution(connection_id, str(exec_id))

                # Get keepalive settings
                settings = get_settings()
                keepalive_interval = settings.messaging.ws_keepalive_sec
                last_keepalive = time.time()

                try:
                    # Yield interactive prompt events from queue
                    while True:
                        try:
                            # Wait for events with timeout
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            # Filter for interactive prompts
                            if event.get("type") == EventType.INTERACTIVE_PROMPT.value:
                                yield serialize_for_json(event.get("data", {}))
                                last_keepalive = time.time()
                        except TimeoutError:
                            # Send keepalive if configured and interval has passed
                            current_time = time.time()
                            if (
                                keepalive_interval > 0
                                and (current_time - last_keepalive) >= keepalive_interval
                            ):
                                yield serialize_for_json(
                                    {"type": "keepalive", "timestamp": datetime.now().isoformat()}
                                )
                                last_keepalive = current_time
                                logger.debug(f"Sent keepalive for interactive prompts {exec_id}")
                            # Continue waiting for events
                            continue
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(
                        connection_id, str(exec_id)
                    )
                    await message_router.unregister_connection(connection_id)

            except asyncio.CancelledError:
                logger.info(f"Interactive prompt subscription cancelled: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in interactive prompt subscription: {e}")
                raise

        @strawberry.subscription
        async def execution_logs(self, execution_id: strawberry.ID) -> AsyncGenerator[JSON]:
            """Subscribe to execution log events."""
            message_router = registry.get(MESSAGE_ROUTER)

            if not message_router:
                logger.error("Message router not available for subscriptions")
                return

            exec_id = ExecutionID(str(execution_id))

            try:
                # Create a queue for receiving events
                event_queue = asyncio.Queue()
                connection_id = f"graphql-log-subscription-{id(event_queue)}"

                # Define handler to put events in queue
                async def event_handler(message):
                    # Serialize the entire message to ensure all nested objects are JSON-safe
                    serialized_message = serialize_for_json(message)
                    await event_queue.put(serialized_message)

                # Register connection and subscribe to execution
                await message_router.register_connection(connection_id, event_handler)
                await message_router.subscribe_connection_to_execution(connection_id, str(exec_id))

                # Get keepalive settings
                settings = get_settings()
                keepalive_interval = settings.messaging.ws_keepalive_sec
                last_keepalive = time.time()

                try:
                    # Yield log events from queue
                    while True:
                        try:
                            # Wait for events with timeout
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            # Filter for execution logs
                            if event.get("type") == EventType.EXECUTION_LOG.value:
                                yield serialize_for_json(event.get("data", {}))
                                last_keepalive = time.time()
                        except TimeoutError:
                            # Send keepalive if configured and interval has passed
                            current_time = time.time()
                            if (
                                keepalive_interval > 0
                                and (current_time - last_keepalive) >= keepalive_interval
                            ):
                                yield serialize_for_json(
                                    {"type": "keepalive", "timestamp": datetime.now().isoformat()}
                                )
                                last_keepalive = current_time
                                logger.debug(f"Sent keepalive for execution logs {exec_id}")
                            # Continue waiting for events
                            continue
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(
                        connection_id, str(exec_id)
                    )
                    await message_router.unregister_connection(connection_id)

            except asyncio.CancelledError:
                logger.info(f"Execution log subscription cancelled: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in execution log subscription: {e}")
                raise

    return Subscription
