"""Backward compatibility re-export for messaging module.

This module maintains backward compatibility for imports during the migration
of messaging to events bounded context.

DEPRECATED: Use dipeo.domain.events instead.
"""

# Re-export everything from events
from dipeo.domain.events import (
    MessageBus,
    DomainEventBus,
)

# Re-export from contracts
from dipeo.domain.events.contracts import (
    DomainEvent,
    ExecutionStartedEvent as ExecutionStarted,
    ExecutionCompletedEvent as ExecutionCompleted,
    ExecutionErrorEvent as ExecutionError,
    NodeStartedEvent as NodeExecutionStarted,
    NodeCompletedEvent as NodeExecutionCompleted,
    NodeOutputEvent as NodeOutputAppended,
    MetricsCollectedEvent as TokenUsageUpdated,
)

# Map ExecutionUpdated to ExecutionCompleted (closest match)
ExecutionUpdated = ExecutionCompleted

# Re-export all event types from events.contracts
from dipeo.domain.events.contracts import *

# Re-export all ports from events.ports
from dipeo.domain.events.ports import *

__all__ = [
    "MessageBus",
    "DomainEventBus",
    "DomainEvent",
    "ExecutionStarted",
    "ExecutionUpdated",
    "ExecutionCompleted",
    "NodeExecutionStarted",
    "NodeOutputAppended",
    "NodeExecutionCompleted",
    "TokenUsageUpdated",
]