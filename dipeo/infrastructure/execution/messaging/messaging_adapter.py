"""Adapters that bridge existing messaging infrastructure to new domain ports."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dipeo.domain.events import EventType
from dipeo.domain.events.ports import MessageBus as MessageRouterPort
from dipeo.domain.events import DomainEventBus, MessageBus
from dipeo.domain.events.contracts import DomainEvent
from dipeo.infrastructure.execution.messaging import MessageRouter
from dipeo.infrastructure.events.adapters.legacy import AsyncEventBus


@dataclass
class SimpleExecutionEvent:
    """Simple execution event for AsyncEventBus compatibility."""
    type: EventType
    execution_id: str
    timestamp: float
    data: dict[str, Any]


class MessageBusAdapter(MessageBus):
    """Adapter wrapping MessageRouter to implement domain MessageBus port."""

    def __init__(self, router: MessageRouterPort | None = None):
        self._router = router or MessageRouter()

    async def initialize(self) -> None:
        await self._router.initialize()

    async def cleanup(self) -> None:
        await self._router.cleanup()
    
    async def emit(self, event: DomainEvent | SimpleExecutionEvent) -> None:
        """Emit an execution event by broadcasting to the execution."""
        # Handle both domain and simple execution event types
        if isinstance(event, DomainEvent):
            # Convert DomainEvent to message dict
            message = {
                "type": event.event_type.value if hasattr(event, 'event_type') else "EXECUTION_UPDATE",
                "execution_id": getattr(event, 'execution_id', ''),
                "timestamp": event.timestamp.timestamp() if hasattr(event.timestamp, 'timestamp') else event.timestamp,
                "event_id": getattr(event, 'event_id', None),
                "data": {
                    "node_id": getattr(event, 'node_id', None),
                    "node_type": getattr(event, 'node_type', None),
                    "status": getattr(event, 'status', None),
                    "error": getattr(event, 'error', None),
                    "output": getattr(event, 'output', None),
                    "metrics": getattr(event, 'metrics', None),
                    **getattr(event, 'metadata', {})
                }
            }
            # Remove None values from data
            message["data"] = {k: v for k, v in message["data"].items() if v is not None}
            execution_id = message["execution_id"]
        else:
            # Original ExecutionEvent handling
            message = {
                "type": event.type.value,
                "execution_id": event.execution_id,
                "timestamp": event.timestamp,
                "data": event.data or {}
            }
            execution_id = event.execution_id
            
        # Broadcast to all connections watching this execution
        await self._router.broadcast_to_execution(execution_id, message)

    async def register_connection(self, connection_id: str, handler: Callable) -> None:
        await self._router.register_connection(connection_id, handler)

    async def unregister_connection(self, connection_id: str) -> None:
        await self._router.unregister_connection(connection_id)

    async def broadcast_to_execution(self, execution_id: str, message: dict) -> None:
        await self._router.broadcast_to_execution(execution_id, message)

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        await self._router.subscribe_connection_to_execution(connection_id, execution_id)

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ) -> None:
        await self._router.unsubscribe_connection_from_execution(connection_id, execution_id)

    def get_stats(self) -> dict:
        return self._router.get_stats()


class DomainEventBusAdapter(DomainEventBus):
    """Adapter that bridges domain events to the core event bus."""

    def __init__(self, event_bus: AsyncEventBus | None = None):
        self._event_bus = event_bus or AsyncEventBus()
        self._domain_handlers: dict[type[DomainEvent], list[Callable]] = {}

    async def initialize(self) -> None:
        """Initialize the event bus."""
        await self._event_bus.start()

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._event_bus.stop()

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event by converting it to core ExecutionEvent."""
        # Map domain events to core event types - comprehensive mapping
        event_type_map = {
            # Execution lifecycle events
            "ExecutionStartedEvent": EventType.EXECUTION_STARTED,
            "ExecutionCompletedEvent": EventType.EXECUTION_COMPLETED,
            "ExecutionErrorEvent": EventType.EXECUTION_ERROR,
            "ExecutionStatusChangedEvent": EventType.EXECUTION_STATUS_CHANGED,
            
            # Node lifecycle events
            "NodeStartedEvent": EventType.NODE_STARTED,
            "NodeCompletedEvent": EventType.NODE_COMPLETED,
            "NodeErrorEvent": EventType.NODE_ERROR,
            "NodeOutputEvent": EventType.NODE_OUTPUT,
            "NodeStatusChangedEvent": EventType.NODE_STATUS_CHANGED,
            "NodeProgressEvent": EventType.NODE_PROGRESS,
            
            # Metrics and monitoring
            "MetricsCollectedEvent": EventType.METRICS_COLLECTED,
            "OptimizationSuggestedEvent": EventType.OPTIMIZATION_SUGGESTED,
            
            # External integrations
            "WebhookReceivedEvent": EventType.WEBHOOK_RECEIVED,
            
            # Interactive events
            "InteractivePromptEvent": EventType.INTERACTIVE_PROMPT,
            "InteractiveResponseEvent": EventType.INTERACTIVE_RESPONSE,
            
            # Logging and updates
            "ExecutionLogEvent": EventType.EXECUTION_LOG,
            "ExecutionUpdateEvent": EventType.EXECUTION_UPDATE,
            
            # Legacy/compatibility mappings
            "ExecutionStarted": EventType.EXECUTION_STARTED,
            "ExecutionCompleted": EventType.EXECUTION_COMPLETED,
            "ExecutionUpdated": EventType.EXECUTION_UPDATE,
            "NodeExecutionStarted": EventType.NODE_STARTED,
            "NodeExecutionCompleted": EventType.NODE_COMPLETED,
            "NodeOutputAppended": EventType.NODE_OUTPUT,
        }
        
        event_class_name = event.__class__.__name__
        core_event_type = event_type_map.get(event_class_name, EventType.EXECUTION_UPDATE)
        
        # Create ExecutionEvent from domain event
        # Try to get execution_id from either 'execution_id' or 'aggregate_id' (base DomainEvent)
        execution_id = getattr(event, 'execution_id', getattr(event, 'aggregate_id', ''))
        
        # Get timestamp from domain event or use current time
        import time
        if hasattr(event, 'timestamp'):
            timestamp = event.timestamp.timestamp() if hasattr(event.timestamp, 'timestamp') else time.time()
        else:
            timestamp = time.time()
        
        # Create simple ExecutionEvent for AsyncEventBus compatibility
        execution_event = SimpleExecutionEvent(
            execution_id=execution_id,
            type=core_event_type,
            timestamp=timestamp,
            data={
                'domain_event': event_class_name,
                'payload': event.to_dict() if hasattr(event, 'to_dict') else vars(event),
            },
        )
        
        await self._event_bus.emit(execution_event)
        
        # Also call domain handlers directly
        handlers = self._domain_handlers.get(type(event), [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # Log but don't fail
                import logging
                logging.getLogger(__name__).error(f"Domain event handler failed: {e}")

    async def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], None]
    ) -> None:
        """Subscribe to a domain event type."""
        if event_type not in self._domain_handlers:
            self._domain_handlers[event_type] = []
        self._domain_handlers[event_type].append(handler)

    async def unsubscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], None]
    ) -> None:
        """Unsubscribe from a domain event type."""
        if event_type in self._domain_handlers:
            try:
                self._domain_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not in list