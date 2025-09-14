"""Event-based state store implementation without global locks."""

import asyncio
import json
import logging
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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
from dipeo.domain.execution.envelope import serialize_protocol
from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort

logger = logging.getLogger(__name__)


class EventBasedStateStore(StateStorePort):
    """State store implementation using per-execution caches instead of global locks."""

    def __init__(
        self,
        db_path: str | None = None,
        message_store: Any | None = None,
    ):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", str(STATE_DB_PATH))
        self._conn: sqlite3.Connection | None = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._executor_shutdown = False
        self._thread_id: int | None = None
        self.message_store = message_store
        self._reconnect_lock = asyncio.Lock()
        self._initialized = False
        self._db_lock = asyncio.Lock()
        self._conn_lock = threading.Lock()

    async def initialize(self):
        """Initialize the state store."""
        if self._initialized:
            return

        async with self._db_lock:
            if self._initialized:
                return

            await self._connect()
            await self._init_schema()
            self._initialized = True

    async def cleanup(self):
        """Cleanup resources."""
        async with self._db_lock:
            if self._conn:
                import contextlib

                with contextlib.suppress(RuntimeError):
                    await asyncio.get_event_loop().run_in_executor(self._executor, self._conn.close)
                self._conn = None

            if not self._executor_shutdown:
                self._executor.shutdown(wait=False)
                self._executor_shutdown = True

            self._initialized = False

    async def _connect(self):
        """Connect to the database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()

        def _connect_sync():
            self._thread_id = threading.get_ident()
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,
                timeout=30.0,
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=10000")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")
            return conn

        if self._executor_shutdown:
            self._executor = ThreadPoolExecutor(max_workers=1)
            self._executor_shutdown = False

        try:
            new_conn = await loop.run_in_executor(self._executor, _connect_sync)

            old_conn = self._conn
            self._conn = new_conn

            if old_conn:
                import contextlib

                with contextlib.suppress(Exception):
                    await loop.run_in_executor(self._executor, old_conn.close)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def _execute_internal(self, *args, **kwargs):
        """Internal execute method for use during initialization."""
        if self._conn is None:
            raise RuntimeError("Database connection not established")

        if self._executor_shutdown:
            raise RuntimeError("Executor has been shut down - reinitialize the store")

        loop = asyncio.get_event_loop()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await loop.run_in_executor(
                    self._executor, self._conn.execute, *args, **kwargs
                )
            except (
                sqlite3.InterfaceError,
                sqlite3.ProgrammingError,
                sqlite3.OperationalError,
            ) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"SQLite error (attempt {attempt + 1}/{max_retries}): {e}, reconnecting..."
                    )
                    async with self._reconnect_lock:
                        await self._connect()
                    await asyncio.sleep(0.1 * (attempt + 1))
                else:
                    logger.error(f"SQLite error after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                raise

    async def _execute(self, *args, **kwargs):
        """Execute a database operation without global lock."""
        if not self._initialized:
            raise RuntimeError("StateStore not initialized - call initialize() first")

        return await self._execute_internal(*args, **kwargs)

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

        loop = asyncio.get_event_loop()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                await loop.run_in_executor(self._executor, self._conn.executescript, schema)
                break
            except (
                sqlite3.InterfaceError,
                sqlite3.ProgrammingError,
                sqlite3.OperationalError,
            ) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"SQLite error during schema init (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    async with self._reconnect_lock:
                        await self._connect()
                    await asyncio.sleep(0.1 * (attempt + 1))
                else:
                    logger.error(f"Failed to initialize schema after {max_retries} attempts: {e}")
                    raise

        try:
            cursor = await self._execute_internal("PRAGMA table_info(execution_states)")
            columns = await loop.run_in_executor(self._executor, cursor.fetchall)
            has_metrics = any(col[1] == "metrics" for col in columns)

            if not has_metrics:
                await self._execute_internal(
                    "ALTER TABLE execution_states ADD COLUMN metrics TEXT DEFAULT NULL"
                )
        except Exception as e:
            logger.debug(f"Could not add metrics column (may already exist): {e}")

    async def create_execution(
        self,
        execution_id: str | ExecutionID,
        diagram_id: str | DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        """Create a new execution."""
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

        await self._persist_state(state)

        return state

    async def save_state(self, state: ExecutionState):
        """Save execution state."""
        # Persist to database to ensure data is saved
        await self._persist_state(state)

    async def _persist_state(self, state: ExecutionState):
        """Persist state to database without global lock."""
        state_dict = state.model_dump()

        await self._execute(
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

    async def get_state(self, execution_id: str) -> ExecutionState | None:
        """Get execution state from database."""
        # Query database directly
        cursor = await self._execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, llm_usage, error, variables,
                   exec_counts, executed_nodes, metrics
            FROM execution_states
            WHERE execution_id = ?
            """,
            (execution_id,),
        )

        row = await asyncio.get_event_loop().run_in_executor(self._executor, cursor.fetchone)
        if not row:
            return None

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
        if status in [
            Status.COMPLETED,
            Status.FAILED,
            Status.ABORTED,
        ]:
            state.ended_at = datetime.now().isoformat()

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
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

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

        state.node_outputs[node_id] = serialized_output

        if llm_usage:
            await self.add_llm_usage(execution_id, llm_usage)

        await self._persist_state(state)

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: Status,
        error: str | None = None,
    ):
        """Update node status."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        now = datetime.now().isoformat()

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
            elif status in [
                Status.COMPLETED,
                Status.FAILED,
                Status.SKIPPED,
            ]:
                state.node_states[node_id].ended_at = now

        if error:
            state.node_states[node_id].error = error

        await self.save_state(state)

    async def get_node_output(self, execution_id: str, node_id: str) -> dict[str, Any] | None:
        """Get node output."""
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
        if isinstance(usage, dict):
            usage = LLMUsage(
                input=usage.get("input", 0),
                output=usage.get("output", 0),
                cached=usage.get("cached"),
                total=usage.get("total", 0),
            )

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
        """Persist final state and delay cache removal to avoid race conditions."""
        # Mark state as inactive before final persistence
        state.is_active = False

        # Ensure the final state is properly persisted to database
        await self._persist_state(state)

        # No cache to remove anymore - state is persisted to database

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

        cursor = await self._execute(query, params)

        rows = await asyncio.get_event_loop().run_in_executor(self._executor, cursor.fetchall)

        executions = []
        for row in rows:
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

        await self._execute(
            "DELETE FROM execution_states WHERE started_at < ?",
            (cutoff_iso,),
        )

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
