"""Unified State Manager for execution state management.

This module provides a centralized, event-sourced state management system
that serves as the single source of truth for execution state across all layers.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Optional

from dipeo.application.execution.event_log import EventLog
from dipeo.application.execution.states.state_snapshot import StateSnapshot
from dipeo.diagram_generated import NodeState, Status
from dipeo.diagram_generated.domain_models import ExecutionID, NodeID
from dipeo.domain.events import DomainEvent, EventType


class StateManager:
    """
    Centralized state manager using event sourcing.

    This class:
    - Maintains the authoritative state for all executions
    - Updates state only through events (no direct mutations)
    - Provides consistent read APIs for all consumers
    - Manages state synchronization across layers
    """

    def __init__(self):
        # Event logs per execution
        self._event_logs: dict[ExecutionID, EventLog] = defaultdict(EventLog)

        # Cached state snapshots per execution
        self._state_cache: dict[ExecutionID, StateSnapshot] = {}

        # Lock for state cache updates
        self._cache_lock = asyncio.Lock()

        # Event handlers for state transitions
        self._event_handlers = {
            EventType.EXECUTION_STARTED: self._handle_execution_started,
            EventType.EXECUTION_COMPLETED: self._handle_execution_completed,
            EventType.EXECUTION_ERROR: self._handle_execution_failed,
            EventType.NODE_STARTED: self._handle_node_started,
            EventType.NODE_COMPLETED: self._handle_node_completed,
            EventType.NODE_ERROR: self._handle_node_failed,
        }

    async def apply_event(self, event: DomainEvent) -> None:
        """
        Apply an event to update state.

        This is the ONLY way to modify state - all changes must go through events.
        """
        execution_id = event.payload.get("execution_id")

        # Append to event log
        await self._event_logs[execution_id].append(event)

        # Update cached state snapshot
        async with self._cache_lock:
            await self._update_state_from_event(execution_id, event)

    async def get_state(self, execution_id: ExecutionID) -> StateSnapshot | None:
        """
        Get current state snapshot for an execution.

        Returns None if execution doesn't exist.
        """
        async with self._cache_lock:
            if execution_id not in self._state_cache:
                # Rebuild state from events if not cached
                await self._rebuild_state(execution_id)

            return self._state_cache.get(execution_id)

    async def get_node_state(self, execution_id: ExecutionID, node_id: NodeID) -> NodeState | None:
        """Get state for a specific node."""
        state = await self.get_state(execution_id)
        return state.get_node_state(node_id) if state else None

    async def get_execution_status(self, execution_id: ExecutionID) -> Status | None:
        """Get current status of an execution."""
        state = await self.get_state(execution_id)
        return state.status if state else None

    async def get_ready_nodes(self, execution_id: ExecutionID) -> list[NodeID]:
        """Get nodes that are ready to execute."""
        state = await self.get_state(execution_id)
        if not state:
            return []

        return state.get_nodes_by_status(Status.PENDING)

    async def get_events(
        self, execution_id: ExecutionID, after_version: int = 0
    ) -> list[DomainEvent]:
        """Get events for an execution after a specific version."""
        return await self._event_logs[execution_id].get_events(after_version)

    async def _rebuild_state(self, execution_id: ExecutionID) -> None:
        """Rebuild state from event log (event sourcing)."""
        events = await self._event_logs[execution_id].get_all_events()

        if not events:
            return

        # Start with empty state
        state = StateSnapshot(
            execution_id=execution_id,
            status=Status.PENDING,
            node_states={},
            start_time=datetime.now(),
            end_time=None,
            error=None,
            metadata={},
            version=0,
        )

        # Apply each event to rebuild state
        for event in events:
            state = await self._apply_event_to_state(state, event)

        self._state_cache[execution_id] = state

    async def _update_state_from_event(self, execution_id: ExecutionID, event: DomainEvent) -> None:
        """Update cached state from a new event."""
        if execution_id not in self._state_cache:
            await self._rebuild_state(execution_id)
            return

        current_state = self._state_cache[execution_id]
        new_state = await self._apply_event_to_state(current_state, event)
        self._state_cache[execution_id] = new_state

    async def _apply_event_to_state(
        self, state: StateSnapshot, event: DomainEvent
    ) -> StateSnapshot:
        """Apply a single event to a state snapshot."""
        handler = self._event_handlers.get(event.type)
        if handler:
            return handler(state, event)
        return state

    def _handle_execution_started(self, state: StateSnapshot, event: DomainEvent) -> StateSnapshot:
        """Handle execution started event."""
        return StateSnapshot(
            execution_id=state.execution_id,
            status=Status.RUNNING,
            node_states=state.node_states.copy(),
            start_time=datetime.now(),  # Use current time since DomainEvent doesn't have timestamp
            end_time=None,
            error=None,
            metadata={**state.metadata, **event.payload},
            version=state.version + 1,
        )

    def _handle_execution_completed(
        self, state: StateSnapshot, event: DomainEvent
    ) -> StateSnapshot:
        """Handle execution completed event."""
        return StateSnapshot(
            execution_id=state.execution_id,
            status=Status.COMPLETED,
            node_states=state.node_states.copy(),
            start_time=state.start_time,
            end_time=datetime.now(),
            error=None,
            metadata={**state.metadata, **event.payload},
            version=state.version + 1,
        )

    def _handle_execution_failed(self, state: StateSnapshot, event: DomainEvent) -> StateSnapshot:
        """Handle execution failed event."""
        return StateSnapshot(
            execution_id=state.execution_id,
            status=Status.FAILED,
            node_states=state.node_states.copy(),
            start_time=state.start_time,
            end_time=datetime.now(),
            error=event.payload.get("error", "Unknown error"),
            metadata={**state.metadata, **event.payload},
            version=state.version + 1,
        )

    def _handle_node_started(self, state: StateSnapshot, event: DomainEvent) -> StateSnapshot:
        """Handle node started event."""
        node_id = event.payload.get("node_id")
        if not node_id:
            return state

        new_node_states = state.node_states.copy()
        new_node_states[node_id] = NodeState(
            node_id=node_id,
            status=Status.RUNNING,
            start_time=datetime.now(),
            end_time=None,
            execution_count=event.payload.get("execution_count", 1),
            error=None,
            metadata=event.payload,
        )

        return StateSnapshot(
            execution_id=state.execution_id,
            status=state.status,
            node_states=new_node_states,
            start_time=state.start_time,
            end_time=state.end_time,
            error=state.error,
            metadata=state.metadata,
            version=state.version + 1,
        )

    def _handle_node_completed(self, state: StateSnapshot, event: DomainEvent) -> StateSnapshot:
        """Handle node completed event."""
        node_id = event.payload.get("node_id")
        if not node_id or node_id not in state.node_states:
            return state

        new_node_states = state.node_states.copy()
        current_node_state = new_node_states[node_id]

        new_node_states[node_id] = NodeState(
            node_id=node_id,
            status=Status.COMPLETED,
            start_time=current_node_state.start_time,
            end_time=datetime.now(),
            execution_count=event.payload.get("execution_count", 1),
            error=None,
            metadata={**current_node_state.metadata, **event.payload},
        )

        return StateSnapshot(
            execution_id=state.execution_id,
            status=state.status,
            node_states=new_node_states,
            start_time=state.start_time,
            end_time=state.end_time,
            error=state.error,
            metadata=state.metadata,
            version=state.version + 1,
        )

    def _handle_node_failed(self, state: StateSnapshot, event: DomainEvent) -> StateSnapshot:
        """Handle node failed event."""
        node_id = event.payload.get("node_id")
        if not node_id or node_id not in state.node_states:
            return state

        new_node_states = state.node_states.copy()
        current_node_state = new_node_states[node_id]

        new_node_states[node_id] = NodeState(
            node_id=node_id,
            status=Status.FAILED,
            start_time=current_node_state.start_time,
            end_time=datetime.now(),
            execution_count=event.payload.get("execution_count", 1),
            error=event.payload.get("error", "Unknown error"),
            metadata={**current_node_state.metadata, **event.payload},
        )

        return StateSnapshot(
            execution_id=state.execution_id,
            status=state.status,
            node_states=new_node_states,
            start_time=state.start_time,
            end_time=state.end_time,
            error=state.error,
            metadata=state.metadata,
            version=state.version + 1,
        )

    async def clear_execution(self, execution_id: ExecutionID) -> None:
        """Clear all state for an execution (for cleanup)."""
        async with self._cache_lock:
            self._state_cache.pop(execution_id, None)
            self._event_logs.pop(execution_id, None)
