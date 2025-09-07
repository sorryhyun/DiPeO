"""Domain event contracts with unified event structure and typed payloads."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Union
from uuid import uuid4

from dipeo.diagram_generated.domain_models import NodeState
from dipeo.diagram_generated.enums import EventType, Status

from .types import EventPriority, EventVersion


@dataclass(frozen=True, slots=True)
class EventScope:
    """Scope information for an event."""

    execution_id: str
    node_id: str | None = None  # when node-scoped
    connection_id: str | None = None  # GraphQL / client socket, optional
    parent_execution_id: str | None = None  # sub-diagrams


# --- Payloads (typed, tiny) --------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecutionStartedPayload:
    """Payload for execution started event."""

    variables: dict[str, Any] = field(default_factory=dict)
    initiated_by: str | None = None
    diagram_id: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutionCompletedPayload:
    """Payload for execution completed event."""

    status: Status = Status.COMPLETED
    total_duration_ms: int | None = None
    total_tokens_used: int | None = None
    node_count: int | None = None


@dataclass(frozen=True, slots=True)
class ExecutionErrorPayload:
    """Payload for execution error event."""

    error_message: str
    error_type: str | None = None
    stack_trace: str | None = None
    failed_node_id: str | None = None


@dataclass(frozen=True, slots=True)
class NodeStartedPayload:
    """Payload for node started event."""

    state: NodeState
    node_type: str | None = None
    inputs: dict[str, Any] | None = None
    iteration: int | None = None  # For loop nodes


@dataclass(frozen=True, slots=True)
class NodeCompletedPayload:
    """Payload for node completed event."""

    state: NodeState
    output: Any = None
    duration_ms: int | None = None
    token_usage: dict | None = None
    output_summary: str | None = None


@dataclass(frozen=True, slots=True)
class NodeErrorPayload:
    """Payload for node error event."""

    state: NodeState
    error_message: str
    error_type: str | None = None
    retryable: bool = False
    retry_count: int = 0
    max_retries: int = 3


@dataclass(frozen=True, slots=True)
class NodeOutputPayload:
    """Payload for node output event (streaming)."""

    output: Any
    is_partial: bool = False
    sequence_number: int | None = None


@dataclass(frozen=True, slots=True)
class MetricsCollectedPayload:
    """Payload for metrics collected event."""

    metrics: dict[str, Any] = field(default_factory=dict)
    # Example metrics:
    # - avg_node_duration_ms
    # - total_tokens_used
    # - parallel_execution_efficiency
    # - memory_usage_mb


@dataclass(frozen=True, slots=True)
class OptimizationSuggestedPayload:
    """Payload for optimization suggested event."""

    suggestion_type: str  # e.g., "parallelize_nodes", "reduce_context"
    affected_nodes: list[str] = field(default_factory=list)
    expected_improvement: str | None = None
    description: str = ""


@dataclass(frozen=True, slots=True)
class WebhookReceivedPayload:
    """Payload for webhook received event."""

    webhook_id: str
    source: str  # e.g., "github", "slack"
    payload: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionLogPayload:
    """Payload for execution log event."""

    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message: str
    logger_name: str
    extra_fields: dict[str, Any] = field(default_factory=dict)


# Union type for all payloads
EventPayload = (
    ExecutionStartedPayload
    | ExecutionCompletedPayload
    | ExecutionErrorPayload
    | NodeStartedPayload
    | NodeCompletedPayload
    | NodeErrorPayload
    | NodeOutputPayload
    | MetricsCollectedPayload
    | OptimizationSuggestedPayload
    | WebhookReceivedPayload
    | ExecutionLogPayload
)

# Optional: mapping to validate at creation time
PAYLOAD_BY_TYPE: dict[EventType, type[EventPayload]] = {
    EventType.EXECUTION_STARTED: ExecutionStartedPayload,
    EventType.EXECUTION_COMPLETED: ExecutionCompletedPayload,
    EventType.EXECUTION_ERROR: ExecutionErrorPayload,
    EventType.NODE_STARTED: NodeStartedPayload,
    EventType.NODE_COMPLETED: NodeCompletedPayload,
    EventType.NODE_ERROR: NodeErrorPayload,
    EventType.NODE_OUTPUT: NodeOutputPayload,
    EventType.METRICS_COLLECTED: MetricsCollectedPayload,
    EventType.OPTIMIZATION_SUGGESTED: OptimizationSuggestedPayload,
    EventType.WEBHOOK_RECEIVED: WebhookReceivedPayload,
    EventType.EXECUTION_LOG: ExecutionLogPayload,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Unified domain event with typed payloads."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: EventType
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: EventVersion = EventVersion.V2
    priority: EventPriority = EventPriority.NORMAL

    scope: EventScope
    payload: EventPayload | None = None

    meta: dict[str, Any] = field(default_factory=dict)  # freeform tags

    # Legacy fields for traceability
    correlation_id: str | None = None  # For tracing related events
    causation_id: str | None = None  # ID of the event that caused this one

    def __post_init__(self):
        """Validate payload matches event type."""
        if self.payload is not None and self.type in PAYLOAD_BY_TYPE:
            expected_type = PAYLOAD_BY_TYPE[self.type]
            if not isinstance(self.payload, expected_type):
                raise ValueError(
                    f"Payload type {type(self.payload).__name__} does not match "
                    f"expected type {expected_type.__name__} for event type {self.type}"
                )


# === Convenience Factory Functions ===


def execution_started(execution_id: str, **kwargs) -> DomainEvent:
    """Create an execution started event."""
    return DomainEvent(
        type=EventType.EXECUTION_STARTED,
        scope=EventScope(execution_id=execution_id),
        payload=ExecutionStartedPayload(**kwargs),
    )


def execution_completed(execution_id: str, **kwargs) -> DomainEvent:
    """Create an execution completed event."""
    return DomainEvent(
        type=EventType.EXECUTION_COMPLETED,
        scope=EventScope(execution_id=execution_id),
        payload=ExecutionCompletedPayload(**kwargs),
    )


def execution_error(execution_id: str, error_message: str, **kwargs) -> DomainEvent:
    """Create an execution error event."""
    return DomainEvent(
        type=EventType.EXECUTION_ERROR,
        scope=EventScope(execution_id=execution_id),
        payload=ExecutionErrorPayload(error_message=error_message, **kwargs),
    )


def node_started(execution_id: str, node_id: str, state: NodeState, **kwargs) -> DomainEvent:
    """Create a node started event."""
    return DomainEvent(
        type=EventType.NODE_STARTED,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=NodeStartedPayload(state=state, **kwargs),
    )


def node_completed(execution_id: str, node_id: str, state: NodeState, **kwargs) -> DomainEvent:
    """Create a node completed event."""
    return DomainEvent(
        type=EventType.NODE_COMPLETED,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=NodeCompletedPayload(state=state, **kwargs),
    )


def node_error(
    execution_id: str, node_id: str, state: NodeState, error_message: str, **kwargs
) -> DomainEvent:
    """Create a node error event."""
    return DomainEvent(
        type=EventType.NODE_ERROR,
        scope=EventScope(execution_id=execution_id, node_id=node_id),
        payload=NodeErrorPayload(state=state, error_message=error_message, **kwargs),
    )
