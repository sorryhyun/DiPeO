"""Async queue-based state store implementation with aiosqlite.

This module provides a thread-safe state store using a single async writer queue
and aiosqlite for consistent async operations, eliminating mixed lock issues.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiosqlite

from dipeo.config import STATE_DB_PATH
from dipeo.diagram_generated import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    LLMUsage,
    NodeState,
    Status,
)
from dipeo.domain.execution.envelope import serialize_protocol
from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort

from .execution_state_cache import ExecutionStateCache

logger = logging.getLogger(__name__)


class AsyncQueueStateStore(StateStorePort):
    """State store implementation using async writer queue and aiosqlite.

    This implementation eliminates mixed threading/async locks by using:
    - A single async writer queue for all database operations
    - aiosqlite for consistent async database access
    - WAL pragma for better concurrency
    - Per-execution caches for fast access
    """

    def __init__(
        self,
        db_path: str | None = None,
        message_store: Any | None = None,
    ):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", str(STATE_DB_PATH))
        self._conn: aiosqlite.Connection | None = None
        self.message_store = message_store
        self._execution_cache = ExecutionStateCache(ttl_seconds=3600)

        # Single writer queue for all DB operations
        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._writer_task: asyncio.Task | None = None

        self._initialized = False
        self._shutdown = False

    async def initialize(self):
        """Initialize the state store."""
        if self._initialized:
            return

        # Create database directory
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        await self._connect()

        # Initialize schema
        await self._init_schema()

        # Start cache
        await self._execution_cache.start()

        # Start writer task
        self._writer_task = asyncio.create_task(self._writer_loop())

        self._initialized = True
        logger.info(f"AsyncQueueStateStore initialized with DB at {self.db_path}")

    async def cleanup(self):
        """Cleanup resources."""
        self._shutdown = True

        # Stop cache
        await self._execution_cache.stop()

        # Signal writer to stop
        await self._write_queue.put(None)

        # Wait for writer to finish
        if self._writer_task:
            await self._writer_task

        # Close database connection
        if self._conn:
            await self._conn.close()
            self._conn = None

        self._initialized = False
        logger.info("AsyncQueueStateStore cleaned up")

    async def _connect(self):
        """Connect to the database with optimal settings."""
        self._conn = await aiosqlite.connect(
            self.db_path,
            isolation_level=None,  # Autocommit mode
        )

        # Enable WAL mode for better concurrency
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA busy_timeout=10000")  # 10 second timeout
        await self._conn.execute("PRAGMA synchronous=NORMAL")  # Better performance with WAL
        await self._conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
        await self._conn.execute("PRAGMA mmap_size=268435456")  # Use memory-mapped I/O (256MB)
        await self._conn.execute("PRAGMA cache_size=-64000")  # 64MB cache

        logger.debug("Database connection established with WAL mode")

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_status ON execution_states(status);
        CREATE INDEX IF NOT EXISTS idx_started_at ON execution_states(started_at);
        CREATE INDEX IF NOT EXISTS idx_diagram_id ON execution_states(diagram_id);
        """

        await self._conn.executescript(schema)
        await self._conn.commit()

        # Try to add metrics column if it doesn't exist (migration)
        try:
            cursor = await self._conn.execute("PRAGMA table_info(execution_states)")
            columns = await cursor.fetchall()
            has_metrics = any(col[1] == "metrics" for col in columns)

            if not has_metrics:
                await self._conn.execute(
                    "ALTER TABLE execution_states ADD COLUMN metrics TEXT DEFAULT NULL"
                )
                await self._conn.commit()
        except Exception as e:
            logger.debug(f"Could not add metrics column (may already exist): {e}")

    async def _writer_loop(self):
        """Background writer loop that processes write operations sequentially."""
        logger.debug("Writer loop started")

        while not self._shutdown:
            try:
                # Get next write operation from queue
                operation = await self._write_queue.get()

                # None signals shutdown
                if operation is None:
                    break

                # Execute the operation
                try:
                    await operation()
                except Exception as e:
                    logger.error(f"Error executing write operation: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in writer loop: {e}")

        logger.debug("Writer loop stopped")

    async def _enqueue_write(self, operation):
        """Enqueue a write operation to be executed by the writer task."""
        if self._shutdown:
            raise RuntimeError("StateStore is shutting down")

        # Create a future to wait for completion
        future = asyncio.Future()

        async def wrapped_operation():
            try:
                result = await operation()
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

        # Add to queue
        await self._write_queue.put(wrapped_operation)

        # Wait for completion
        return await future

    async def create_execution(
        self,
        execution_id: str | ExecutionID,
        diagram_id: str | DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        """Create a new execution."""
        if not self._initialized:
            raise RuntimeError("StateStore not initialized - call initialize() first")

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

        # Cache first for fast access
        cache = await self._execution_cache.get_cache(exec_id)
        await cache.set_state(state)

        # Then persist to DB via queue
        async def persist():
            await self._persist_state_internal(state)

        await self._enqueue_write(persist)

        return state

    async def _persist_state_internal(self, state: ExecutionState):
        """Internal method to persist state (called from writer loop)."""
        state_dict = state.model_dump()

        await self._conn.execute(
            """
            INSERT OR REPLACE INTO execution_states
            (execution_id, status, diagram_id, started_at, ended_at,
             node_states, node_outputs, llm_usage, error, variables,
             exec_counts, executed_nodes, metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state.id,
                state.status.value,
                state.diagram_id,
                state.started_at,
                state.ended_at,
                json.dumps(state_dict["node_states"]),
                json.dumps(state_dict["node_outputs"]),
                json.dumps(state_dict["llm_usage"]),
                state.error,
                json.dumps(state_dict["variables"]),
                json.dumps(state_dict["exec_counts"]),
                json.dumps(state_dict["executed_nodes"]),
                json.dumps(state_dict.get("metrics")) if state_dict.get("metrics") else None,
            ),
        )
        await self._conn.commit()

    async def save_state(self, state: ExecutionState):
        """Save execution state."""
        if not self._initialized:
            raise RuntimeError("StateStore not initialized - call initialize() first")

        # Update cache immediately
        if state.is_active:
            cache = await self._execution_cache.get_cache(state.id)
            await cache.set_state(state)

        # Persist to DB via queue
        async def persist():
            await self._persist_state_internal(state)

        await self._enqueue_write(persist)

    async def get_state(self, execution_id: str) -> ExecutionState | None:
        """Get execution state, preferring cache."""
        if not self._initialized:
            raise RuntimeError("StateStore not initialized - call initialize() first")

        # Try cache first
        cache = await self._execution_cache.get_cache(execution_id)
        cached_state = await cache.get_state()
        if cached_state:
            return cached_state

        # Fall back to DB
        cursor = await self._conn.execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, llm_usage, error, variables,
                   exec_counts, executed_nodes, metrics
            FROM execution_states
            WHERE execution_id = ?
            """,
            (execution_id,),
        )

        row = await cursor.fetchone()
        if not row:
            return None

        # Parse node_outputs
        raw_outputs = json.loads(row[6]) if row[6] else {}
        node_outputs = {}
        for node_id, output_data in raw_outputs.items():
            if isinstance(output_data, dict):
                node_outputs[node_id] = output_data
            else:
                # Fallback for unexpected non-dict data
                node_outputs[node_id] = {
                    "envelope_format": True,
                    "id": str(uuid4()),
                    "trace_id": "",
                    "produced_by": node_id,
                    "content_type": "raw_text",
                    "body": output_data,
                    "meta": {},
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
            "is_active": False,
        }
        return ExecutionState(**state_data)

    async def update_status(self, execution_id: str, status: Status, error: str | None = None):
        """Update execution status."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.status = status
        state.error = error
        if status in [Status.COMPLETED, Status.FAILED, Status.ABORTED]:
            state.ended_at = datetime.now().isoformat()
            state.is_active = False

        await self.save_state(state)

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        llm_usage: LLMUsage | dict | None = None,
    ) -> None:
        """Update node output."""
        # Get from cache for fast update
        cache = await self._execution_cache.get_cache(execution_id)
        state = await cache.get_state()

        if not state:
            # Fall back to DB
            state = await self.get_state(execution_id)
            if not state:
                raise ValueError(f"Execution {execution_id} not found")

        # Handle Envelope outputs
        if hasattr(output, "__class__") and hasattr(output, "to_dict"):
            serialized_output = serialize_protocol(output)
        elif isinstance(output, dict) and (
            output.get("envelope_format") or output.get("_envelope_format")
        ):
            serialized_output = output
        else:
            from dipeo.domain.execution.envelope import EnvelopeFactory

            if is_exception:
                wrapped_output = EnvelopeFactory.error(
                    str(output),
                    error_type=type(output).__name__
                    if hasattr(output, "__class__")
                    else "Exception",
                    node_id=str(node_id),
                )
            else:
                wrapped_output = EnvelopeFactory.text(str(output), node_id=str(node_id))
            serialized_output = serialize_protocol(wrapped_output)

        # Update cache immediately
        await cache.set_node_output(node_id, serialized_output)

        # Update state
        state.node_outputs[node_id] = serialized_output

        # Update LLM usage if provided
        if llm_usage:
            await self.add_llm_usage(execution_id, llm_usage)

        # Persist to DB
        await self.save_state(state)

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: Status,
        error: str | None = None,
    ):
        """Update node status."""
        # Get from cache
        cache = await self._execution_cache.get_cache(execution_id)
        state = await cache.get_state()

        if not state:
            state = await self.get_state(execution_id)
            if not state:
                raise ValueError(f"Execution {execution_id} not found")

        now = datetime.now().isoformat()

        # Add node to executed_nodes list when it starts executing
        if status == Status.RUNNING and node_id not in state.executed_nodes:
            state.executed_nodes.append(node_id)

        if node_id not in state.node_states:
            state.node_states[node_id] = NodeState(
                status=status,
                started_at=now if status == Status.RUNNING else None,
                ended_at=None,
                error=None,
                llm_usage=None,
            )
        else:
            state.node_states[node_id].status = status
            if status == Status.RUNNING:
                state.node_states[node_id].started_at = now
            elif status in [Status.COMPLETED, Status.FAILED, Status.SKIPPED]:
                state.node_states[node_id].ended_at = now

        if error:
            state.node_states[node_id].error = error

        # Update cache
        await cache.set_node_status(node_id, status, error)

        # Persist
        await self.save_state(state)

    async def get_node_output(self, execution_id: str, node_id: str) -> dict[str, Any] | None:
        """Get node output."""
        # Try cache first
        cache = await self._execution_cache.get_cache(execution_id)
        output = await cache.get_node_output(node_id)
        if output is not None:
            return output

        # Fall back to full state
        state = await self.get_state(execution_id)
        if not state:
            return None
        return state.node_outputs.get(node_id)

    async def update_variables(self, execution_id: str, variables: dict[str, Any]):
        """Update execution variables."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.variables.update(variables)

        # Update cache
        cache = await self._execution_cache.get_cache(execution_id)
        await cache.update_variables(variables)

        await self.save_state(state)

    async def update_metrics(self, execution_id: str, metrics: dict[str, Any]):
        """Update execution metrics."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.metrics = metrics
        await self.save_state(state)

    async def add_llm_usage(self, execution_id: str, usage: LLMUsage | dict):
        """Add LLM usage."""
        # Convert dict to LLMUsage if needed
        if isinstance(usage, dict):
            usage = LLMUsage(
                input=usage.get("input", 0),
                output=usage.get("output", 0),
                cached=usage.get("cached"),
                total=usage.get("total", 0),
            )

        cache = await self._execution_cache.get_cache(execution_id)
        await cache.add_llm_usage(usage)

        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        if state.llm_usage:
            state.llm_usage.input += usage.input
            state.llm_usage.output += usage.output
            if usage.cached:
                state.llm_usage.cached = (state.llm_usage.cached or 0) + usage.cached
            state.llm_usage.total = state.llm_usage.input + state.llm_usage.output
        else:
            state.llm_usage = usage

        await self.save_state(state)

    async def persist_final_state(self, state: ExecutionState):
        """Persist final state and remove from cache."""
        state.is_active = False
        await self.save_state(state)
        await self._execution_cache.remove_cache(state.id)

    async def list_executions(
        self,
        diagram_id: DiagramID | None = None,
        status: Status | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        """List executions."""
        query = "SELECT execution_id, status, diagram_id, started_at, ended_at, node_states, node_outputs, llm_usage, error, variables, exec_counts, executed_nodes, metrics FROM execution_states"
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

        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()

        executions = []
        for row in rows:
            # Parse node_outputs
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
                        "body": output_data,
                        "meta": {},
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
                "is_active": False,
            }
            execution_state = ExecutionState(**state_data)
            executions.append(execution_state)

        return executions

    async def cleanup_old_states(self, days: int = 7):
        """Cleanup old execution states."""
        cutoff_date = datetime.now()
        cutoff_date = cutoff_date.replace(microsecond=0)
        cutoff_iso = (cutoff_date - timedelta(days=days)).isoformat()

        async def cleanup():
            await self._conn.execute(
                "DELETE FROM execution_states WHERE started_at < ?",
                (cutoff_iso,),
            )
            await self._conn.execute("VACUUM")
            await self._conn.commit()

        await self._enqueue_write(cleanup)
