"""Simplified MessageRouter adapter implementing the DomainEventBus port."""

import logging
from dataclasses import asdict
from typing import Optional, cast
from uuid import uuid4

from dipeo.domain.events.ports import (
    DomainEventBus,
    EventHandler,
    EventSubscription,
    EventPriority,
)
from dipeo.domain.events import (
    DomainEvent,
    EventType,
    ExecutionStartedPayload,
    ExecutionCompletedPayload,
    NodeStartedPayload,
    NodeCompletedPayload,
    NodeErrorPayload,
)
from dipeo.diagram_generated import Status
from .message_router import MessageRouter

logger = logging.getLogger(__name__)


class MessageRouterEventBusAdapter(DomainEventBus):
    """Simplified adapter that implements DomainEventBus using MessageRouter.
    
    Key improvements:
    1. Leverages DomainEvent's dataclass structure for automatic serialization
    2. Cleaner separation of concerns
    3. Reduced code duplication
    """
    
    def __init__(self, message_router: MessageRouter):
        self.message_router = message_router
        self._subscriptions: dict[str, EventSubscription] = {}
        
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event by converting it to MessageRouter format."""
        # Convert domain event to MessageRouter format
        message = self._serialize_event(event)
        
        # Route through MessageRouter for execution events
        if event.scope.execution_id:
            await self.message_router.broadcast_to_execution(
                event.scope.execution_id,
                message
            )
        else:
            logger.debug(f"Non-execution event published: {event.type}")
            
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically."""
        # Group events by execution_id for efficient routing
        execution_events: dict[str, list[dict]] = {}
        
        for event in events:
            if event.scope.execution_id:
                if event.scope.execution_id not in execution_events:
                    execution_events[event.scope.execution_id] = []
                execution_events[event.scope.execution_id].append(
                    self._serialize_event(event)
                )
        
        # Broadcast each execution's events
        for execution_id, messages in execution_events.items():
            for message in messages:
                await self.message_router.broadcast_to_execution(
                    execution_id,
                    message
                )
    
    async def subscribe(
        self,
        event_types: list[EventType],
        handler: EventHandler,
        filter_expression: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL
    ) -> EventSubscription:
        """Subscribe to domain events.
        
        Note: Currently used primarily by infrastructure components.
        Application layer uses observers for now.
        """
        subscription = EventSubscription(
            subscription_id=str(uuid4()),
            event_types=event_types,
            handler=handler,
            filter_expression=filter_expression,
            priority=priority,
            active=True,
        )
        
        self._subscriptions[subscription.subscription_id] = subscription
        
        # Note: Actual subscription logic would integrate with MessageRouter
        # For now, this is a placeholder for future infrastructure subscriptions
        
        return subscription
    
    async def unsubscribe(self, subscription: EventSubscription) -> None:
        """Unsubscribe from domain events."""
        self._subscriptions.pop(subscription.subscription_id, None)
        subscription.active = False
    
    async def start(self) -> None:
        """Start the event bus."""
        await self.message_router.initialize()
    
    async def stop(self) -> None:
        """Stop the event bus and clean up resources."""
        await self.message_router.cleanup()
    
    def _serialize_event(self, event: DomainEvent) -> dict:
        """Simplified serialization leveraging DomainEvent's dataclass structure."""
        # Base message with common fields
        message = {
            "type": self._get_message_type(event),
            "timestamp": event.occurred_at.isoformat(),
            "event_id": event.id,
            "execution_id": event.scope.execution_id,
        }
        
        # Add optional scope fields
        if event.scope.node_id:
            message["node_id"] = event.scope.node_id
        if event.scope.connection_id:
            message["connection_id"] = event.scope.connection_id
        if event.scope.parent_execution_id:
            message["parent_execution_id"] = event.scope.parent_execution_id
        
        # Serialize payload
        message["data"] = self._serialize_payload(event)
        
        return message
    
    def _get_message_type(self, event: DomainEvent) -> str:
        """Map event types for backward compatibility."""
        # Map new event types to legacy message types for backward compatibility
        compatibility_mapping = {
            EventType.EXECUTION_STARTED: EventType.EXECUTION_STATUS_CHANGED,
            EventType.EXECUTION_COMPLETED: EventType.EXECUTION_STATUS_CHANGED,
            EventType.NODE_STARTED: EventType.NODE_STATUS_CHANGED,
            EventType.NODE_COMPLETED: EventType.NODE_STATUS_CHANGED,
            EventType.NODE_ERROR: EventType.NODE_STATUS_CHANGED,
        }
        
        mapped_type = compatibility_mapping.get(event.type, event.type)
        return mapped_type.value
    
    def _serialize_payload(self, event: DomainEvent) -> dict:
        """Serialize event payload with specific handling for backward compatibility."""
        if not event.payload:
            return {"timestamp": event.occurred_at.isoformat(), **event.meta}
        
        # Convert payload to dict
        payload_dict = asdict(event.payload)
        payload_dict["timestamp"] = event.occurred_at.isoformat()
        
        # Special handling for backward compatibility
        if event.type == EventType.EXECUTION_STARTED:
            payload = cast(ExecutionStartedPayload, event.payload)
            payload_dict["status"] = Status.RUNNING.value
            payload_dict["parent_execution_id"] = event.scope.parent_execution_id
            
        elif event.type == EventType.EXECUTION_COMPLETED:
            payload = cast(ExecutionCompletedPayload, event.payload)
            payload_dict["status"] = payload.status.value
            
        elif event.type in (EventType.NODE_STARTED, EventType.NODE_COMPLETED, EventType.NODE_ERROR):
            # Add node_id to data for node events
            payload_dict["node_id"] = event.scope.node_id
            
            # Handle NodeState serialization
            if "state" in payload_dict and payload_dict["state"]:
                state = payload_dict["state"]
                if isinstance(state, dict):
                    # Extract relevant fields from state
                    if "status" in state:
                        payload_dict["status"] = state["status"]
                    if "started_at" in state:
                        payload_dict["started_at"] = state["started_at"]
                    if "ended_at" in state:
                        payload_dict["ended_at"] = state["ended_at"]
                    if "node_type" in state:
                        payload_dict["node_type"] = state["node_type"]
                # Remove the nested state object
                del payload_dict["state"]
            
            # Add specific status for different node events
            if event.type == EventType.NODE_STARTED:
                payload_dict["status"] = Status.RUNNING.value
            elif event.type == EventType.NODE_COMPLETED:
                payload_dict.setdefault("status", Status.COMPLETED.value)
            elif event.type == EventType.NODE_ERROR:
                payload_dict["status"] = Status.FAILED.value
        
        return payload_dict


# Backward compatibility adapter
class MessageBusCompatibilityAdapter:
    """Provides MessageBus interface for backward compatibility."""
    
    def __init__(self, message_router: MessageRouter):
        self.message_router = message_router
        
    async def initialize(self) -> None:
        """Initialize the message bus."""
        await self.message_router.initialize()
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.message_router.cleanup()
    
    async def register_connection(self, connection_id: str, handler) -> None:
        """Register a connection handler."""
        await self.message_router.register_connection(connection_id, handler)
    
    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a connection."""
        await self.message_router.unregister_connection(connection_id)
    
    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        """Broadcast message to all connections subscribed to an execution."""
        await self.message_router.broadcast_to_execution(execution_id, message)
    
    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Subscribe a connection to execution updates."""
        await self.message_router.subscribe_connection_to_execution(
            connection_id, execution_id
        )
    
    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        """Unsubscribe a connection from execution updates."""
        await self.message_router.unsubscribe_connection_from_execution(
            connection_id, execution_id
        )
    
    def get_stats(self) -> dict:
        """Get bus statistics."""
        return self.message_router.get_stats()