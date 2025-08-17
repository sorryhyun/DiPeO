"""Domain event contracts with versioned schemas."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from dipeo.diagram_generated import NodeState, Status

from .types import EventType, EventPriority, EventVersion


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base domain event with metadata."""
    
    event_type: EventType = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: EventVersion = EventVersion.V2
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None  # For tracing related events
    causation_id: Optional[str] = None    # ID of the event that caused this one
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class ExecutionEvent(DomainEvent):
    """Base event for execution-related events."""
    
    execution_id: str
    diagram_id: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class NodeEvent(ExecutionEvent):
    """Base event for node-related events."""
    
    node_id: str
    node_type: Optional[str] = None


# Execution lifecycle events

@dataclass(frozen=True, kw_only=True)
class ExecutionStartedEvent(ExecutionEvent):
    """Execution has started."""
    
    event_type: EventType = field(default=EventType.EXECUTION_STARTED, init=False)
    variables: dict[str, Any] = field(default_factory=dict)
    parent_execution_id: Optional[str] = None  # For sub-diagrams
    initiated_by: Optional[str] = None  # User or system that started execution


@dataclass(frozen=True, kw_only=True)
class ExecutionCompletedEvent(ExecutionEvent):
    """Execution has completed successfully."""
    
    event_type: EventType = field(default=EventType.EXECUTION_COMPLETED, init=False)
    status: Status = Status.COMPLETED
    total_duration_ms: Optional[int] = None
    total_tokens_used: Optional[int] = None
    node_count: Optional[int] = None


@dataclass(frozen=True, kw_only=True)
class ExecutionErrorEvent(ExecutionEvent):
    """Execution has failed with an error."""
    
    event_type: EventType = field(default=EventType.EXECUTION_ERROR, init=False)
    error: str
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    failed_node_id: Optional[str] = None


# Node lifecycle events

@dataclass(frozen=True, kw_only=True)
class NodeStartedEvent(NodeEvent):
    """Node execution has started."""
    
    event_type: EventType = field(default=EventType.NODE_STARTED, init=False)
    inputs: Optional[dict[str, Any]] = None  # Resolved inputs
    iteration: Optional[int] = None  # For loop nodes


@dataclass(frozen=True, kw_only=True)
class NodeCompletedEvent(NodeEvent):
    """Node execution has completed."""
    
    event_type: EventType = field(default=EventType.NODE_COMPLETED, init=False)
    state: NodeState
    duration_ms: Optional[int] = None
    token_usage: Optional[dict] = None
    output_summary: Optional[str] = None  # Brief description of output


@dataclass(frozen=True, kw_only=True)
class NodeErrorEvent(NodeEvent):
    """Node execution has failed."""
    
    event_type: EventType = field(default=EventType.NODE_ERROR, init=False)
    error: str
    error_type: Optional[str] = None
    retryable: bool = False
    retry_count: int = 0
    max_retries: int = 3


@dataclass(frozen=True, kw_only=True)
class NodeOutputEvent(NodeEvent):
    """Node has produced output (for streaming)."""
    
    event_type: EventType = field(default=EventType.NODE_OUTPUT, init=False)
    output: Any
    is_partial: bool = False  # For streaming outputs
    sequence_number: Optional[int] = None  # For ordering partial outputs


# Monitoring and metrics events

@dataclass(frozen=True, kw_only=True)
class MetricsCollectedEvent(ExecutionEvent):
    """Performance metrics have been collected."""
    
    event_type: EventType = field(default=EventType.METRICS_COLLECTED, init=False)
    metrics: dict[str, Any] = field(default_factory=dict)
    # Example metrics:
    # - avg_node_duration_ms
    # - total_tokens_used
    # - parallel_execution_efficiency
    # - memory_usage_mb


@dataclass(frozen=True, kw_only=True)
class OptimizationSuggestedEvent(ExecutionEvent):
    """Optimization opportunity has been identified."""
    
    event_type: EventType = field(default=EventType.OPTIMIZATION_SUGGESTED, init=False)
    suggestion_type: str  # e.g., "parallelize_nodes", "reduce_context"
    affected_nodes: list[str] = field(default_factory=list)
    expected_improvement: Optional[str] = None
    description: str = ""


# External integration events

@dataclass(frozen=True, kw_only=True)
class WebhookReceivedEvent(DomainEvent):
    """Webhook has been received."""
    
    event_type: EventType = field(default=EventType.WEBHOOK_RECEIVED, init=False)
    webhook_id: str
    source: str  # e.g., "github", "slack"
    payload: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    execution_id: Optional[str] = None  # If webhook triggers an execution


# Logging events

@dataclass(frozen=True, kw_only=True)
class ExecutionLogEvent(ExecutionEvent):
    """Log entry for execution."""
    
    event_type: EventType = field(default=EventType.EXECUTION_LOG, init=False)
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message: str
    logger_name: str
    node_id: Optional[str] = None
    extra_fields: dict[str, Any] = field(default_factory=dict)