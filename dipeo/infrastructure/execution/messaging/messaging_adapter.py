"""Adapters that bridge existing messaging infrastructure to new domain ports."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dipeo.domain.events import EventType
from dipeo.domain.events.ports import MessageBus as MessageRouterPort
from dipeo.domain.events import MessageBus
from dipeo.domain.events.contracts import DomainEvent
from dipeo.infrastructure.execution.messaging import MessageRouter

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
            execution_id = event.scope.execution_id
            payload = event.payload
            
            # Build data dict from payload attributes
            data = {}
            if payload:
                # Extract common fields from various payload types
                for field in ['node_id', 'node_type', 'status', 'error_message', 
                             'output', 'metrics', 'variables', 'state']:
                    if hasattr(payload, field):
                        value = getattr(payload, field)
                        if value is not None:
                            # Map error_message to error for backward compatibility
                            if field == 'error_message':
                                data['error'] = value
                            else:
                                data[field] = value
            
            # Add node_id from scope if present
            if event.scope.node_id:
                data['node_id'] = event.scope.node_id
            
            message = {
                "type": event.type.value,
                "execution_id": execution_id,
                "timestamp": event.occurred_at.timestamp() if event.occurred_at else None,
                "event_id": event.id,
                "data": data
            }
        else:
            # Original SimpleExecutionEvent handling
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

