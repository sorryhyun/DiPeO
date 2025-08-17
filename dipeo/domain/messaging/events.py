"""Domain events for messaging."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class DomainEvent:
    """Base domain event."""
    
    event_id: str
    timestamp: datetime
    aggregate_id: str


@dataclass
class ExecutionStarted(DomainEvent):
    """Execution has started."""
    
    diagram_id: Optional[str]
    variables: dict[str, Any]


@dataclass
class ExecutionUpdated(DomainEvent):
    """Execution state has been updated."""
    
    status: str
    error: Optional[str] = None


@dataclass
class ExecutionCompleted(DomainEvent):
    """Execution has completed."""
    
    status: str
    error: Optional[str] = None


@dataclass
class NodeExecutionStarted(DomainEvent):
    """Node execution has started."""
    
    node_id: str
    node_type: str


@dataclass
class NodeOutputAppended(DomainEvent):
    """Output has been appended to a node."""
    
    node_id: str
    output: Any
    is_exception: bool = False
    token_usage: Optional[dict] = None


@dataclass
class NodeExecutionCompleted(DomainEvent):
    """Node execution has completed."""
    
    node_id: str
    status: str
    error: Optional[str] = None


@dataclass
class TokenUsageUpdated(DomainEvent):
    """Token usage has been updated."""
    
    token_usage: dict
    cumulative: bool = True