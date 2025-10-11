"""Persistence management for cache-first state store."""

import asyncio
import json
import logging
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import ExecutionState, NodeState, Status

from .models import CacheEntry, CacheMetrics

logger = get_module_logger(__name__)


class PersistenceManager:
    """Manages database operations and persistence."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        # Use single worker to serialize database access and avoid threading issues
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._metrics = CacheMetrics()

    @property
    def metrics(self) -> CacheMetrics:
        """Get persistence metrics."""
        return self._metrics

    async def connect(self) -> None:
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

    async def disconnect(self) -> None:
        """Disconnect from database."""
        if self._conn:
            self._conn.close()
            self._conn = None
        # Don't shutdown executor as it might be reused

    def shutdown(self) -> None:
        """Shutdown the executor (call only when completely done)."""
        self._executor.shutdown(wait=False)

    async def init_schema(self) -> None:
        """Initialize database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS executions (
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

        CREATE INDEX IF NOT EXISTS idx_status ON executions(status);
        CREATE INDEX IF NOT EXISTS idx_started_at ON executions(started_at);
        CREATE INDEX IF NOT EXISTS idx_diagram_id ON executions(diagram_id);
        CREATE INDEX IF NOT EXISTS idx_access_count ON executions(access_count DESC);
        CREATE INDEX IF NOT EXISTS idx_last_accessed ON executions(last_accessed DESC);

        -- Transitions table for idempotency
        CREATE TABLE IF NOT EXISTS transitions (
            id TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL,
            node_id TEXT,
            phase TEXT NOT NULL,
            seq INTEGER NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE UNIQUE INDEX IF NOT EXISTS ux_exec_seq ON transitions(execution_id, seq);
        CREATE INDEX IF NOT EXISTS idx_exec_transitions ON transitions(execution_id);
        CREATE INDEX IF NOT EXISTS idx_created_at ON transitions(created_at DESC);
        """

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._conn.executescript, schema)

    async def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a database query."""
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(self._executor, self._conn.execute, query, params)

        # Update metrics
        if query.strip().upper().startswith("SELECT"):
            self._metrics.db_reads += 1
        else:
            self._metrics.db_writes += 1

        return cursor

    async def persist_entry(
        self, execution_id: str, entry: CacheEntry, use_full_sync: bool = False
    ) -> None:
        """Persist a cache entry to database with optional enhanced durability."""
        from dipeo.infrastructure.timing import atime_phase

        async with atime_phase(str(execution_id), "system", "db_serialize"):
            state_dict = entry.state.model_dump()
            # DEBUG: Check if metrics are in the dump
            if state_dict.get("metrics"):
                logger.info(
                    f"[PERSIST] {execution_id[:8]}... HAS metrics: {len(state_dict['metrics'].get('node_metrics', {})) if isinstance(state_dict['metrics'], dict) else 'N/A'} nodes"
                )
            else:
                logger.warning(
                    f"[PERSIST] {execution_id[:8]}... NO metrics (metrics={state_dict.get('metrics')})"
                )

        # Use enhanced durability for critical writes
        if use_full_sync:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor, self._conn.execute, "PRAGMA synchronous=FULL"
            )

        try:
            async with atime_phase(str(execution_id), "system", "db_write"):
                await self.execute(
                    """
                    INSERT INTO executions
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
                        json.dumps(state_dict.get("metrics"))
                        if state_dict.get("metrics")
                        else None,
                        entry.access_count,
                        datetime.now().isoformat(),
                    ),
                )

            # Force commit for critical writes
            if use_full_sync:
                async with atime_phase(str(execution_id), "system", "db_commit"):
                    await loop.run_in_executor(self._executor, self._conn.commit)

        finally:
            # Restore normal synchronous mode after critical write
            if use_full_sync:
                await loop.run_in_executor(
                    self._executor, self._conn.execute, "PRAGMA synchronous=NORMAL"
                )

        entry.is_dirty = False
        entry.is_persisted = True

    async def load_state(self, execution_id: str) -> ExecutionState | None:
        """Load execution state from database."""
        cursor = await self.execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, llm_usage, error, variables,
                   exec_counts, executed_nodes, metrics, access_count
            FROM executions
            WHERE execution_id = ?
            """,
            (execution_id,),
        )

        loop = asyncio.get_event_loop()
        row = await loop.run_in_executor(self._executor, cursor.fetchone)

        if not row:
            return None

        return self._parse_state_from_row(row)

    async def load_warm_cache_states(self, limit: int) -> list[tuple[ExecutionState, int]]:
        """Load frequently accessed states for cache warming."""
        cursor = await self.execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, llm_usage, error, variables,
                   exec_counts, executed_nodes, metrics, access_count
            FROM executions
            WHERE status IN (?, ?)
            ORDER BY access_count DESC, last_accessed DESC
            LIMIT ?
            """,
            (Status.RUNNING.value, Status.PENDING.value, limit),
        )

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(self._executor, cursor.fetchall)

        states = []
        for row in rows:
            state = self._parse_state_from_row(row)
            access_count = row[13] if len(row) > 13 else 0
            states.append((state, access_count))

        return states

    async def update_access_tracking(self, execution_id: str) -> None:
        """Update access count and timestamp for an execution."""
        await self.execute(
            """
            UPDATE executions
            SET access_count = access_count + 1,
                last_accessed = ?
            WHERE execution_id = ?
            """,
            (datetime.now().isoformat(), execution_id),
        )

    async def list_executions(
        self,
        diagram_id: str | None = None,
        status: Status | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        """List executions from database."""
        query = """
        SELECT execution_id, status, diagram_id, started_at, ended_at,
               node_states, node_outputs, llm_usage, error, variables,
               exec_counts, executed_nodes, metrics
        FROM executions
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

        cursor = await self.execute(query, tuple(params))

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(self._executor, cursor.fetchall)

        executions = []
        for row in rows:
            state = self._parse_state_from_row(row)
            executions.append(state)

        return executions

    async def cleanup_old_states(self, days: int = 7) -> None:
        """Cleanup old execution states."""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()

        await self.execute("DELETE FROM executions WHERE started_at < ?", (cutoff_iso,))
        await self.execute("VACUUM")

    async def record_transition(
        self,
        execution_id: str,
        node_id: str | None,
        phase: str,
        seq: int,
        payload: dict[str, Any],
    ) -> bool:
        """Record a state transition with idempotency.

        Returns True if this is a new transition, False if it already existed.
        """
        transition_id = f"{execution_id}:{seq}"

        try:
            await self.execute(
                """
                INSERT INTO transitions (id, execution_id, node_id, phase, seq, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    transition_id,
                    execution_id,
                    node_id,
                    phase,
                    seq,
                    json.dumps(payload),
                ),
            )
            return True
        except sqlite3.IntegrityError:
            # Transition already exists - idempotent operation
            logger.debug(f"Transition {transition_id} already exists (idempotent)")
            return False

    async def get_latest_sequence(self, execution_id: str) -> int:
        """Get the latest sequence number for an execution."""
        cursor = await self.execute(
            "SELECT MAX(seq) FROM transitions WHERE execution_id = ?",
            (execution_id,),
        )

        loop = asyncio.get_event_loop()
        row = await loop.run_in_executor(self._executor, cursor.fetchone)

        return row[0] if row and row[0] is not None else 0

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
