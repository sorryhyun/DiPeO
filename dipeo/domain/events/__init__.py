"""Domain events for execution lifecycle and monitoring."""

from .contracts import (
    PAYLOAD_BY_TYPE,
    DomainEvent,
    EventPayload,
    EventScope,
    ExecutionCompletedPayload,
    ExecutionErrorPayload,
    ExecutionLogPayload,
    # Payloads
    ExecutionStartedPayload,
    MetricsCollectedPayload,
    NodeCompletedPayload,
    NodeErrorPayload,
    NodeOutputPayload,
    NodeStartedPayload,
    OptimizationSuggestedPayload,
    WebhookReceivedPayload,
    execution_completed,
    execution_error,
    # Factory functions
    execution_started,
    node_completed,
    node_error,
    node_started,
)
from .filters import (
    CompositeFilter,
    EventTypeFilter,
    ExecutionScopeFilter,
    NodeScopeFilter,
    SubDiagramFilter,
)
from .publisher import EventPublisher
from .types import EventPriority, EventType, EventVersion
from .unified_ports import EventBus, EventFilter, EventHandler, EventStore, EventSubscription

__all__ = [
    "PAYLOAD_BY_TYPE",
    "CompositeFilter",
    # Core contracts
    "DomainEvent",
    # Unified Ports
    "EventBus",
    "EventFilter",
    "EventHandler",
    "EventPayload",
    "EventPriority",
    # Publisher
    "EventPublisher",
    "EventScope",
    "EventStore",
    "EventSubscription",
    # Types
    "EventType",
    "EventTypeFilter",
    "EventVersion",
    "ExecutionCompletedPayload",
    "ExecutionErrorPayload",
    "ExecutionLogPayload",
    # Filters
    "ExecutionScopeFilter",
    # Payloads
    "ExecutionStartedPayload",
    "MetricsCollectedPayload",
    "NodeCompletedPayload",
    "NodeErrorPayload",
    "NodeOutputPayload",
    "NodeScopeFilter",
    "NodeStartedPayload",
    "OptimizationSuggestedPayload",
    "SubDiagramFilter",
    "WebhookReceivedPayload",
    "execution_completed",
    "execution_error",
    # Factory functions
    "execution_started",
    "node_completed",
    "node_error",
    "node_started",
]
