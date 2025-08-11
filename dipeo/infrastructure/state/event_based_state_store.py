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
from dipeo.diagram_generated import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    Status,
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
        self._executor = ThreadPoolExecutor(max_workers=1)  # Single worker to avoid threading issues
        self._executor_shutdown = False  # Track executor state ourselves
        self._thread_id: int | None = None
        self.message_store = message_store
        self._execution_cache = ExecutionStateCache(ttl_seconds=3600)
        self._reconnect_lock = asyncio.Lock()  # Separate lock for reconnection
        self._initialized = False
        self._db_lock = asyncio.Lock()  # Only for DB schema operations
        self._conn_lock = threading.Lock()  # Thread-safe connection access
    
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
            # Use thread-safe mode for SQLite
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threaded access
                isolation_level=None,
                timeout=30.0,  # 30 second timeout
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=10000")  # 10 second timeout for locks
            conn.execute("PRAGMA synchronous=NORMAL")  # Better performance with WAL
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            conn.execute("PRAGMA mmap_size=268435456")  # Use memory-mapped I/O (256MB)
            return conn
        
        # Recreate executor if it was shut down
        if self._executor_shutdown:
            self._executor = ThreadPoolExecutor(max_workers=1)
            self._executor_shutdown = False
        
        try:
            # Create new connection
            new_conn = await loop.run_in_executor(self._executor, _connect_sync)
            
            # Swap connections atomically
            old_conn = self._conn
            self._conn = new_conn
            
            # Close old connection if any (after setting new one)
            if old_conn:
                try:
                    await loop.run_in_executor(self._executor, old_conn.close)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def _execute_internal(self, *args, **kwargs):
        """Internal execute method for use during initialization."""
        if self._conn is None:
            raise RuntimeError("Database connection not established")
        
        # Check if executor is still valid
        if self._executor_shutdown:
            raise RuntimeError("Executor has been shut down - reinitialize the store")
        
        loop = asyncio.get_event_loop()
        
        # Retry logic for connection issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await loop.run_in_executor(
                    self._executor, self._conn.execute, *args, **kwargs
                )
            except (sqlite3.InterfaceError, sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
                # These errors typically indicate connection issues
                if attempt < max_retries - 1:
                    logger.warning(f"SQLite error (attempt {attempt + 1}/{max_retries}): {e}, reconnecting...")
                    async with self._reconnect_lock:
                        # Only reconnect if connection is still the same one that failed
                        await self._connect()
                    # Small delay before retry
                    await asyncio.sleep(0.1 * (attempt + 1))
                else:
                    logger.error(f"SQLite error after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                # Other errors should not trigger reconnection
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
        CREATE INDEX IF NOT EXISTS idx_diagram_id ON execution_states(diagram_id);
        """
        
        loop = asyncio.get_event_loop()
        
        # Retry logic for schema initialization
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await loop.run_in_executor(
                    self._executor, self._conn.executescript, schema
                )
                break
            except (sqlite3.InterfaceError, sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"SQLite error during schema init (attempt {attempt + 1}/{max_retries}): {e}")
                    async with self._reconnect_lock:
                        await self._connect()
                    await asyncio.sleep(0.1 * (attempt + 1))
                else:
                    logger.error(f"Failed to initialize schema after {max_retries} attempts: {e}")
                    raise
        
        # Try to add metrics column to existing tables (migration)
        try:
            # Check if metrics column exists first
            cursor = await self._execute_internal(
                "PRAGMA table_info(execution_states)"
            )
            columns = await loop.run_in_executor(self._executor, cursor.fetchall)
            has_metrics = any(col[1] == "metrics" for col in columns)
            
            if not has_metrics:
                await self._execute_internal(
                    "ALTER TABLE execution_states ADD COLUMN metrics TEXT DEFAULT NULL"
                )
        except Exception as e:
            # Log but don't fail - column might already exist
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
            diag_id = (
                DiagramID(diagram_id) if isinstance(diagram_id, str) else diagram_id
            )
        
        now = datetime.now().isoformat()
        state = ExecutionState(
            id=ExecutionID(exec_id),
            status=Status.PENDING,
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
        
        from dipeo.diagram_generated import SerializedNodeOutput
        
        # Parse node_outputs and convert to SerializedNodeOutput objects
        raw_outputs = json.loads(row[6]) if row[6] else {}
        node_outputs = {}
        for node_id, output_data in raw_outputs.items():
            if isinstance(output_data, dict):
                # Map _protocol_type to type field (using alias)
                if "_protocol_type" in output_data:
                    protocol_type = output_data.pop("_protocol_type")
                    # Map BaseNodeOutput to a valid type for SerializedNodeOutput
                    if protocol_type == "BaseNodeOutput":
                        output_data["_type"] = "TextOutput"  # Default fallback type
                    else:
                        output_data["_type"] = protocol_type
                # Skip SerializedNodeOutput conversion due to Pydantic _type field issue
                node_outputs[node_id] = output_data
            else:
                # Fallback for unexpected data - use dict instead of SerializedNodeOutput
                node_outputs[node_id] = {
                    "_type": "Unknown",
                    "value": output_data,
                    "node_id": node_id,
                    "metadata": "{}"
                }
        
        state_data = {
            "id": row[0],
            "status": row[1],
            "diagram_id": row[2],
            "started_at": row[3],
            "ended_at": row[4],
            "node_states": json.loads(row[5]) if row[5] else {},
            "node_outputs": node_outputs,
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
        self, execution_id: str, status: Status, error: str | None = None
    ):
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
            state.is_active = False
        
        await self.save_state(state)
    
    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        token_usage: TokenUsage | dict | None = None,
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
            from dipeo.diagram_generated import NodeID
            
            wrapped_output = BaseNodeOutput(
                value={"default": str(output)} if is_exception else output,
                node_id=NodeID(node_id),
                error=str(output) if is_exception else None,
            )
            serialized_output = serialize_protocol(wrapped_output)
        
        # Convert to SerializedNodeOutput if needed
        from dipeo.diagram_generated import SerializedNodeOutput
        if isinstance(serialized_output, dict):
            # Skip SerializedNodeOutput conversion for now due to Pydantic _type field issue
            # Just use the dict directly which has all the needed fields
            serialized_node_output = serialized_output
        else:
            serialized_node_output = serialized_output
        
        # Update cache immediately
        await cache.set_node_output(node_id, serialized_output)
        
        # Update state
        state.node_outputs[node_id] = serialized_node_output
        
        # Update token usage if provided
        if token_usage:
            await self.add_token_usage(execution_id, token_usage)
        
        # Persist to DB
        await self._persist_state(state)
    
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
        
        if node_id not in state.node_states:
            state.node_states[node_id] = NodeState(
                status=status,
                started_at=now if status == Status.RUNNING else None,
                ended_at=None,
                error=None,
                token_usage=None,
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
    
    async def update_metrics(self, execution_id: str, metrics: dict[str, Any]):
        """Update execution metrics."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
        
        state.metrics = metrics
        await self.save_state(state)
    
    async def add_token_usage(self, execution_id: str, tokens: TokenUsage | dict):
        """Add token usage."""
        # Convert dict to TokenUsage if needed
        if isinstance(tokens, dict):
            tokens = TokenUsage(
                input=tokens.get('input', 0),
                output=tokens.get('output', 0),
                cached=tokens.get('cached'),
                total=tokens.get('total', 0)
            )
        
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
        status: Status | None = None,
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
        
        from dipeo.diagram_generated import SerializedNodeOutput
        
        executions = []
        for row in rows:
            # Parse node_outputs and convert to SerializedNodeOutput objects
            raw_outputs = json.loads(row[6]) if row[6] else {}
            node_outputs = {}
            for node_id, output_data in raw_outputs.items():
                if isinstance(output_data, dict):
                    # Ensure _protocol_type is preserved as _type
                    if "_protocol_type" in output_data and "_type" not in output_data:
                        protocol_type = output_data["_protocol_type"]
                        # Map BaseNodeOutput to a valid type for SerializedNodeOutput
                        if protocol_type == "BaseNodeOutput":
                            output_data["_type"] = "TextOutput"  # Default fallback type
                        else:
                            output_data["_type"] = protocol_type
                    # Skip SerializedNodeOutput conversion due to Pydantic _type field issue
                    node_outputs[node_id] = output_data
                else:
                    # Fallback for unexpected data - use dict instead of SerializedNodeOutput
                    node_outputs[node_id] = {
                        "_protocol_type": "Unknown",
                        "value": output_data,
                        "node_id": node_id,
                        "metadata": "{}"
                    }
            
            state_data = {
                "id": row[0],
                "status": row[1],
                "diagram_id": row[2],
                "started_at": row[3],
                "ended_at": row[4],
                "node_states": json.loads(row[5]) if row[5] else {},
                "node_outputs": node_outputs,
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