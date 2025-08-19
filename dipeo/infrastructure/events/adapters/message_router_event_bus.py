"""MessageRouter adapter implementing the DomainEventBus port.

This adapter bridges domain events to the existing MessageRouter infrastructure,
handling all serialization and format conversion at the infrastructure layer.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from dipeo.domain.events.ports import (
    DomainEventBus,
    EventHandler,
    EventSubscription,
    EventPriority,
)
from dipeo.domain.events.contracts import (
    DomainEvent,
    ExecutionEvent,
    NodeEvent,
    ExecutionStartedEvent,
    ExecutionCompletedEvent,
    ExecutionErrorEvent,
    NodeStartedEvent,
    NodeCompletedEvent,
    NodeErrorEvent,
    NodeOutputEvent,
    ExecutionLogEvent,
)
from dipeo.domain.events.types import EventType
from dipeo.diagram_generated import Status
from dipeo.infrastructure.execution.messaging.message_router import MessageRouter

logger = logging.getLogger(__name__)


class MessageRouterEventBusAdapter(DomainEventBus):
    """Adapter that implements DomainEventBus using MessageRouter.
    
    This adapter:
    1. Receives typed domain events
    2. Serializes them to the format expected by MessageRouter
    3. Routes them through the existing infrastructure
    
    All serialization and infrastructure concerns are kept here,
    while the domain and application layers work with pure domain events.
    """
    
    def __init__(self, message_router: MessageRouter):
        self.message_router = message_router
        self._subscriptions: dict[str, EventSubscription] = {}
        
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event by converting it to MessageRouter format.
        
        Args:
            event: The domain event to publish
        """
        # Convert domain event to MessageRouter format
        message = self._serialize_event(event)
        
        # Route through MessageRouter if this is an execution event
        if isinstance(event, ExecutionEvent):
            await self.message_router.broadcast_to_execution(
                event.execution_id,
                message
            )
        else:
            # For non-execution events, handle differently or log
            logger.debug(f"Non-execution event published: {event.event_type}")
            
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically.
        
        Args:
            events: List of domain events to publish
        """
        # Group events by execution_id for efficient routing
        execution_events: dict[str, list[dict]] = {}
        
        for event in events:
            if isinstance(event, ExecutionEvent):
                if event.execution_id not in execution_events:
                    execution_events[event.execution_id] = []
                execution_events[event.execution_id].append(
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
        
        Note: This is primarily used by infrastructure components.
        Application layer uses observers for now.
        
        Args:
            event_types: Types of events to subscribe to
            handler: Handler to process events
            filter_expression: Optional filter expression
            priority: Priority for event processing
            
        Returns:
            Subscription object that can be used to unsubscribe
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
        """Unsubscribe from domain events.
        
        Args:
            subscription: The subscription to cancel
        """
        self._subscriptions.pop(subscription.subscription_id, None)
        subscription.active = False
    
    async def start(self) -> None:
        """Start the event bus."""
        await self.message_router.initialize()
    
    async def stop(self) -> None:
        """Stop the event bus and clean up resources."""
        await self.message_router.cleanup()
    
    def _serialize_event(self, event: DomainEvent) -> dict:
        """Serialize a domain event to MessageRouter format.
        
        This method handles all serialization, keeping it in the infrastructure layer.
        
        Args:
            event: Domain event to serialize
            
        Returns:
            Dictionary in MessageRouter format
        """
        base_message = {
            "type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.event_id,
        }
        
        # Add execution_id for execution events
        if isinstance(event, ExecutionEvent):
            base_message["execution_id"] = event.execution_id
        
        # Serialize event-specific data based on type
        if isinstance(event, ExecutionStartedEvent):
            # Map to EXECUTION_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.EXECUTION_STATUS_CHANGED.value
            base_message["data"] = {
                "status": Status.RUNNING.value,
                "diagram_id": event.diagram_id,
                "variables": event.variables,
                "parent_execution_id": event.parent_execution_id,
                "initiated_by": event.initiated_by,
                "timestamp": event.timestamp.isoformat(),
            }
        
        elif isinstance(event, ExecutionCompletedEvent):
            # Map to EXECUTION_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.EXECUTION_STATUS_CHANGED.value
            base_message["data"] = {
                "status": event.status.value,
                "total_duration_ms": event.total_duration_ms,
                "total_tokens_used": event.total_tokens_used,
                "node_count": event.node_count,
                "timestamp": event.timestamp.isoformat(),
            }
        
        elif isinstance(event, ExecutionErrorEvent):
            # Keep EXECUTION_ERROR as is
            base_message["data"] = {
                "error": event.error,
                "error_type": event.error_type,
                "stack_trace": event.stack_trace,
                "failed_node_id": event.failed_node_id,
                "timestamp": event.timestamp.isoformat(),
            }
        
        elif isinstance(event, NodeStartedEvent):
            # Map to NODE_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.NODE_STATUS_CHANGED.value
            base_message["data"] = {
                "node_id": event.node_id,
                "node_type": event.node_type,
                "status": Status.RUNNING.value,
                "inputs": event.inputs,
                "iteration": event.iteration,
                "timestamp": event.timestamp.isoformat(),
            }
        
        elif isinstance(event, NodeCompletedEvent):
            # Map to NODE_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.NODE_STATUS_CHANGED.value
            base_message["data"] = {
                "node_id": event.node_id,
                "node_type": event.node_type,
                "status": event.state.status.value,
                "output": event.state.output if event.state.output else None,
                "started_at": event.state.started_at.isoformat() if event.state.started_at else None,
                "ended_at": event.state.ended_at.isoformat() if event.state.ended_at else None,
                "duration_ms": event.duration_ms,
                "token_usage": event.token_usage,
                "tokens_used": event.token_usage.get("total") if event.token_usage else None,
                "output_summary": event.output_summary,
                "timestamp": event.timestamp.isoformat(),
            }
        
        elif isinstance(event, NodeErrorEvent):
            # Map to NODE_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.NODE_STATUS_CHANGED.value
            base_message["data"] = {
                "node_id": event.node_id,
                "node_type": event.node_type,
                "status": Status.FAILED.value,
                "error": event.error,
                "error_type": event.error_type,
                "retryable": event.retryable,
                "retry_count": event.retry_count,
                "max_retries": event.max_retries,
                "timestamp": event.timestamp.isoformat(),
            }
        
        elif isinstance(event, NodeOutputEvent):
            base_message["data"] = {
                "node_id": event.node_id,
                "node_type": event.node_type,
                "output": event.output,
                "is_partial": event.is_partial,
                "sequence_number": event.sequence_number,
                "timestamp": event.timestamp.isoformat(),
            }
        
        elif isinstance(event, ExecutionLogEvent):
            base_message["data"] = {
                "level": event.level,
                "message": event.message,
                "logger": event.logger_name,
                "node_id": event.node_id,
                **event.extra_fields,
            }
        
        else:
            # Generic serialization for other event types
            base_message["data"] = {
                "timestamp": event.timestamp.isoformat(),
                **event.metadata,
            }
        
        return base_message


# Backwards compatibility: Also implement MessageBus interface
# This allows gradual migration from MessageBus to DomainEventBus
class MessageBusCompatibilityAdapter:
    """Provides MessageBus interface for backwards compatibility."""
    
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