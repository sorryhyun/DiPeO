import asyncio
import json
import logging
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from dipeo.core.constants import STATE_DB_PATH
from dipeo.core.execution.node_output import serialize_protocol
from dipeo.models import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeState,
    TokenUsage,
)

from .execution_cache import ExecutionCache
from .message_store import MessageStore

logger = logging.getLogger(__name__)


class StateRegistry:
    # Lightweight registry that stores references to data

    def __init__(
        self,
        db_path: str | None = None,
        message_store: Optional["MessageStore"] = None,
    ):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", str(STATE_DB_PATH))
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)  # Single thread for SQLite
        self._thread_id: int | None = None
        self.message_store = message_store
        self._execution_cache = ExecutionCache(ttl_minutes=60)
        self._initialized = False
        self._initializing = False

    async def initialize(self):
        async with self._lock:
            if self._initialized:
                return
            self._initializing = True
            try:
                await self._connect()
                await self._init_schema()
                self._initialized = True
            finally:
                self._initializing = False

    async def cleanup(self):
        async with self._lock:
            if self._conn:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        self._executor, self._conn.close
                    )
                except RuntimeError:
                    # Executor already shutdown
                    pass
                self._conn = None

            # Don't shutdown executor immediately - let pending operations complete
            if not self._executor._shutdown:
                self._executor.shutdown(wait=False)

            self._initialized = False

    async def _connect(self):
        print(f"[StateRegistry] Attempting to connect to database at: {self.db_path}")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        print(
            f"[StateRegistry] Database directory created/verified: {Path(self.db_path).parent}"
        )

        loop = asyncio.get_event_loop()

        def _connect_sync():
            self._thread_id = threading.get_ident()
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=True,  # Changed to True since we use single thread
                isolation_level=None,  # Autocommit mode
            )
            conn.execute("PRAGMA journal_mode=WAL")
            return conn

        # Ensure executor is available
        if self._executor._shutdown:
            self._executor = ThreadPoolExecutor(max_workers=1)

        try:
            self._conn = await loop.run_in_executor(self._executor, _connect_sync)
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                # Recreate executor and retry
                self._executor = ThreadPoolExecutor(max_workers=1)
                self._conn = await loop.run_in_executor(self._executor, _connect_sync)
            else:
                raise

    async def _execute(self, *args, **kwargs):
        """Execute a database operation in the dedicated thread."""
        # Only ensure initialization if we're not already initializing
        # (to avoid circular dependency when _execute is called from _init_schema)
        if not self._initializing:
            await self._ensure_initialized()

        if self._conn is None:
            raise RuntimeError(
                "StateRegistry not initialized. Call initialize() first."
            )

        # Ensure executor is available
        if self._executor._shutdown:
            self._executor = ThreadPoolExecutor(max_workers=1)

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                self._executor, self._conn.execute, *args, **kwargs
            )
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                # Recreate executor and retry once
                self._executor = ThreadPoolExecutor(max_workers=1)
                return await loop.run_in_executor(
                    self._executor, self._conn.execute, *args, **kwargs
                )
            raise

    async def _ensure_initialized(self):
        """Ensure the registry is initialized, initializing if necessary."""
        if not self._initialized:
            await self.initialize()

        # Check if executor was shutdown and recreate if needed
        if self._executor._shutdown:
            self._executor = ThreadPoolExecutor(max_workers=1)

    async def _init_schema(self):
        schema = """
        CREATE TABLE IF NOT EXISTS execution_states (
            execution_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            diagram_id TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            node_states TEXT NOT NULL,
            node_outputs TEXT NOT NULL,
            token_usage TEXT NOT NULL,
            error TEXT,
            variables TEXT NOT NULL,
            exec_counts TEXT NOT NULL DEFAULT '{}',
            executed_nodes TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_status ON execution_states(status);
        CREATE INDEX IF NOT EXISTS idx_started_at ON execution_states(started_at);

        -- Add columns to existing tables if they don't exist
        -- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we need to check first
        """

        # First, create the tables
        # Ensure executor is available
        if self._executor._shutdown:
            self._executor = ThreadPoolExecutor(max_workers=1)

        try:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._conn.executescript, schema
            )
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                # Recreate executor and retry
                self._executor = ThreadPoolExecutor(max_workers=1)
                await asyncio.get_event_loop().run_in_executor(
                    self._executor, self._conn.executescript, schema
                )
            else:
                raise

        # Then check if columns exist (for migration purposes)
        cursor = await self._execute("PRAGMA table_info(execution_states)")
        columns = await asyncio.get_event_loop().run_in_executor(
            self._executor, cursor.fetchall
        )
        column_names = [col[1] for col in columns]

        # Add missing columns if needed (for existing databases)
        if "exec_counts" not in column_names:
            await self._execute(
                "ALTER TABLE execution_states ADD COLUMN exec_counts TEXT NOT NULL DEFAULT '{}'"
            )
        if "executed_nodes" not in column_names:
            await self._execute(
                "ALTER TABLE execution_states ADD COLUMN executed_nodes TEXT NOT NULL DEFAULT '[]'"
            )

    async def create_execution(
        self,
        execution_id: str | ExecutionID,
        diagram_id: str | DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        await self._ensure_initialized()

        # Handle both str and ExecutionID types
        exec_id = execution_id if isinstance(execution_id, str) else str(execution_id)
        diag_id = None
        if diagram_id:
            diag_id = (
                DiagramID(diagram_id) if isinstance(diagram_id, str) else diagram_id
            )

        now = datetime.now().isoformat()
        state = ExecutionState(
            id=ExecutionID(exec_id),
            status=ExecutionStatus.PENDING,
            diagram_id=diag_id,
            started_at=now,
            ended_at=None,
            node_states={},
            node_outputs={},
            token_usage=TokenUsage(input=0, output=0, cached=None, total=0),
            error=None,
            variables=variables or {},
            is_active=True,
            exec_counts={},
            executed_nodes=[],
        )

        await self.save_state(state)
        return state

    async def save_state(self, state: ExecutionState):
        await self._ensure_initialized()

        # Update cache for active executions
        if state.is_active:
            await self._execution_cache.set(state.id, state)
        else:
            # Remove from cache if execution is no longer active
            await self._execution_cache.remove(state.id)

        async with self._lock:
            # Use model_dump for complete serialization
            state_dict = state.model_dump()

            # Extract fields for database columns
            await self._execute(
                """
                INSERT OR REPLACE INTO execution_states
                (execution_id, status, diagram_id, started_at, ended_at,
                 node_states, node_outputs, token_usage, error, variables,
                 exec_counts, executed_nodes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.id,
                    state.status.value,
                    state.diagram_id,
                    state.started_at,
                    state.ended_at,
                    json.dumps(state_dict["node_states"]),
                    json.dumps(state_dict["node_outputs"]),
                    json.dumps(state_dict["token_usage"]),
                    state.error,
                    json.dumps(state_dict["variables"]),
                    json.dumps(state_dict["exec_counts"]),
                    json.dumps(state_dict["executed_nodes"]),
                ),
            )

    async def get_state(self, execution_id: str) -> ExecutionState | None:
        await self._ensure_initialized()

        # Check cache first
        cached_state = await self._execution_cache.get(execution_id)
        if cached_state:
            return cached_state

        # Fall back to database
        cursor = await self._execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, token_usage, error, variables,
                   exec_counts, executed_nodes
            FROM execution_states
            WHERE execution_id = ?
            """,
            (execution_id,),
        )

        row = await asyncio.get_event_loop().run_in_executor(
            self._executor, cursor.fetchone
        )
        if not row:
            return None

        # Build ExecutionState data dictionary
        state_data = {
            "id": row[0],
            "status": row[1],
            "diagram_id": row[2],
            "started_at": row[3],
            "ended_at": row[4],
            "node_states": json.loads(row[5]) if row[5] else {},
            "node_outputs": json.loads(row[6]) if row[6] else {},
            "token_usage": json.loads(row[7])
            if row[7]
            else {"input": 0, "output": 0, "cached": None, "total": 0},
            "error": row[8],
            "variables": json.loads(row[9]) if row[9] else {},
            "exec_counts": json.loads(row[10]) if len(row) > 10 and row[10] else {},
            "executed_nodes": json.loads(row[11]) if len(row) > 11 and row[11] else [],
            "is_active": False,  # Loaded from DB means it's not active
        }

        # Create ExecutionState from the data
        return ExecutionState(**state_data)

    async def update_status(
        self, execution_id: str, status: ExecutionStatus, error: str | None = None
    ):
        await self._ensure_initialized()

        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.status = status
        state.error = error
        if status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.ABORTED,
        ]:
            state.ended_at = datetime.now().isoformat()
            state.is_active = False

        await self.save_state(state)

    async def get_node_output(
        self, execution_id: str, node_id: str
    ) -> dict[str, Any] | None:
        state = await self.get_state(execution_id)
        if not state:
            return None
        return state.node_outputs.get(node_id)

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        token_usage: TokenUsage | None = None,
    ) -> None:
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        # Handle protocol outputs vs raw outputs
        if hasattr(output, "__class__") and hasattr(output, "to_dict"):
            # It's already a protocol output, serialize it
            serialized_output = serialize_protocol(output)
        elif isinstance(output, dict) and "_protocol_type" in output:
            # It's already a serialized protocol output
            serialized_output = output
        else:
            # It's a raw output, wrap it in a basic protocol format
            from dipeo.core.execution.node_output import BaseNodeOutput
            from dipeo.models import NodeID

            wrapped_output = BaseNodeOutput(
                value={"default": str(output)} if is_exception else output,
                node_id=NodeID(node_id),
                error=str(output) if is_exception else None,
            )
            serialized_output = serialize_protocol(wrapped_output)

        # Handle PersonJob outputs with conversation history
        if (
            isinstance(serialized_output, dict)
            and serialized_output.get("metadata")
            and serialized_output["metadata"].get("_type") == "personjob_output"
            and not state.is_active
        ):
            # Only persist conversation for completed executions
            conversation = serialized_output["metadata"].get("conversation_history", [])
            if conversation and self.message_store:
                message_ref = await self.message_store.store_message(
                    execution_id=execution_id,
                    node_id=node_id,
                    content={"conversation": conversation},
                    person_id=serialized_output["metadata"].get("person_id"),
                    token_count=serialized_output["metadata"].get("token_count"),
                )
                # Replace conversation with reference
                serialized_output["metadata"]["conversation_ref"] = message_ref
                serialized_output["metadata"].pop("conversation_history", None)

        # Store the serialized output
        state.node_outputs[node_id] = serialized_output

        # Update token usage if provided
        if token_usage:
            await self.add_token_usage(execution_id, token_usage)

        await self.save_state(state)

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: NodeExecutionStatus,
        error: str | None = None,
    ):
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        now = datetime.now().isoformat()

        if node_id not in state.node_states:
            state.node_states[node_id] = NodeState(
                status=status,
                started_at=now if status == NodeExecutionStatus.RUNNING else None,
                ended_at=None,
                error=None,
                token_usage=None,
            )
        else:
            state.node_states[node_id].status = status
            if status == NodeExecutionStatus.RUNNING:
                state.node_states[node_id].started_at = now
            elif status in [
                NodeExecutionStatus.COMPLETED,
                NodeExecutionStatus.FAILED,
                NodeExecutionStatus.SKIPPED,
            ]:
                state.node_states[node_id].ended_at = now

        # Update error
        if error:
            state.node_states[node_id].error = error

        await self.save_state(state)

    async def update_variables(self, execution_id: str, variables: dict[str, Any]):
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.variables.update(variables)
        await self.save_state(state)

    async def update_token_usage(self, execution_id: str, tokens: TokenUsage):
        # Update token usage statistics
        # Try to update cache first if execution is active
        cached_state = await self._execution_cache.get(execution_id)
        if cached_state:
            await self._execution_cache.update_token_usage(execution_id, tokens)
            return

        # Fall back to database update
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        # Replace the entire token usage with the new total
        state.token_usage = tokens
        await self.save_state(state)

    async def add_token_usage(self, execution_id: str, tokens: TokenUsage):
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        if state.token_usage:
            state.token_usage.input += tokens.input
            state.token_usage.output += tokens.output
            if tokens.cached:
                state.token_usage.cached = (
                    state.token_usage.cached or 0
                ) + tokens.cached
            state.token_usage.total = state.token_usage.input + state.token_usage.output
        else:
            state.token_usage = tokens

        await self.save_state(state)

    async def list_executions(
        self,
        diagram_id: DiagramID | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        # Build query with optional filters
        query = "SELECT execution_id, status, diagram_id, started_at, ended_at, node_states, node_outputs, token_usage, error, variables, exec_counts, executed_nodes FROM execution_states"
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

        rows = await asyncio.get_event_loop().run_in_executor(
            self._executor, cursor.fetchall
        )

        executions = []
        for row in rows:
            # Build ExecutionState data dictionary
            state_data = {
                "id": row[0],
                "status": row[1],
                "diagram_id": row[2],
                "started_at": row[3],
                "ended_at": row[4],
                "node_states": json.loads(row[5]) if row[5] else {},
                "node_outputs": json.loads(row[6]) if row[6] else {},
                "token_usage": json.loads(row[7])
                if row[7]
                else {"input": 0, "output": 0, "cached": None, "total": 0},
                "error": row[8],
                "variables": json.loads(row[9]) if row[9] else {},
                "exec_counts": json.loads(row[10]) if len(row) > 10 and row[10] else {},
                "executed_nodes": json.loads(row[11])
                if len(row) > 11 and row[11]
                else [],
                "is_active": False,  # Loaded from DB means it's not active
            }

            # Create ExecutionState from the data
            execution_state = ExecutionState(**state_data)
            executions.append(execution_state)

        return executions

    async def cleanup_old_states(self, days: int = 7):
        cutoff_date = datetime.now()
        cutoff_date = cutoff_date.replace(microsecond=0)
        cutoff_iso = (cutoff_date - timedelta(days=days)).isoformat()

        await self._execute(
            "DELETE FROM execution_states WHERE started_at < ?",
            (cutoff_iso,),
        )

        await self._execute("VACUUM")

    async def get_state_from_cache(self, execution_id: str) -> ExecutionState | None:
        return await self._execution_cache.get(execution_id)

    async def create_execution_in_cache(
        self,
        execution_id: str | ExecutionID,
        diagram_id: str | DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        # Handle both str and ExecutionID types
        exec_id = execution_id if isinstance(execution_id, str) else str(execution_id)
        diag_id = None
        if diagram_id:
            diag_id = (
                DiagramID(diagram_id) if isinstance(diagram_id, str) else diagram_id
            )

        now = datetime.now().isoformat()
        state = ExecutionState(
            id=ExecutionID(exec_id),
            status=ExecutionStatus.PENDING,
            diagram_id=diag_id,
            started_at=now,
            ended_at=None,
            node_states={},
            node_outputs={},
            token_usage=TokenUsage(input=0, output=0, cached=None, total=0),
            error=None,
            variables=variables or {},
            is_active=True,
            exec_counts={},
            executed_nodes=[],
        )

        # Only store in cache, not in database
        await self._execution_cache.set(execution_id, state)
        return state

    async def persist_final_state(self, state: ExecutionState):
        # Ensure the state is marked as inactive
        state.is_active = False

        # Save to database
        async with self._lock:
            await self.save_state(state)

        # Remove from cache after persisting
        await self._execution_cache.remove(state.id)
