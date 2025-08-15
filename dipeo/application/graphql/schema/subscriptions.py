"""GraphQL subscriptions for real-time updates."""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Any

import strawberry

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.core.ports import MessageRouterPort, StateStorePort
from strawberry.scalars import JSON as JSONScalar
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import EventType

logger = logging.getLogger(__name__)


def serialize_for_json(obj: Any, seen: set = None, max_depth: int = 10) -> Any:
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
    if obj is None or isinstance(obj, (bool, int, float, str)):
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
        elif isinstance(obj, (list, tuple)):
            return [serialize_for_json(item, seen, max_depth - 1) for item in obj]
        elif isinstance(obj, (set, frozenset)):
            return [serialize_for_json(item, seen, max_depth - 1) for item in obj]
        elif hasattr(obj, "__dict__"):
            # Handle Pydantic models or other objects with __dict__
            # Skip private attributes to avoid internal state
            return {k: serialize_for_json(v, seen, max_depth - 1) 
                   for k, v in obj.__dict__.items() 
                   if not k.startswith('_')}
        else:
            return str(obj)  # Fallback to string representation
    finally:
        # Remove from seen set when done
        seen.discard(obj_id)

# Service keys
MESSAGE_ROUTER = ServiceKey[MessageRouterPort]("message_router")
STATE_STORE = ServiceKey[StateStorePort]("state_store")


@strawberry.type
class ExecutionUpdate:
    """Real-time execution update."""
    execution_id: str
    event_type: str
    data: JSONScalar
    timestamp: str


def create_subscription_type(registry: ServiceRegistry) -> type:
    """Create a Subscription type with injected service registry."""
    
    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def execution_updates(
            self, execution_id: strawberry.ID
        ) -> AsyncGenerator[ExecutionUpdate, None]:
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
                
                try:
                    # Yield events from queue
                    while True:
                        try:
                            # Wait for events with timeout to allow periodic checks
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            timestamp = event.get("timestamp")
                            if not timestamp:
                                timestamp = datetime.now().isoformat()
                            elif isinstance(timestamp, datetime):
                                timestamp = timestamp.isoformat()
                            
                            # Extract the event type
                            event_type = event.get("type", "unknown")
                            
                            # For node events, restructure the data to match frontend expectations
                            if event_type in ["NODE_STARTED", "NODE_COMPLETED", "NODE_FAILED"]:
                                # Extract node-specific fields and rename to snake_case
                                data = {
                                    "node_id": event.get("nodeId"),
                                    "node_type": event.get("nodeType"),
                                    "status": event.get("status"),
                                    "output": event.get("output"),
                                    "metrics": event.get("metrics"),
                                    "error": event.get("error"),
                                }
                                # Remove None values
                                data = {k: v for k, v in data.items() if v is not None}
                            elif event_type == "NODE_STATUS_CHANGED":
                                # Handle NODE_STATUS_CHANGED events from UnifiedEventObserver
                                # The data is already in the correct format
                                data = event.get("data", {})
                            elif event_type == "EXECUTION_STATUS_CHANGED":
                                # Handle EXECUTION_STATUS_CHANGED events for execution start/stop
                                data = event.get("data", {})
                            else:
                                # For other events, pass through the data as-is
                                data = {k: v for k, v in event.items() if k not in ["type", "timestamp", "executionId"]}
                            
                            yield ExecutionUpdate(
                                execution_id=str(exec_id),
                                event_type=event_type,
                                data=serialize_for_json(data),
                                timestamp=str(timestamp),
                            )
                        except asyncio.TimeoutError:
                            # Check if execution still exists periodically
                            if state_store:
                                execution = await state_store.get_state(str(exec_id))
                                if not execution or not execution.is_active:
                                    break
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(connection_id, str(exec_id))
                    await message_router.unregister_connection(connection_id)
                    
            except asyncio.CancelledError:
                logger.info(f"Subscription cancelled for execution: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in execution subscription: {e}")
                raise
        
        @strawberry.subscription
        async def node_updates(
            self, execution_id: strawberry.ID, node_id: Optional[str] = None
        ) -> AsyncGenerator[JSONScalar, None]:
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
                
                try:
                    # Yield node update events from queue
                    while True:
                        try:
                            # Wait for events with timeout
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            # Filter for node updates
                            if event.get("type") in [EventType.NODE_STATUS_CHANGED.value, EventType.NODE_PROGRESS.value]:
                                data = event.get("data", {})
                                # If node_id specified, filter for that node
                                if node_id and data.get("node_id") != node_id:
                                    continue
                                # Yield the data in the format expected by the frontend
                                yield serialize_for_json(data)
                        except asyncio.TimeoutError:
                            # Continue waiting for events
                            continue
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(connection_id, str(exec_id))
                    await message_router.unregister_connection(connection_id)
                        
            except asyncio.CancelledError:
                logger.info(f"Node subscription cancelled for execution: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in node subscription: {e}")
                raise
        
        @strawberry.subscription
        async def interactive_prompts(
            self, execution_id: strawberry.ID
        ) -> AsyncGenerator[JSONScalar, None]:
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
                
                try:
                    # Yield interactive prompt events from queue
                    while True:
                        try:
                            # Wait for events with timeout
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            # Filter for interactive prompts
                            if event.get("type") == EventType.INTERACTIVE_PROMPT.value:
                                yield serialize_for_json(event.get("data", {}))
                        except asyncio.TimeoutError:
                            # Continue waiting for events
                            continue
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(connection_id, str(exec_id))
                    await message_router.unregister_connection(connection_id)
                        
            except asyncio.CancelledError:
                logger.info(f"Interactive prompt subscription cancelled: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in interactive prompt subscription: {e}")
                raise
        
        @strawberry.subscription
        async def execution_logs(
            self, execution_id: strawberry.ID
        ) -> AsyncGenerator[JSONScalar, None]:
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
                
                try:
                    # Yield log events from queue
                    while True:
                        try:
                            # Wait for events with timeout
                            event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                            # Filter for execution logs
                            if event.get("type") == EventType.EXECUTION_LOG.value:
                                yield serialize_for_json(event.get("data", {}))
                        except asyncio.TimeoutError:
                            # Continue waiting for events
                            continue
                finally:
                    # Clean up subscription
                    await message_router.unsubscribe_connection_from_execution(connection_id, str(exec_id))
                    await message_router.unregister_connection(connection_id)
                        
            except asyncio.CancelledError:
                logger.info(f"Execution log subscription cancelled: {exec_id}")
                raise
            except Exception as e:
                logger.error(f"Error in execution log subscription: {e}")
                raise
    
    return Subscription