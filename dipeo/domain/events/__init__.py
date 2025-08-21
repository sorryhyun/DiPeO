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

from .ports import DomainEventBus, EventHandler, EventSubscription, EventEmitter, EventConsumer, MessageBus, EventFilter
from .types import EventType, EventPriority, EventVersion
from .publisher import EventPublisher
from .filters import (
    ExecutionScopeFilter,
    NodeScopeFilter,
    EventTypeFilter,
    CompositeFilter,
    SubDiagramFilter,
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
    # Ports
    "DomainEventBus",
    "EventHandler",
    "EventSubscription",
    "EventEmitter",
    "EventConsumer",
    "MessageBus",
    "EventFilter",
    # Types
    "EventType",
    "EventPriority",
    "EventVersion",
    # Publisher
    "EventPublisher",
    # Filters
    "ExecutionScopeFilter",
    "NodeScopeFilter",
    "EventTypeFilter",
    "CompositeFilter",
    "SubDiagramFilter",
]