"""Cache-first state store with Phase 4 optimizations."""

import asyncio
import contextlib
import logging
import os
import time
from datetime import datetime
from typing import Any

from dipeo.config import STATE_DB_PATH
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    LLMUsage,
    NodeState,
    Status,
)
from dipeo.domain.events import DomainEvent, EventType
from dipeo.domain.execution.envelope import serialize_protocol
from dipeo.domain.execution.state.ports import (
    ExecutionCachePort,
    ExecutionStateService,
)
from dipeo.domain.execution.state.ports import (
    ExecutionStateRepository as StateStorePort,
)

from .cache_manager import CacheManager
from .models import CacheEntry, PersistenceCheckpoint
from .persistence_manager import PersistenceManager

logger = get_module_logger(__name__)


class CacheFirstStateStore(StateStorePort, ExecutionStateService, ExecutionCachePort):
    """Cache-first state store with Phase 4 optimizations.

    This implementation prioritizes cache operations over database writes:
    - All reads go through cache first
    - Writes update cache immediately, database eventually
    - Database persistence only at checkpoints and completion
    - Cache warming for frequently accessed executions
    - Intelligent cache invalidation based on access patterns
    """

    def __init__(
        self,
        db_path: str | None = None,
        message_store: Any | None = None,
        cache_size: int = 1000,
        checkpoint_interval: int = 10,  # Checkpoint every N nodes
        warm_cache_size: int = 20,  # Number of frequently accessed executions to keep warm
        persistence_delay: float = 5.0,  # Delay before persisting to database
        write_through_critical: bool = False,  # Write-through for critical events
    ):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", str(STATE_DB_PATH))
        self.message_store = message_store

        # Managers
        self._cache_manager = CacheManager(
            cache_size=cache_size,
            warm_cache_size=warm_cache_size,
        )
        self._persistence_manager = PersistenceManager(self.db_path)

        # Checkpoint configuration
        self._checkpoint_interval = checkpoint_interval
        self._checkpoint_queue: asyncio.Queue = asyncio.Queue()
        self._persistence_delay = persistence_delay
        self._write_through_critical = write_through_critical

        # Background tasks
        self._persistence_task: asyncio.Task | None = None
        self._cache_manager_task: asyncio.Task | None = None
        self._warmup_task: asyncio.Task | None = None

        # State
        self._initialized = False
        self._running = False

    async def initialize(self):
        """Initialize the cache-first state store."""
        if self._initialized:
            return

        # Initialize database connection
        await self._persistence_manager.connect()
        await self._persistence_manager.init_schema()

        # Warm up cache with frequently accessed executions
        states = await self._persistence_manager.load_warm_cache_states(
            self._cache_manager._warm_cache_size
        )
        await self._cache_manager.warm_cache_with_states(states)

        # Start background tasks
        self._running = True
        self._persistence_task = asyncio.create_task(self._persistence_loop())

        cache_tasks = await self._cache_manager.start_background_tasks()
        self._cache_manager_task, self._warmup_task = cache_tasks

        self._initialized = True

    async def cleanup(self):
        """Cleanup resources."""
        self._running = False

        # Persist all dirty cache entries
        await self._persist_all_dirty()

        # Stop cache manager background tasks
        await self._cache_manager.stop_background_tasks()

        # Stop persistence task
        if self._persistence_task:
            self._persistence_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._persistence_task

        # Stop cache manager tasks
        for task in [self._cache_manager_task, self._warmup_task]:
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        # Close database connection
        await self._persistence_manager.disconnect()

        self._initialized = False

        # Log final metrics
        self._log_metrics()

    async def handle(self, event: DomainEvent) -> None:
        """Handle method for EventBus compatibility."""
        await self.handle_event(event)

    async def handle_event(self, event: DomainEvent) -> None:
        """Handle domain events for state persistence with idempotency."""
        execution_id = event.scope.execution_id
        event_type = event.type

        # Filter out events from sub-diagrams or executions we're not tracking
        # EXCEPT for EXECUTION_COMPLETED which should always be processed to finalize state
        if not await self._cache_manager.has_execution(execution_id):
            # Allow EXECUTION_COMPLETED through even if not in cache - it finalizes the execution
            if event_type != EventType.EXECUTION_COMPLETED:
                # Skip other events for unknown executions (likely sub-diagrams)
                return

            # For EXECUTION_COMPLETED on unknown execution, try to load from database
            state = await self._persistence_manager.load_state(execution_id)
            if state:
                # Add to cache so completion can be processed
                entry = CacheEntry(
                    state=state,
                    is_dirty=True,
                    is_persisted=True,
                )
                await self._cache_manager.put_entry(execution_id, entry)
            else:
                # No state in DB either - skip this event
                logger.warning(
                    f"EXECUTION_COMPLETED event for unknown execution {execution_id} - no state in cache or DB"
                )
                return

        # Get sequence number from metadata if available (set by event_pipeline)
        seq = event.meta.get("seq") if event.meta else None
        if seq is not None:
            # Record transition for idempotency
            node_id = getattr(event.scope, "node_id", None)
            payload = {
                "event_type": event_type.value,
                "data": getattr(event, "data", {}),
            }
            is_new = await self._persistence_manager.record_transition(
                execution_id, node_id, event_type.value, seq, payload
            )
            if not is_new:
                # Event already processed - skip
                logger.debug(f"Skipping duplicate event {event_type} seq {seq} for {execution_id}")
                return

        # Check if this is a critical event requiring immediate persistence
        is_critical = self._write_through_critical and event_type in [
            EventType.NODE_COMPLETED,
            EventType.EXECUTION_COMPLETED,
        ]

        # For EXECUTION_COMPLETED, update status and persist immediately
        if event_type == EventType.EXECUTION_COMPLETED:
            # Extract status from event payload (defaults to COMPLETED)
            status = Status.COMPLETED
            if hasattr(event, "payload") and hasattr(event.payload, "status"):
                status = event.payload.status

            # Update execution status IN CACHE ONLY (don't queue checkpoint yet)
            state = await self.get_state(execution_id)
            if state:
                state.status = status
                state.ended_at = datetime.now().isoformat()
                await self.save_state(state)

            # Handle critical persistence or normal checkpoint
            # This is the ONLY place we should persist for EXECUTION_COMPLETED
            if self._write_through_critical:
                await self._persist_critical_event(execution_id)
            else:
                # Create final checkpoint
                entry = await self._cache_manager.get_entry(execution_id)
                checkpoint = PersistenceCheckpoint(
                    execution_id=execution_id,
                    checkpoint_time=time.time(),
                    node_count=len(entry.state.executed_nodes) if entry else 0,
                    is_final=True,
                )
                await self._checkpoint_queue.put(checkpoint)
            return

        # For other events, update cache and let checkpoint system handle persistence
        if event_type == EventType.EXECUTION_STARTED:
            await self.update_status(execution_id, Status.RUNNING)
        elif event_type == EventType.NODE_STARTED:
            await self.update_node_status(execution_id, event.scope.node_id, Status.RUNNING)
        elif event_type == EventType.NODE_COMPLETED:
            await self.update_node_status(execution_id, event.scope.node_id, Status.COMPLETED)
            # Handle output if present in event data
            if hasattr(event, "data") and event.data and "output" in event.data:
                await self.update_node_output(
                    execution_id,
                    event.scope.node_id,
                    event.data["output"],
                    is_exception=False,
                    llm_usage=event.data.get("llm_usage"),
                )
            # Write-through for critical events
            if is_critical:
                await self._persist_critical_event(execution_id)
        elif event_type == EventType.NODE_ERROR:
            error_msg = None
            if hasattr(event, "data") and event.data:
                error_msg = event.data.get("error", str(event.data))
            await self.update_node_status(
                execution_id, event.scope.node_id, Status.FAILED, error=error_msg
            )
        elif event_type == EventType.EXECUTION_FAILED:
            error_msg = None
            if hasattr(event, "data") and event.data:
                error_msg = event.data.get("error", str(event.data))
            await self.update_status(execution_id, Status.FAILED, error=error_msg)

    async def _persistence_loop(self):
        """Background task to handle checkpoints and delayed persistence."""
        while self._running:
            try:
                # Process checkpoint queue
                try:
                    checkpoint = await asyncio.wait_for(
                        self._checkpoint_queue.get(), timeout=self._persistence_delay
                    )
                    await self._handle_checkpoint(checkpoint)
                except TimeoutError:
                    # Persist any dirty entries that have been waiting
                    await self._persist_old_dirty_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in persistence loop: {e}", exc_info=True)

    async def _handle_checkpoint(self, checkpoint: PersistenceCheckpoint):
        """Handle a persistence checkpoint."""
        entry = await self._cache_manager.get_entry(checkpoint.execution_id)
        if entry and (entry.is_dirty or checkpoint.is_final):
            await self._persistence_manager.persist_entry(checkpoint.execution_id, entry)
            entry.checkpoint_count += 1
            self._persistence_manager.metrics.checkpoints += 1

    async def _persist_old_dirty_entries(self):
        """Persist dirty entries that have been waiting."""
        dirty_entries = await self._cache_manager.get_dirty_entries(
            age_threshold=self._persistence_delay
        )
        for exec_id, entry in dirty_entries:
            await self._persistence_manager.persist_entry(exec_id, entry)

    async def _persist_critical_event(self, execution_id: str):
        """Immediately persist critical events with enhanced durability."""
        entry = await self._cache_manager.get_entry(execution_id)
        if not entry:
            return

        # Use enhanced durability settings for critical writes
        await self._persistence_manager.persist_entry(execution_id, entry, use_full_sync=True)
        entry.is_dirty = False
        entry.is_persisted = True
        self._persistence_manager.metrics.checkpoints += 1
        # logger.debug(f"Critical event persisted immediately for execution {execution_id}")

    async def _persist_all_dirty(self):
        """Persist all dirty cache entries."""
        dirty_entries = await self._cache_manager.get_all_dirty_entries()
        for exec_id, entry in dirty_entries:
            await self._persistence_manager.persist_entry(exec_id, entry)

    def _log_metrics(self):
        """Log current metrics."""
        cache_metrics = self._cache_manager.metrics
        persist_metrics = self._persistence_manager.metrics

        logger.info(
            f"CacheFirst Metrics - "
            f"Cache hits: {cache_metrics.cache_hits}, "
            f"Cache misses: {cache_metrics.cache_misses}, "
            f"Hit rate: {cache_metrics.cache_hit_rate:.1f}%, "
            f"Warm cache hits: {cache_metrics.warm_cache_hits}, "
            f"DB reads: {persist_metrics.db_reads}, "
            f"DB writes: {persist_metrics.db_writes}, "
            f"Checkpoints: {persist_metrics.checkpoints}, "
            f"Evictions: {cache_metrics.cache_evictions}, "
            f"Cache size: {len(self._cache_manager.cache)}/{self._cache_manager._cache_size}"
        )

    async def create_execution(
        self,
        execution_id: str | ExecutionID,
        diagram_id: str | DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        """Create a new execution (cache-only until checkpoint)."""
        exec_id = execution_id if isinstance(execution_id, str) else str(execution_id)
        diag_id = None
        if diagram_id:
            diag_id = DiagramID(diagram_id) if isinstance(diagram_id, str) else diagram_id

        now = datetime.now().isoformat()
        state = ExecutionState(
            id=ExecutionID(exec_id),
            status=Status.PENDING,
            diagram_id=diag_id,
            started_at=now,
            ended_at=None,
            node_states={},
            node_outputs={},
            llm_usage=LLMUsage(input=0, output=0, cached=None, total=0),
            error=None,
            variables=variables or {},
            is_active=True,
            exec_counts={},
            executed_nodes=[],
        )

        # Create cache entry (not persisted yet)
        entry = CacheEntry(
            state=state,
            variables=variables or {},
            is_dirty=True,
            is_persisted=False,
        )

        await self._cache_manager.put_entry(exec_id, entry)

        return state

    async def save_state(self, state: ExecutionState):
        """Save state to cache (deferred database write)."""
        from dipeo.infrastructure.timing import atime_phase

        exec_id = state.id

        async with atime_phase(str(exec_id), "system", "cache_write"):
            entry = await self._cache_manager.get_entry(exec_id)
            if entry:
                entry.state = state
                entry.mark_dirty()
            else:
                entry = CacheEntry(
                    state=state,
                    is_dirty=True,
                    is_persisted=False,
                )
                await self._cache_manager.put_entry(exec_id, entry)

        # Check if we need a checkpoint
        node_count = len(state.executed_nodes)
        if node_count > 0 and node_count % self._checkpoint_interval == 0:
            checkpoint = PersistenceCheckpoint(
                execution_id=exec_id,
                checkpoint_time=time.time(),
                node_count=node_count,
                is_final=False,
            )
            await self._checkpoint_queue.put(checkpoint)

    async def get_state(self, execution_id: str) -> ExecutionState | None:
        """Get state from cache first, then database if needed."""
        # Check cache first
        entry = await self._cache_manager.get_entry(execution_id)
        if entry:
            return entry.state

        # Load from database
        state = await self._persistence_manager.load_state(execution_id)
        if not state:
            return None

        # Add to cache
        entry = CacheEntry(
            state=state,
            is_persisted=True,
        )

        # Populate node data
        for node_id, node_state in state.node_states.items():
            entry.node_statuses[node_id] = node_state.status
            if node_state.error:
                entry.node_errors[node_id] = node_state.error

        entry.node_outputs = state.node_outputs.copy()
        entry.variables = state.variables.copy()
        entry.llm_usage = state.llm_usage

        await self._cache_manager.put_entry(execution_id, entry)

        # Update database access count
        await self._persistence_manager.update_access_tracking(execution_id)

        return state

    async def update_status(self, execution_id: str, status: Status, error: str | None = None):
        """Update execution status in cache."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.status = status
        state.error = error
        if status in [Status.COMPLETED, Status.FAILED, Status.ABORTED]:
            state.ended_at = datetime.now().isoformat()

            # Final checkpoint
            checkpoint = PersistenceCheckpoint(
                execution_id=execution_id,
                checkpoint_time=time.time(),
                node_count=len(state.executed_nodes),
                is_final=True,
            )
            await self._checkpoint_queue.put(checkpoint)

        await self.save_state(state)

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        llm_usage: LLMUsage | dict | None = None,
    ) -> None:
        """Update node output in cache."""
        entry = await self._cache_manager.get_entry(execution_id)
        if not entry:
            # Load state if not in cache
            state = await self.get_state(execution_id)
            if not state:
                raise ValueError(f"Execution {execution_id} not found")
            entry = await self._cache_manager.get_entry(execution_id)

        # Serialize output
        if hasattr(output, "__class__") and hasattr(output, "to_dict"):
            serialized_output = serialize_protocol(output)
        elif isinstance(output, dict) and (
            output.get("envelope_format") or output.get("_envelope_format")
        ):
            serialized_output = output
        else:
            from dipeo.domain.execution.envelope import EnvelopeFactory

            if is_exception:
                wrapped_output = EnvelopeFactory.create(
                    body={
                        "error": str(output),
                        "type": type(output).__name__
                        if hasattr(output, "__class__")
                        else "Exception",
                    },
                    produced_by=str(node_id),
                )
            else:
                wrapped_output = EnvelopeFactory.create(body=str(output), produced_by=str(node_id))
            serialized_output = serialize_protocol(wrapped_output)

        # Update cache
        async with self._cache_manager.cache_lock:
            entry.node_outputs[node_id] = serialized_output
            entry.state.node_outputs[node_id] = serialized_output
            entry.mark_dirty()

        if llm_usage:
            await self.add_llm_usage(execution_id, llm_usage)

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: Status,
        error: str | None = None,
    ):
        """Update node status in cache."""
        entry = await self._cache_manager.get_entry(execution_id)
        if not entry:
            state = await self.get_state(execution_id)
            if not state:
                raise ValueError(f"Execution {execution_id} not found")
            entry = await self._cache_manager.get_entry(execution_id)

        async with self._cache_manager.cache_lock:
            now = datetime.now().isoformat()

            # Add node to executed_nodes list if not already there
            # This ensures nodes appear in execution order even if events arrive out of order
            if node_id not in entry.state.executed_nodes:
                entry.state.executed_nodes.append(node_id)

            if node_id not in entry.state.node_states:
                entry.state.node_states[node_id] = NodeState(
                    status=status,
                    started_at=now if status == Status.RUNNING else None,
                    ended_at=None,
                    error=None,
                    llm_usage=None,
                )
            else:
                entry.state.node_states[node_id].status = status
                if status == Status.RUNNING:
                    entry.state.node_states[node_id].started_at = now
                elif status in [Status.COMPLETED, Status.FAILED, Status.SKIPPED]:
                    entry.state.node_states[node_id].ended_at = now

            if error:
                entry.state.node_states[node_id].error = error
                entry.node_errors[node_id] = error

        entry.node_statuses[node_id] = status
        entry.mark_dirty()

    async def get_node_output(self, execution_id: str, node_id: str) -> dict[str, Any] | None:
        """Get node output from cache."""
        entry = await self._cache_manager.get_entry(execution_id)
        if entry:
            return entry.node_outputs.get(node_id)

        state = await self.get_state(execution_id)
        if not state:
            return None
        return state.node_outputs.get(node_id)

    async def update_variables(self, execution_id: str, variables: dict[str, Any]):
        """Update execution variables in cache."""
        entry = await self._cache_manager.get_entry(execution_id)
        if not entry:
            state = await self.get_state(execution_id)
            if not state:
                raise ValueError(f"Execution {execution_id} not found")
            entry = await self._cache_manager.get_entry(execution_id)

        async with self._cache_manager.cache_lock:
            entry.state.variables.update(variables)
            entry.variables.update(variables)
            entry.mark_dirty()

    async def update_metrics(self, execution_id: str, metrics: dict[str, Any]):
        """Update execution metrics in cache."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.metrics = metrics
        await self.save_state(state)

    async def add_llm_usage(self, execution_id: str, usage: LLMUsage | dict):
        """Add LLM usage in cache."""
        if isinstance(usage, dict):
            usage = LLMUsage(
                input=usage.get("input", 0),
                output=usage.get("output", 0),
                cached=usage.get("cached"),
                total=usage.get("total", 0),
            )

        entry = await self._cache_manager.get_entry(execution_id)
        if not entry:
            state = await self.get_state(execution_id)
            if not state:
                raise ValueError(f"Execution {execution_id} not found")
            entry = await self._cache_manager.get_entry(execution_id)

        async with self._cache_manager.cache_lock:
            if entry.state.llm_usage:
                entry.state.llm_usage.input += usage.input
                entry.state.llm_usage.output += usage.output
                if usage.cached:
                    entry.state.llm_usage.cached = (
                        entry.state.llm_usage.cached or 0
                    ) + usage.cached
                entry.state.llm_usage.total = (
                    entry.state.llm_usage.input + entry.state.llm_usage.output
                )
            else:
                entry.state.llm_usage = usage

        entry.llm_usage = entry.state.llm_usage
        entry.mark_dirty()

    async def persist_final_state(self, state: ExecutionState):
        """Persist final state immediately."""
        state.is_active = False

        entry = await self._cache_manager.get_entry(state.id)
        if entry:
            entry.state = state
            await self._persistence_manager.persist_entry(state.id, entry)

            # Remove from cache after delay
            async def delayed_removal():
                await asyncio.sleep(10)
                await self._cache_manager.remove_entry(state.id)

            asyncio.create_task(delayed_removal())
        else:
            # Direct persist if not in cache
            entry = CacheEntry(state=state, is_dirty=True)
            await self._persistence_manager.persist_entry(state.id, entry)

    async def list_executions(
        self,
        diagram_id: DiagramID | None = None,
        status: Status | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        """List executions from database."""
        return await self._persistence_manager.list_executions(
            diagram_id=diagram_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def cleanup_old_states(self, days: int = 7):
        """Cleanup old execution states."""
        await self._persistence_manager.cleanup_old_states(days)

    async def get_execution(self, execution_id: str) -> ExecutionState | None:
        """Get execution state - alias for get_state."""
        return await self.get_state(execution_id)

    async def save_execution(self, state: ExecutionState) -> None:
        """Save execution state - alias for save_state."""
        await self.save_state(state)

    async def cleanup_old_executions(self, days: int = 7) -> None:
        """Clean up old execution states - alias for cleanup_old_states."""
        await self.cleanup_old_states(days)

    def get_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        cache_metrics = self._cache_manager.metrics.to_dict()
        persist_metrics = self._persistence_manager.metrics.to_dict()

        # Combine metrics from both managers
        combined = {**cache_metrics}
        combined["db_reads"] = persist_metrics["db_reads"]
        combined["db_writes"] = persist_metrics["db_writes"]
        combined["checkpoints"] = persist_metrics["checkpoints"]

        return combined

    # ExecutionStateService protocol implementation
    async def start_execution(
        self,
        execution_id: ExecutionID,
        diagram_id: DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        """Start a new execution."""
        await self.create_execution(execution_id, diagram_id, variables)
        await self.update_status(str(execution_id), Status.RUNNING)
        state = await self.get_state(str(execution_id))
        return state

    async def finish_execution(
        self,
        execution_id: str,
        status: Status,
        error: str | None = None,
    ) -> None:
        """Finish an execution with final status."""
        await self.update_status(execution_id, status, error)

    async def update_node_execution(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        status: Status,
        is_exception: bool = False,
        llm_usage: LLMUsage | None = None,
        error: str | None = None,
    ) -> None:
        """Atomically update node execution state."""
        await self.update_node_output(execution_id, node_id, output, is_exception, llm_usage)
        await self.update_node_status(execution_id, node_id, status, error)

    async def append_llm_usage(self, execution_id: str, usage: LLMUsage) -> None:
        """Append to cumulative LLM usage."""
        await self.add_llm_usage(execution_id, usage)

    async def append_token_usage(self, execution_id: str, tokens: LLMUsage) -> None:
        """Append to cumulative token usage (alias for append_llm_usage)."""
        await self.add_llm_usage(execution_id, tokens)

    async def get_execution_state(self, execution_id: str) -> ExecutionState | None:
        """Get current execution state."""
        return await self.get_state(execution_id)

    # ExecutionCachePort protocol implementation
    async def get_state_from_cache(self, execution_id: str) -> ExecutionState | None:
        """Get state from cache only (no DB lookup)."""
        entry = await self._cache_manager.get_entry(execution_id)
        return entry.state if entry else None

    async def create_execution_in_cache(
        self,
        execution_id: ExecutionID,
        diagram_id: DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        """Create execution in cache only."""
        return await self.create_execution(execution_id, diagram_id, variables)
