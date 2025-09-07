"""Common event filter implementations for domain event filtering."""

from dataclasses import dataclass

from .contracts import DomainEvent
from .ports import EventFilter
from .types import EventType


@dataclass
class ExecutionScopeFilter:
    """Filter events based on execution scope.

    This filter is used to scope events to specific executions,
    particularly useful for sub-diagram execution isolation.
    """

    execution_id: str
    include_children: bool = True

    def matches(self, event: DomainEvent) -> bool:
        """Check if event belongs to the scoped execution."""
        if not event.scope.execution_id:
            return False

        event_exec_id = str(event.scope.execution_id)

        if self.include_children:
            # Include events from this execution and its sub-executions
            return event_exec_id.startswith(self.execution_id)
        else:
            # Only include events from this exact execution
            return event_exec_id == self.execution_id


@dataclass
class NodeScopeFilter:
    """Filter events based on node scope."""

    node_ids: set[str]

    def matches(self, event: DomainEvent) -> bool:
        """Check if event belongs to one of the specified nodes."""
        if not event.scope.node_id:
            # Non-node events pass through
            return True
        return event.scope.node_id in self.node_ids


@dataclass
class EventTypeFilter:
    """Filter events based on event type."""

    allowed_types: set[EventType]

    def matches(self, event: DomainEvent) -> bool:
        """Check if event type is allowed."""
        return event.type in self.allowed_types


@dataclass
class CompositeFilter:
    """Combines multiple filters with AND/OR logic."""

    filters: list[EventFilter]
    require_all: bool = True  # True = AND, False = OR

    def matches(self, event: DomainEvent) -> bool:
        """Check if event matches composite filter criteria."""
        if not self.filters:
            return True

        if self.require_all:
            # AND logic - all filters must match
            return all(f.matches(event) for f in self.filters)
        else:
            # OR logic - at least one filter must match
            return any(f.matches(event) for f in self.filters)


@dataclass
class SubDiagramFilter:
    """Filter for sub-diagram execution events.

    This replaces the ScopedObserver functionality with proper event filtering.
    """

    parent_execution_id: str
    propagate_to_sub: bool = True
    scope_to_execution: bool = False
    allowed_event_types: set[EventType] | None = None

    def matches(self, event: DomainEvent) -> bool:
        """Check if event should be propagated based on sub-diagram rules."""
        if not event.scope.execution_id:
            return False

        event_exec_id = str(event.scope.execution_id)

        # Check execution scope
        if self.scope_to_execution:
            # Only handle events from the parent execution (not sub-executions)
            if not event_exec_id.startswith(self.parent_execution_id):
                return False
        elif not self.propagate_to_sub:
            # Don't handle any sub-execution events
            if event_exec_id != self.parent_execution_id:
                return False

        # Check event type filtering
        return not self.allowed_event_types or event.type in self.allowed_event_types


# Export commonly used filters
__all__ = [
    "CompositeFilter",
    "EventFilter",
    "EventTypeFilter",
    "ExecutionScopeFilter",
    "NodeScopeFilter",
    "SubDiagramFilter",
]
