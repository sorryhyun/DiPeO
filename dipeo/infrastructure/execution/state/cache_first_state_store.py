"""Cache-first state store with Phase 4 optimizations."""

import asyncio
import contextlib
import json
import logging
import os
import sqlite3
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from dipeo.config import STATE_DB_PATH
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
from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata for cache-first architecture."""

    state: ExecutionState
    node_outputs: dict[str, Any] = field(default_factory=dict)
    node_statuses: dict[str, Status] = field(default_factory=dict)
    node_errors: dict[str, str] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    llm_usage: LLMUsage | None = None

    # Metadata
    last_access_time: float = field(default_factory=time.time)
    last_write_time: float = field(default_factory=time.time)
    access_count: int = 0
    is_dirty: bool = False
    is_persisted: bool = False
    checkpoint_count: int = 0

    def touch(self):
        """Update access time and count."""
        self.last_access_time = time.time()
        self.access_count += 1

    def mark_dirty(self):
        """Mark cache entry as having unpersisted changes."""
        self.is_dirty = True
        self.last_write_time = time.time()


@dataclass
class PersistenceCheckpoint:
    """Checkpoint for periodic persistence."""

    execution_id: str
    checkpoint_time: float
    node_count: int
    is_final: bool = False


class CacheFirstStateStore(StateStorePort):
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
    ):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", str(STATE_DB_PATH))
        self.message_store = message_store

        # Cache configuration
        self._cache: dict[str, CacheEntry] = {}
        self._cache_size = cache_size
        self._cache_lock = asyncio.Lock()

        # Frequently accessed executions (for cache warming)
        self._access_frequency: defaultdict[str, int] = defaultdict(int)
        self._warm_cache_size = warm_cache_size
        self._warm_cache_ids: set[str] = set()

        # Checkpoint configuration
        self._checkpoint_interval = checkpoint_interval
        self._checkpoint_queue: asyncio.Queue = asyncio.Queue()
        self._persistence_delay = persistence_delay

        # Database connection
        self._conn: sqlite3.Connection | None = None
        self._executor = ThreadPoolExecutor(max_workers=2)

        # Background tasks
        self._persistence_task: asyncio.Task | None = None
        self._cache_manager_task: asyncio.Task | None = None
        self._warmup_task: asyncio.Task | None = None

        # Metrics
        self._metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_reads": 0,
            "db_writes": 0,
            "checkpoints": 0,
            "cache_evictions": 0,
            "warm_cache_hits": 0,
        }

        # State
        self._initialized = False
        self._running = False

    async def initialize(self):
        """Initialize the cache-first state store."""
        if self._initialized:
            return

        # Initialize database connection
        await self._connect()
        await self._init_schema()

        # Warm up cache with frequently accessed executions
        await self._warm_cache()

        # Start background tasks
        self._running = True
        self._persistence_task = asyncio.create_task(self._persistence_loop())
        self._cache_manager_task = asyncio.create_task(self._cache_management_loop())
        self._warmup_task = asyncio.create_task(self._cache_warmup_loop())

        self._initialized = True
        logger.info(
            f"CacheFirstStateStore initialized with cache size {self._cache_size}, "
            f"checkpoint interval {self._checkpoint_interval} nodes"
        )

    async def cleanup(self):
        """Cleanup resources."""
        self._running = False

        # Persist all dirty cache entries
        await self._persist_all_dirty()

        # Stop background tasks
        for task in [self._persistence_task, self._cache_manager_task, self._warmup_task]:
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        # Close database connection
        if self._conn:
            self._conn.close()

        self._executor.shutdown(wait=False)
        self._initialized = False

        # Log final metrics
        self._log_metrics()

    async def handle_event(self, event: DomainEvent) -> None:
        """Handle domain events for state persistence."""
        execution_id = event.scope.execution_id
        event_type = event.type

        # For EXECUTION_COMPLETED, persist immediately
        if event_type == EventType.EXECUTION_COMPLETED:
            checkpoint = PersistenceCheckpoint(
                execution_id=execution_id,
                checkpoint_time=time.time(),
                node_count=len(
                    self._cache.get(execution_id, CacheEntry(state=None)).state.executed_nodes
                )
                if execution_id in self._cache
                else 0,
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

    async def _connect(self):
        """Connect to the database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()

        def _connect_sync():
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,
                timeout=30.0,
            )
            # Performance optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")
            return conn

        self._conn = await loop.run_in_executor(self._executor, _connect_sync)

    async def _init_schema(self):
        """Initialize database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS execution_states (
            execution_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            diagram_id TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            node_states TEXT NOT NULL,
            node_outputs TEXT NOT NULL,
            llm_usage TEXT NOT NULL,
            error TEXT,
            variables TEXT NOT NULL,
            exec_counts TEXT NOT NULL DEFAULT '{}',
            executed_nodes TEXT NOT NULL DEFAULT '[]',
            metrics TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_status ON execution_states(status);
        CREATE INDEX IF NOT EXISTS idx_started_at ON execution_states(started_at);
        CREATE INDEX IF NOT EXISTS idx_diagram_id ON execution_states(diagram_id);
        CREATE INDEX IF NOT EXISTS idx_access_count ON execution_states(access_count DESC);
        CREATE INDEX IF NOT EXISTS idx_last_accessed ON execution_states(last_accessed DESC);
        """

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._conn.executescript, schema)

    async def _warm_cache(self):
        """Warm cache with frequently accessed executions."""
        # Query for most frequently accessed executions
        cursor = await self._execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, llm_usage, error, variables,
                   exec_counts, executed_nodes, metrics, access_count
            FROM execution_states
            WHERE status IN (?, ?)
            ORDER BY access_count DESC, last_accessed DESC
            LIMIT ?
            """,
            (Status.RUNNING.value, Status.PENDING.value, self._warm_cache_size),
        )

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(self._executor, cursor.fetchall)

        for row in rows:
            state = self._parse_state_from_row(row)
            exec_id = state.id

            # Create cache entry
            entry = CacheEntry(
                state=state, is_persisted=True, access_count=row[13] if len(row) > 13 else 0
            )

            # Populate node data
            for node_id, node_state in state.node_states.items():
                entry.node_statuses[node_id] = node_state.status
                if node_state.error:
                    entry.node_errors[node_id] = node_state.error

            entry.node_outputs = state.node_outputs.copy()
            entry.variables = state.variables.copy()
            entry.llm_usage = state.llm_usage

            async with self._cache_lock:
                self._cache[exec_id] = entry
                self._warm_cache_ids.add(exec_id)

        if rows:
            logger.info(f"Warmed cache with {len(rows)} frequently accessed executions")

    async def _execute(self, query: str, params: tuple = ()):
        """Execute a database query."""
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(self._executor, self._conn.execute, query, params)
        self._metrics["db_reads"] += 1 if query.strip().upper().startswith("SELECT") else 0
        self._metrics["db_writes"] += 1 if not query.strip().upper().startswith("SELECT") else 0
        return cursor

    def _parse_state_from_row(self, row) -> ExecutionState:
        """Parse ExecutionState from database row."""
        raw_outputs = json.loads(row[6]) if row[6] else {}
        node_outputs = {}
        for node_id, output_data in raw_outputs.items():
            if isinstance(output_data, dict):
                node_outputs[node_id] = output_data
            else:
                node_outputs[node_id] = {
                    "envelope_format": True,
                    "id": str(uuid4()),
                    "trace_id": "",
                    "produced_by": node_id,
                    "content_type": "raw_text",
                    "schema_id": None,
                    "serialization_format": None,
                    "body": output_data,
                    "meta": {"timestamp": time.time()},
                    "representations": None,
                }

        state_data = {
            "id": row[0],
            "status": row[1],
            "diagram_id": row[2],
            "started_at": row[3],
            "ended_at": row[4],
            "node_states": json.loads(row[5]) if row[5] else {},
            "node_outputs": node_outputs,
            "llm_usage": json.loads(row[7])
            if row[7]
            else {"input": 0, "output": 0, "cached": None, "total": 0},
            "error": row[8],
            "variables": json.loads(row[9]) if row[9] else {},
            "exec_counts": json.loads(row[10]) if len(row) > 10 and row[10] else {},
            "executed_nodes": json.loads(row[11]) if len(row) > 11 and row[11] else [],
            "metrics": json.loads(row[12]) if len(row) > 12 and row[12] else None,
            "is_active": row[1] in [Status.RUNNING.value, Status.PENDING.value],
        }

        return ExecutionState(**state_data)

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

    async def _cache_management_loop(self):
        """Background task to manage cache size and eviction."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._evict_if_needed()
                self._log_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache management loop: {e}", exc_info=True)

    async def _cache_warmup_loop(self):
        """Background task to update warm cache based on access patterns."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                await self._update_warm_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache warmup loop: {e}", exc_info=True)

    async def _handle_checkpoint(self, checkpoint: PersistenceCheckpoint):
        """Handle a persistence checkpoint."""
        async with self._cache_lock:
            if checkpoint.execution_id in self._cache:
                entry = self._cache[checkpoint.execution_id]
                if entry.is_dirty or checkpoint.is_final:
                    await self._persist_entry(checkpoint.execution_id, entry)
                    entry.checkpoint_count += 1
                    self._metrics["checkpoints"] += 1

    async def _persist_entry(self, execution_id: str, entry: CacheEntry):
        """Persist a cache entry to database."""
        state_dict = entry.state.model_dump()

        await self._execute(
            """
            INSERT INTO execution_states
            (execution_id, status, diagram_id, started_at, ended_at,
             node_states, node_outputs, llm_usage, error, variables,
             exec_counts, executed_nodes, metrics, access_count, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(execution_id) DO UPDATE SET
                status=excluded.status,
                ended_at=excluded.ended_at,
                node_states=excluded.node_states,
                node_outputs=excluded.node_outputs,
                llm_usage=excluded.llm_usage,
                error=excluded.error,
                variables=excluded.variables,
                exec_counts=excluded.exec_counts,
                executed_nodes=excluded.executed_nodes,
                metrics=excluded.metrics,
                access_count=excluded.access_count,
                last_accessed=excluded.last_accessed
            """,
            (
                entry.state.id,
                entry.state.status.value,
                entry.state.diagram_id,
                entry.state.started_at,
                entry.state.ended_at,
                json.dumps(state_dict["node_states"]),
                json.dumps(state_dict["node_outputs"]),
                json.dumps(state_dict["llm_usage"]),
                entry.state.error,
                json.dumps(state_dict["variables"]),
                json.dumps(state_dict["exec_counts"]),
                json.dumps(state_dict["executed_nodes"]),
                json.dumps(state_dict.get("metrics")) if state_dict.get("metrics") else None,
                entry.access_count,
                datetime.now().isoformat(),
            ),
        )

        entry.is_dirty = False
        entry.is_persisted = True

    async def _persist_old_dirty_entries(self):
        """Persist dirty entries that have been waiting."""
        current_time = time.time()

        async with self._cache_lock:
            for exec_id, entry in self._cache.items():
                if entry.is_dirty:
                    time_since_write = current_time - entry.last_write_time
                    if time_since_write >= self._persistence_delay:
                        await self._persist_entry(exec_id, entry)

    async def _persist_all_dirty(self):
        """Persist all dirty cache entries."""
        async with self._cache_lock:
            for exec_id, entry in self._cache.items():
                if entry.is_dirty:
                    await self._persist_entry(exec_id, entry)

    async def _evict_if_needed(self):
        """Evict cache entries if cache is full."""
        async with self._cache_lock:
            if len(self._cache) <= self._cache_size:
                return

            # Sort by access time and frequency
            entries = [
                (exec_id, entry)
                for exec_id, entry in self._cache.items()
                if exec_id not in self._warm_cache_ids  # Don't evict warm cache
            ]

            entries.sort(key=lambda x: (x[1].access_count, x[1].last_access_time))

            # Evict least recently/frequently used
            evict_count = len(self._cache) - int(self._cache_size * 0.9)  # Keep 90% full

            for exec_id, entry in entries[:evict_count]:
                if entry.is_dirty:
                    await self._persist_entry(exec_id, entry)
                del self._cache[exec_id]
                self._metrics["cache_evictions"] += 1

    async def _update_warm_cache(self):
        """Update the warm cache based on access patterns."""
        # Find most frequently accessed executions
        top_accessed = sorted(self._access_frequency.items(), key=lambda x: x[1], reverse=True)[
            : self._warm_cache_size
        ]

        new_warm_ids = {exec_id for exec_id, _ in top_accessed}

        # Update warm cache IDs
        async with self._cache_lock:
            self._warm_cache_ids = new_warm_ids

        # Reset access frequency counter
        self._access_frequency.clear()

    def _log_metrics(self):
        """Log current metrics."""
        cache_hit_rate = (
            self._metrics["cache_hits"]
            / (self._metrics["cache_hits"] + self._metrics["cache_misses"])
            * 100
            if (self._metrics["cache_hits"] + self._metrics["cache_misses"]) > 0
            else 0
        )

        logger.info(
            f"CacheFirst Metrics - "
            f"Cache hits: {self._metrics['cache_hits']}, "
            f"Cache misses: {self._metrics['cache_misses']}, "
            f"Hit rate: {cache_hit_rate:.1f}%, "
            f"Warm cache hits: {self._metrics['warm_cache_hits']}, "
            f"DB reads: {self._metrics['db_reads']}, "
            f"DB writes: {self._metrics['db_writes']}, "
            f"Checkpoints: {self._metrics['checkpoints']}, "
            f"Evictions: {self._metrics['cache_evictions']}, "
            f"Cache size: {len(self._cache)}/{self._cache_size}"
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

        async with self._cache_lock:
            self._cache[exec_id] = entry

        return state

    async def save_state(self, state: ExecutionState):
        """Save state to cache (deferred database write)."""
        exec_id = state.id

        async with self._cache_lock:
            if exec_id in self._cache:
                entry = self._cache[exec_id]
                entry.state = state
                entry.mark_dirty()
            else:
                entry = CacheEntry(
                    state=state,
                    is_dirty=True,
                    is_persisted=False,
                )
                self._cache[exec_id] = entry

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
        async with self._cache_lock:
            if execution_id in self._cache:
                entry = self._cache[execution_id]
                entry.touch()
                self._access_frequency[execution_id] += 1

                if execution_id in self._warm_cache_ids:
                    self._metrics["warm_cache_hits"] += 1
                else:
                    self._metrics["cache_hits"] += 1

                return entry.state

        self._metrics["cache_misses"] += 1

        # Load from database
        cursor = await self._execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, llm_usage, error, variables,
                   exec_counts, executed_nodes, metrics, access_count
            FROM execution_states
            WHERE execution_id = ?
            """,
            (execution_id,),
        )

        loop = asyncio.get_event_loop()
        row = await loop.run_in_executor(self._executor, cursor.fetchone)

        if not row:
            return None

        state = self._parse_state_from_row(row)

        # Add to cache
        entry = CacheEntry(
            state=state,
            is_persisted=True,
            access_count=row[13] if len(row) > 13 else 0,
        )

        # Populate node data
        for node_id, node_state in state.node_states.items():
            entry.node_statuses[node_id] = node_state.status
            if node_state.error:
                entry.node_errors[node_id] = node_state.error

        entry.node_outputs = state.node_outputs.copy()
        entry.variables = state.variables.copy()
        entry.llm_usage = state.llm_usage

        async with self._cache_lock:
            self._cache[execution_id] = entry

        # Update database access count
        await self._execute(
            "UPDATE execution_states SET access_count = access_count + 1, last_accessed = ? WHERE execution_id = ?",
            (datetime.now().isoformat(), execution_id),
        )

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
        async with self._cache_lock:
            if execution_id not in self._cache:
                # Load state if not in cache
                state = await self.get_state(execution_id)
                if not state:
                    raise ValueError(f"Execution {execution_id} not found")

            entry = self._cache[execution_id]

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
                    wrapped_output = EnvelopeFactory.create(
                        body=str(output), produced_by=str(node_id)
                    )
                serialized_output = serialize_protocol(wrapped_output)

            # Update cache
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
        async with self._cache_lock:
            if execution_id not in self._cache:
                state = await self.get_state(execution_id)
                if not state:
                    raise ValueError(f"Execution {execution_id} not found")

            entry = self._cache[execution_id]
            now = datetime.now().isoformat()

            if status == Status.RUNNING and node_id not in entry.state.executed_nodes:
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
        async with self._cache_lock:
            if execution_id in self._cache:
                entry = self._cache[execution_id]
                entry.touch()
                return entry.node_outputs.get(node_id)

        state = await self.get_state(execution_id)
        if not state:
            return None
        return state.node_outputs.get(node_id)

    async def update_variables(self, execution_id: str, variables: dict[str, Any]):
        """Update execution variables in cache."""
        async with self._cache_lock:
            if execution_id not in self._cache:
                state = await self.get_state(execution_id)
                if not state:
                    raise ValueError(f"Execution {execution_id} not found")

            entry = self._cache[execution_id]
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

        async with self._cache_lock:
            if execution_id not in self._cache:
                state = await self.get_state(execution_id)
                if not state:
                    raise ValueError(f"Execution {execution_id} not found")

            entry = self._cache[execution_id]

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

        async with self._cache_lock:
            if state.id in self._cache:
                entry = self._cache[state.id]
                entry.state = state
                await self._persist_entry(state.id, entry)

                # Remove from cache after delay
                async def delayed_removal():
                    await asyncio.sleep(10)
                    async with self._cache_lock:
                        if state.id in self._cache:
                            del self._cache[state.id]

                asyncio.create_task(delayed_removal())
            else:
                # Direct persist if not in cache
                entry = CacheEntry(state=state, is_dirty=True)
                await self._persist_entry(state.id, entry)

    async def list_executions(
        self,
        diagram_id: DiagramID | None = None,
        status: Status | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        """List executions from database."""
        query = """
        SELECT execution_id, status, diagram_id, started_at, ended_at,
               node_states, node_outputs, llm_usage, error, variables,
               exec_counts, executed_nodes, metrics
        FROM execution_states
        """
        conditions = []
        params = []

        if diagram_id:
            conditions.append("diagram_id = ?")
            params.append(diagram_id)

        if status:
            conditions.append("status = ?")
            params.append(status.value)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await self._execute(query, tuple(params))

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(self._executor, cursor.fetchall)

        executions = []
        for row in rows:
            state = self._parse_state_from_row(row)
            executions.append(state)

        return executions

    async def cleanup_old_states(self, days: int = 7):
        """Cleanup old execution states."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()

        await self._execute("DELETE FROM execution_states WHERE started_at < ?", (cutoff_iso,))

        await self._execute("VACUUM")

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
        return self._metrics.copy()
