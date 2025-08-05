"""Event-based state store implementation without global locks."""

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
from dipeo.core.ports import StateStorePort
from dipeo.models import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeState,
    TokenUsage,
)

from .execution_state_cache import ExecutionStateCache

logger = logging.getLogger(__name__)


class EventBasedStateStore(StateStorePort):
    """State store implementation using per-execution caches instead of global locks."""
    
    def __init__(
        self,
        db_path: str | None = None,
        message_store: Optional[Any] = None,
    ):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", str(STATE_DB_PATH))
        self._conn: sqlite3.Connection | None = None
        self._executor = ThreadPoolExecutor(max_workers=4)  # Multiple workers for parallel writes
        self._thread_id: int | None = None
        self.message_store = message_store
        self._execution_cache = ExecutionStateCache(ttl_seconds=3600)
        self._initialized = False
        self._db_lock = asyncio.Lock()  # Only for DB schema operations
    
    async def initialize(self):
        """Initialize the state store."""
        if self._initialized:
            return
            
        async with self._db_lock:
            if self._initialized:
                return
                
            await self._connect()
            await self._init_schema()
            await self._execution_cache.start()
            self._initialized = True
            logger.info("EventBasedStateStore initialized")
    
    async def cleanup(self):
        """Cleanup resources."""
        # Stop cache first
        await self._execution_cache.stop()
        
        # Close DB connection
        async with self._db_lock:
            if self._conn:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        self._executor, self._conn.close
                    )
                except RuntimeError:
                    pass
                self._conn = None
            
            if not self._executor._shutdown:
                self._executor.shutdown(wait=False)
            
            self._initialized = False
    
    async def _connect(self):
        """Connect to the database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        loop = asyncio.get_event_loop()
        
        def _connect_sync():
            self._thread_id = threading.get_ident()
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threaded access
                isolation_level=None,
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")  # 5 second timeout for locks
            return conn
        
        if self._executor._shutdown:
            self._executor = ThreadPoolExecutor(max_workers=4)
        
        self._conn = await loop.run_in_executor(self._executor, _connect_sync)
    
    async def _execute_internal(self, *args, **kwargs):
        """Internal execute method for use during initialization."""
        if self._conn is None:
            raise RuntimeError("Database connection not established")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._conn.execute, *args, **kwargs
        )
    
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
            token_usage TEXT NOT NULL,
            error TEXT,
            variables TEXT NOT NULL,
            exec_counts TEXT NOT NULL DEFAULT '{}',
            executed_nodes TEXT NOT NULL DEFAULT '[]',
            metrics TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_status ON execution_states(status);
        CREATE INDEX IF NOT EXISTS idx_started_at ON execution_states(started_at);
        """
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, self._conn.executescript, schema
        )
        
        # Try to add metrics column to existing tables
        try:
            await self._execute_internal("ALTER TABLE execution_states ADD COLUMN metrics TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
    
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
        
        # Cache first for fast access
        cache = await self._execution_cache.get_cache(exec_id)
        await cache.set_state(state)
        
        # Then persist to DB
        await self._persist_state(state)
        
        return state
    
    async def save_state(self, state: ExecutionState):
        """Save execution state."""
        # Update cache
        if state.is_active:
            cache = await self._execution_cache.get_cache(state.id)
            await cache.set_state(state)
        
        # Persist to DB (no global lock needed)
        await self._persist_state(state)
    
    async def _persist_state(self, state: ExecutionState):
        """Persist state to database without global lock."""
        state_dict = state.model_dump()
        
        await self._execute(
            """
            INSERT OR REPLACE INTO execution_states
            (execution_id, status, diagram_id, started_at, ended_at,
             node_states, node_outputs, token_usage, error, variables,
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
                json.dumps(state_dict["token_usage"]),
                state.error,
                json.dumps(state_dict["variables"]),
                json.dumps(state_dict["exec_counts"]),
                json.dumps(state_dict["executed_nodes"]),
                json.dumps(state_dict.get("metrics")) if state_dict.get("metrics") else None,
            ),
        )
    
    async def get_state(self, execution_id: str) -> ExecutionState | None:
        """Get execution state, preferring cache."""
        # Try cache first
        cache = await self._execution_cache.get_cache(execution_id)
        cached_state = await cache.get_state()
        if cached_state:
            return cached_state
        
        # Fall back to DB
        cursor = await self._execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, token_usage, error, variables,
                   exec_counts, executed_nodes, metrics
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
            "metrics": json.loads(row[12]) if len(row) > 12 and row[12] else None,
            "is_active": False,
        }
        return ExecutionState(**state_data)
    
    async def update_status(
        self, execution_id: str, status: ExecutionStatus, error: str | None = None
    ):
        """Update execution status."""
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
    
    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        token_usage: TokenUsage | None = None,
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
        
        # Handle protocol outputs vs raw outputs
        if hasattr(output, "__class__") and hasattr(output, "to_dict"):
            serialized_output = serialize_protocol(output)
        elif isinstance(output, dict) and "_protocol_type" in output:
            serialized_output = output
        else:
            from dipeo.core.execution.node_output import BaseNodeOutput
            from dipeo.models import NodeID
            
            wrapped_output = BaseNodeOutput(
                value={"default": str(output)} if is_exception else output,
                node_id=NodeID(node_id),
                error=str(output) if is_exception else None,
            )
            serialized_output = serialize_protocol(wrapped_output)
        
        # Update cache immediately
        await cache.set_node_output(node_id, serialized_output)
        
        # Update state
        state.node_outputs[node_id] = serialized_output
        
        # Update token usage if provided
        if token_usage:
            await self.add_token_usage(execution_id, token_usage)
        
        # Persist to DB
        await self._persist_state(state)
    
    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: NodeExecutionStatus,
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
        
        if error:
            state.node_states[node_id].error = error
        
        # Update cache
        await cache.set_node_status(node_id, status, error)
        
        # Persist
        await self.save_state(state)
    
    async def get_node_output(
        self, execution_id: str, node_id: str
    ) -> dict[str, Any] | None:
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
    
    async def add_token_usage(self, execution_id: str, tokens: TokenUsage):
        """Add token usage."""
        cache = await self._execution_cache.get_cache(execution_id)
        await cache.add_token_usage(tokens)
        
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
    
    async def persist_final_state(self, state: ExecutionState):
        """Persist final state and remove from cache."""
        state.is_active = False
        await self._persist_state(state)
        await self._execution_cache.remove_cache(state.id)
    
    async def list_executions(
        self,
        diagram_id: DiagramID | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        """List executions."""
        query = "SELECT execution_id, status, diagram_id, started_at, ended_at, node_states, node_outputs, token_usage, error, variables, exec_counts, executed_nodes, metrics FROM execution_states"
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