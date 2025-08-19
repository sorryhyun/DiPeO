"""Domain events for execution lifecycle and monitoring."""

from .contracts import (
    DomainEvent,
    EventScope,
    # Payloads
    ExecutionStartedPayload,
    ExecutionCompletedPayload,
    ExecutionErrorPayload,
    NodeStartedPayload,
    NodeCompletedPayload,
    NodeErrorPayload,
    NodeOutputPayload,
    MetricsCollectedPayload,
    OptimizationSuggestedPayload,
    WebhookReceivedPayload,
    ExecutionLogPayload,
    EventPayload,
    PAYLOAD_BY_TYPE,
    # Factory functions
    execution_started,
    execution_completed,
    execution_error,
    node_started,
    node_completed,
    node_error,
)

from .ports import DomainEventBus, EventHandler, EventSubscription, EventEmitter, EventConsumer, MessageBus
from .types import EventType, EventPriority, EventVersion

# Backward compatibility - create wrapper classes that can be instantiated
class ExecutionEvent(DomainEvent):
    """Legacy execution event wrapper - DEPRECATED."""
    pass

class NodeEvent(DomainEvent):
    """Legacy node event wrapper - DEPRECATED."""
    pass

# Legacy event classes that can be instantiated with keyword arguments
def ExecutionStartedEvent(**kwargs):
    """Legacy factory for execution started events."""
    execution_id = kwargs.pop('execution_id')
    return DomainEvent(
        type=EventType.EXECUTION_STARTED,
        scope=EventScope(
            execution_id=execution_id,
            parent_execution_id=kwargs.pop('parent_execution_id', None)
        ),
        payload=ExecutionStartedPayload(
            variables=kwargs.pop('variables', {}),
            initiated_by=kwargs.pop('initiated_by', None),
            diagram_id=kwargs.pop('diagram_id', None)
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def ExecutionCompletedEvent(**kwargs):
    """Legacy factory for execution completed events."""
    execution_id = kwargs.pop('execution_id')
    return DomainEvent(
        type=EventType.EXECUTION_COMPLETED,
        scope=EventScope(execution_id=execution_id),
        payload=ExecutionCompletedPayload(
            status=kwargs.pop('status', None),
            total_duration_ms=kwargs.pop('total_duration_ms', None),
            total_tokens_used=kwargs.pop('total_tokens_used', None),
            node_count=kwargs.pop('node_count', None)
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def ExecutionErrorEvent(**kwargs):
    """Legacy factory for execution error events."""
    execution_id = kwargs.pop('execution_id')
    return DomainEvent(
        type=EventType.EXECUTION_ERROR,
        scope=EventScope(execution_id=execution_id),
        payload=ExecutionErrorPayload(
            error_message=kwargs.pop('error', ''),
            error_type=kwargs.pop('error_type', None),
            stack_trace=kwargs.pop('stack_trace', None),
            failed_node_id=kwargs.pop('failed_node_id', None)
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def NodeStartedEvent(**kwargs):
    """Legacy factory for node started events."""
    execution_id = kwargs.pop('execution_id')
    node_id = kwargs.pop('node_id')
    return DomainEvent(
        type=EventType.NODE_STARTED,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=NodeStartedPayload(
            state=kwargs.pop('state', None),
            node_type=kwargs.pop('node_type', None),
            inputs=kwargs.pop('inputs', None),
            iteration=kwargs.pop('iteration', None)
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def NodeCompletedEvent(**kwargs):
    """Legacy factory for node completed events."""
    execution_id = kwargs.pop('execution_id')
    node_id = kwargs.pop('node_id')
    return DomainEvent(
        type=EventType.NODE_COMPLETED,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=NodeCompletedPayload(
            state=kwargs.pop('state', None),
            output=kwargs.pop('output', None),
            duration_ms=kwargs.pop('duration_ms', None),
            token_usage=kwargs.pop('token_usage', None),
            output_summary=kwargs.pop('output_summary', None)
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def NodeErrorEvent(**kwargs):
    """Legacy factory for node error events."""
    execution_id = kwargs.pop('execution_id')
    node_id = kwargs.pop('node_id')
    # Create a default error state if not provided
    from dipeo.diagram_generated import NodeState, Status
    state = kwargs.pop('state', None)
    if not state:
        state = NodeState(
            status=Status.FAILED,
            error=kwargs.get('error', '')
        )
    return DomainEvent(
        type=EventType.NODE_ERROR,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=NodeErrorPayload(
            state=state,
            error_message=kwargs.pop('error', ''),
            error_type=kwargs.pop('error_type', None),
            retryable=kwargs.pop('retryable', False),
            retry_count=kwargs.pop('retry_count', 0),
            max_retries=kwargs.pop('max_retries', 3)
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def NodeOutputEvent(**kwargs):
    """Legacy factory for node output events."""
    execution_id = kwargs.pop('execution_id')
    node_id = kwargs.pop('node_id')
    return DomainEvent(
        type=EventType.NODE_OUTPUT,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=NodeOutputPayload(
            output=kwargs.pop('output', None),
            is_partial=kwargs.pop('is_partial', False),
            sequence_number=kwargs.pop('sequence_number', None)
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def MetricsCollectedEvent(**kwargs):
    """Legacy factory for metrics collected events."""
    execution_id = kwargs.pop('execution_id')
    return DomainEvent(
        type=EventType.METRICS_COLLECTED,
        scope=EventScope(execution_id=execution_id),
        payload=MetricsCollectedPayload(
            metrics=kwargs.pop('metrics', {})
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def OptimizationSuggestedEvent(**kwargs):
    """Legacy factory for optimization suggested events."""
    execution_id = kwargs.pop('execution_id')
    return DomainEvent(
        type=EventType.OPTIMIZATION_SUGGESTED,
        scope=EventScope(execution_id=execution_id),
        payload=OptimizationSuggestedPayload(
            suggestion_type=kwargs.pop('suggestion_type', ''),
            affected_nodes=kwargs.pop('affected_nodes', []),
            expected_improvement=kwargs.pop('expected_improvement', None),
            description=kwargs.pop('description', '')
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def WebhookReceivedEvent(**kwargs):
    """Legacy factory for webhook received events."""
    execution_id = kwargs.pop('execution_id', 'system')
    return DomainEvent(
        type=EventType.WEBHOOK_RECEIVED,
        scope=EventScope(execution_id=execution_id),
        payload=WebhookReceivedPayload(
            webhook_id=kwargs.pop('webhook_id', ''),
            source=kwargs.pop('source', ''),
            payload=kwargs.pop('payload', {}),
            headers=kwargs.pop('headers', {})
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

def ExecutionLogEvent(**kwargs):
    """Legacy factory for execution log events."""
    execution_id = kwargs.pop('execution_id')
    node_id = kwargs.pop('node_id', None)
    return DomainEvent(
        type=EventType.EXECUTION_LOG,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=ExecutionLogPayload(
            level=kwargs.pop('level', 'INFO'),
            message=kwargs.pop('message', ''),
            logger_name=kwargs.pop('logger_name', 'unknown'),
            extra_fields=kwargs.pop('extra_fields', {})
        ),
        **{k: v for k, v in kwargs.items() if k in ['correlation_id', 'causation_id', 'priority', 'version']}
    )

__all__ = [
    # Core contracts
    "DomainEvent",
    "EventScope",
    # Payloads
    "ExecutionStartedPayload",
    "ExecutionCompletedPayload",
    "ExecutionErrorPayload",
    "NodeStartedPayload",
    "NodeCompletedPayload",
    "NodeErrorPayload",
    "NodeOutputPayload",
    "MetricsCollectedPayload",
    "OptimizationSuggestedPayload",
    "WebhookReceivedPayload",
    "ExecutionLogPayload",
    "EventPayload",
    "PAYLOAD_BY_TYPE",
    # Factory functions
    "execution_started",
    "execution_completed",
    "execution_error",
    "node_started",
    "node_completed",
    "node_error",
    # Legacy classes (backward compatibility)
    "ExecutionEvent",
    "NodeEvent",
    "ExecutionStartedEvent",
    "ExecutionCompletedEvent",
    "ExecutionErrorEvent",
    "NodeStartedEvent",
    "NodeCompletedEvent",
    "NodeErrorEvent",
    "NodeOutputEvent",
    "MetricsCollectedEvent",
    "OptimizationSuggestedEvent",
    "WebhookReceivedEvent",
    "ExecutionLogEvent",
    # Ports
    "DomainEventBus",
    "EventHandler",
    "EventSubscription",
    "EventEmitter",
    "EventConsumer",
    "MessageBus",
    # Types
    "EventType",
    "EventPriority",
    "EventVersion",
]