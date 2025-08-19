"""MessageRouter adapter implementing the DomainEventBus port.

This adapter bridges domain events to the existing MessageRouter infrastructure,
handling all serialization and format conversion at the infrastructure layer.
"""

import logging
from dataclasses import asdict
from datetime import datetime
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
    EventScope,
    ExecutionStartedPayload,
    ExecutionCompletedPayload,
    ExecutionErrorPayload,
    NodeStartedPayload,
    NodeCompletedPayload,
    NodeErrorPayload,
    NodeOutputPayload,
    ExecutionLogPayload,
    MetricsCollectedPayload,
    OptimizationSuggestedPayload,
    WebhookReceivedPayload,
    EventType,
)
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
        
        # Route through MessageRouter for execution events
        if event.scope.execution_id:
            await self.message_router.broadcast_to_execution(
                event.scope.execution_id,
                message
            )
        else:
            # For non-execution events, handle differently or log
            logger.debug(f"Non-execution event published: {event.type}")
            
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events atomically.
        
        Args:
            events: List of domain events to publish
        """
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
            "type": event.type.value,
            "timestamp": event.occurred_at.isoformat(),
            "event_id": event.id,
        }
        
        # Add scope information
        base_message["execution_id"] = event.scope.execution_id
        if event.scope.node_id:
            base_message["node_id"] = event.scope.node_id
        if event.scope.connection_id:
            base_message["connection_id"] = event.scope.connection_id
        if event.scope.parent_execution_id:
            base_message["parent_execution_id"] = event.scope.parent_execution_id
        
        # Serialize event payload based on type
        if event.type == EventType.EXECUTION_STARTED:
            # Map to EXECUTION_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.EXECUTION_STATUS_CHANGED.value
            payload = cast(ExecutionStartedPayload, event.payload)
            base_message["data"] = {
                "status": Status.RUNNING.value,
                "diagram_id": payload.diagram_id,
                "variables": payload.variables,
                "initiated_by": payload.initiated_by,
                "parent_execution_id": event.scope.parent_execution_id,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.EXECUTION_COMPLETED:
            # Map to EXECUTION_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.EXECUTION_STATUS_CHANGED.value
            payload = cast(ExecutionCompletedPayload, event.payload)
            base_message["data"] = {
                "status": payload.status.value,
                "total_duration_ms": payload.total_duration_ms,
                "total_tokens_used": payload.total_tokens_used,
                "node_count": payload.node_count,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.EXECUTION_ERROR:
            payload = cast(ExecutionErrorPayload, event.payload)
            base_message["data"] = {
                "error": payload.error_message,
                "error_type": payload.error_type,
                "stack_trace": payload.stack_trace,
                "failed_node_id": payload.failed_node_id,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.NODE_STARTED:
            # Map to NODE_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.NODE_STATUS_CHANGED.value
            payload = cast(NodeStartedPayload, event.payload)
            base_message["data"] = {
                "node_id": event.scope.node_id,
                "node_type": payload.node_type,
                "status": Status.RUNNING.value,
                "inputs": payload.inputs,
                "iteration": payload.iteration,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.NODE_COMPLETED:
            # Map to NODE_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.NODE_STATUS_CHANGED.value
            payload = cast(NodeCompletedPayload, event.payload)
            base_message["data"] = {
                "node_id": event.scope.node_id,
                "node_type": self._get_node_type_from_payload(payload),
                "status": payload.state.status.value if payload.state else Status.COMPLETED.value,
                "output": payload.output,
                "started_at": payload.state.started_at if payload.state else None,
                "ended_at": payload.state.ended_at if payload.state else None,
                "duration_ms": payload.duration_ms,
                "token_usage": payload.token_usage,
                "tokens_used": payload.token_usage.get("total") if payload.token_usage else None,
                "output_summary": payload.output_summary,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.NODE_ERROR:
            # Map to NODE_STATUS_CHANGED for backward compatibility
            base_message["type"] = EventType.NODE_STATUS_CHANGED.value
            payload = cast(NodeErrorPayload, event.payload)
            base_message["data"] = {
                "node_id": event.scope.node_id,
                "node_type": self._get_node_type_from_payload(payload),
                "status": Status.FAILED.value,
                "error": payload.error_message,
                "error_type": payload.error_type,
                "retryable": payload.retryable,
                "retry_count": payload.retry_count,
                "max_retries": payload.max_retries,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.NODE_OUTPUT:
            payload = cast(NodeOutputPayload, event.payload)
            base_message["data"] = {
                "node_id": event.scope.node_id,
                "output": payload.output,
                "is_partial": payload.is_partial,
                "sequence_number": payload.sequence_number,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.EXECUTION_LOG:
            payload = cast(ExecutionLogPayload, event.payload)
            base_message["data"] = {
                "level": payload.level,
                "message": payload.message,
                "logger": payload.logger_name,
                "node_id": event.scope.node_id,
                **payload.extra_fields,
            }
        
        elif event.type == EventType.METRICS_COLLECTED:
            payload = cast(MetricsCollectedPayload, event.payload)
            base_message["data"] = {
                "metrics": payload.metrics,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.OPTIMIZATION_SUGGESTED:
            payload = cast(OptimizationSuggestedPayload, event.payload)
            base_message["data"] = {
                "suggestion_type": payload.suggestion_type,
                "affected_nodes": payload.affected_nodes,
                "expected_improvement": payload.expected_improvement,
                "description": payload.description,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        elif event.type == EventType.WEBHOOK_RECEIVED:
            payload = cast(WebhookReceivedPayload, event.payload)
            base_message["data"] = {
                "webhook_id": payload.webhook_id,
                "source": payload.source,
                "payload": payload.payload,
                "headers": payload.headers,
                "timestamp": event.occurred_at.isoformat(),
            }
        
        else:
            # Generic serialization for other event types
            base_message["data"] = {
                "timestamp": event.occurred_at.isoformat(),
                **event.meta,
            }
            if event.payload:
                # Try to convert payload to dict if it has that capability
                if hasattr(event.payload, '__dict__'):
                    base_message["data"]["payload"] = asdict(event.payload)
        
        return base_message
    
    def _get_node_type_from_payload(self, payload) -> Optional[str]:
        """Extract node type from payload if available."""
        # Check if node_type is stored in the payload
        if hasattr(payload, 'node_type'):
            return payload.node_type
        # Check if it's stored in the state
        if hasattr(payload, 'state') and hasattr(payload.state, 'node_type'):
            return payload.state.node_type
        return None


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