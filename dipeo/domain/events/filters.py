"""Common event filter implementations for domain event filtering."""

from dataclasses import dataclass

from .contracts import DomainEvent
from .types import EventType
from .unified_ports import EventFilter


@dataclass
class ExecutionScopeFilter:
    """Filter events by execution scope for sub-diagram isolation."""

    execution_id: str
    include_children: bool = True

    def matches(self, event: DomainEvent) -> bool:
        if not event.scope.execution_id:
            return False

        event_exec_id = str(event.scope.execution_id)

        if self.include_children:
            return event_exec_id.startswith(self.execution_id)
        else:
            return event_exec_id == self.execution_id


@dataclass
class NodeScopeFilter:
    """Filter events by node scope."""

    node_ids: set[str]

    def matches(self, event: DomainEvent) -> bool:
        if not event.scope.node_id:
            return True
        return event.scope.node_id in self.node_ids


@dataclass
class EventTypeFilter:
    """Filter events by type."""

    allowed_types: set[EventType]

    def matches(self, event: DomainEvent) -> bool:
        return event.type in self.allowed_types


@dataclass
class CompositeFilter:
    """Combine multiple filters with AND/OR logic."""

    filters: list[EventFilter]
    require_all: bool = True

    def matches(self, event: DomainEvent) -> bool:
        if not self.filters:
            return True

        if self.require_all:
            return all(f.matches(event) for f in self.filters)
        else:
            return any(f.matches(event) for f in self.filters)


@dataclass
class SubDiagramFilter:
    """Filter for sub-diagram execution events."""

    parent_execution_id: str
    propagate_to_sub: bool = True
    scope_to_execution: bool = False
    allowed_event_types: set[EventType] | None = None

    def matches(self, event: DomainEvent) -> bool:
        if not event.scope.execution_id:
            return False

        event_exec_id = str(event.scope.execution_id)

        if self.scope_to_execution:
            if not event_exec_id.startswith(self.parent_execution_id):
                return False
        elif not self.propagate_to_sub:
            if event_exec_id != self.parent_execution_id:
                return False

        return not self.allowed_event_types or event.type in self.allowed_event_types


__all__ = [
    "CompositeFilter",
    "EventFilter",
    "EventTypeFilter",
    "ExecutionScopeFilter",
    "NodeScopeFilter",
    "SubDiagramFilter",
]
