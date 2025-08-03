"""Observer that publishes events to message router for web-based executions."""

import logging
from datetime import datetime

from dipeo.core.ports import ExecutionObserver, MessageRouterPort
from dipeo.models import (
    ExecutionStatus,
    NodeExecutionStatus,
    NodeState,
    EventType,
)

try:
    from .scoped_observer import ObserverMetadata
except ImportError:
    from dipeo.application.execution.observers import ObserverMetadata

logger = logging.getLogger(__name__)


class EventPublishingObserver(ExecutionObserver):
    """Observer that publishes execution events to message router.
    
    This observer is used for web-based executions to provide real-time
    updates through GraphQL subscriptions.
    """
    
    def __init__(self, message_router: MessageRouterPort, execution_runtime=None):
        self.message_router = message_router
        self.execution_runtime = execution_runtime
        
        # Configure metadata for sub-diagram propagation
        self.metadata = ObserverMetadata(
            propagate_to_sub=True,
            scope_to_execution=False,
            filter_events=None  # Publish all events
        )
    
    async def on_execution_start(self, execution_id: str, diagram_id: str | None):
        await self._publish_event(
            execution_id,
            EventType.EXECUTION_STATUS_CHANGED,
            {
                "status": ExecutionStatus.RUNNING.value,
                "diagram_id": diagram_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    async def on_node_start(self, execution_id: str, node_id: str):
        # Get node type if runtime is available
        node_type = None
        if self.execution_runtime:
            from dipeo.models import NodeID
            node = self.execution_runtime.get_node(NodeID(node_id))
            if node:
                node_type = node.type.value if hasattr(node.type, 'value') else str(node.type)
        
        await self._publish_event(
            execution_id,
            EventType.NODE_STATUS_CHANGED,
            {
                "node_id": node_id,
                "status": NodeExecutionStatus.RUNNING.value,
                "node_type": node_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    async def on_node_complete(self, execution_id: str, node_id: str, state: NodeState):
        # Get node type if runtime is available
        node_type = None
        if self.execution_runtime:
            from dipeo.models import NodeID
            node = self.execution_runtime.get_node(NodeID(node_id))
            if node:
                node_type = node.type.value if hasattr(node.type, 'value') else str(node.type)
        
        await self._publish_event(
            execution_id,
            EventType.NODE_STATUS_CHANGED,
            {
                "node_id": node_id,
                "status": state.status.value,
                "node_type": node_type,
                "output": state.output if state.output else None,
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "ended_at": state.ended_at.isoformat() if state.ended_at else None,
                "token_usage": state.token_usage.model_dump() if state.token_usage else None,
                "tokens_used": state.token_usage.total if state.token_usage else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        # Get node type if runtime is available
        node_type = None
        if self.execution_runtime:
            from dipeo.models import NodeID
            node = self.execution_runtime.get_node(NodeID(node_id))
            if node:
                node_type = node.type.value if hasattr(node.type, 'value') else str(node.type)
        
        await self._publish_event(
            execution_id,
            EventType.NODE_STATUS_CHANGED,
            {
                "node_id": node_id,
                "status": NodeExecutionStatus.FAILED.value,
                "node_type": node_type,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    async def on_execution_complete(self, execution_id: str):
        await self._publish_event(
            execution_id,
            EventType.EXECUTION_STATUS_CHANGED,
            {
                "status": ExecutionStatus.COMPLETED.value,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    async def on_execution_error(self, execution_id: str, error: str):
        await self._publish_event(
            execution_id,
            EventType.EXECUTION_ERROR,
            {
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    async def _publish_event(self, execution_id: str, event_type: EventType, data: dict):
        """Publish event to message router."""
        event = {
            "type": event_type.value,
            "execution_id": execution_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Publish to all connections subscribed to this execution
        try:
            await self.message_router.broadcast_to_execution(execution_id, event)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")