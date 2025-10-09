"""Event log implementation for execution state management."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from dipeo.domain.events import DomainEvent


@dataclass
class EventLog:
    """Thread-safe event log for an execution.

    Maintains an ordered log of all events that have occurred during an execution,
    providing thread-safe access to the event history.
    """

    events: list[DomainEvent] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def append(self, event: DomainEvent) -> None:
        """Append an event to the log.

        Args:
            event: Event to append
        """
        async with self._lock:
            self.events.append(event)

    async def get_events(self, after_version: int = 0) -> list[DomainEvent]:
        """Get events after a specific version.

        Args:
            after_version: Version number to start from (exclusive)

        Returns:
            List of events after the specified version
        """
        async with self._lock:
            return self.events[after_version:]

    async def get_all_events(self) -> list[DomainEvent]:
        """Get all events in the log.

        Returns:
            Copy of all events in chronological order
        """
        async with self._lock:
            return self.events.copy()

    @property
    def version(self) -> int:
        """Get current version (number of events)."""
        return len(self.events)
