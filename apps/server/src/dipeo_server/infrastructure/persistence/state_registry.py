import asyncio
import json
import logging
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dipeo_domain import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeOutput,
    NodeState,
    TokenUsage,
)

from .message_store import MessageStore

try:
    from config import STATE_DB_PATH
except ImportError:
    STATE_DB_PATH = Path("/tmp/dipeo_state.db")

logger = logging.getLogger(__name__)


class StateRegistry:
    """Lightweight registry that stores references to data."""

    def __init__(self, db_path: Optional[str] = None, message_store: Optional['MessageStore'] = None):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", str(STATE_DB_PATH))
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)  # Single thread for SQLite
        self._thread_id: Optional[int] = None
        self.message_store = message_store

    async def initialize(self):
        await self._connect()
        await self._init_schema()

    async def cleanup(self):
        if self._conn:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._conn.close
            )
            self._conn = None
        self._executor.shutdown(wait=True)

    async def _connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

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

        self._conn = await loop.run_in_executor(self._executor, _connect_sync)

    async def _execute(self, *args, **kwargs):
        """Execute a database operation in the dedicated thread."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._conn.execute, *args, **kwargs)

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_status ON execution_states(status);
        CREATE INDEX IF NOT EXISTS idx_started_at ON execution_states(started_at);
        """

        await asyncio.get_event_loop().run_in_executor(
            self._executor, self._conn.executescript, schema
        )

    async def create_execution(
        self,
        execution_id: str,
        diagram_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> ExecutionState:
        now = datetime.now().isoformat()
        state = ExecutionState(
            id=ExecutionID(execution_id),
            status=ExecutionStatus.STARTED,
            diagram_id=DiagramID(diagram_id) if diagram_id else None,
            started_at=now,
            ended_at=None,
            node_states={},
            node_outputs={},
            token_usage=TokenUsage(input=0, output=0, cached=None, total=0),
            error=None,
            variables=variables or {},
            is_active=True,
        )

        await self.save_state(state)
        return state

    async def save_state(self, state: ExecutionState):
        """Save execution state to database."""
        async with self._lock:
            # Convert node_states and node_outputs to JSON-serializable format
            node_states_dict = {}
            for node_id, node_state in state.node_states.items():
                if hasattr(node_state, "model_dump"):
                    node_states_dict[node_id] = node_state.model_dump()
                elif hasattr(node_state, "dict"):  # Pydantic v1 compatibility
                    node_states_dict[node_id] = node_state.dict()
                elif isinstance(node_state, dict):
                    node_states_dict[node_id] = node_state
                else:
                    # Fallback: convert to dict manually
                    node_states_dict[node_id] = {
                        "status": node_state.status.value if hasattr(node_state.status, 'value') else str(node_state.status),
                        "started_at": node_state.started_at,
                        "ended_at": node_state.ended_at,
                        "error": node_state.error,
                        "skip_reason": getattr(node_state, 'skip_reason', None),
                        "token_usage": node_state.token_usage.model_dump() if hasattr(node_state, 'token_usage') and node_state.token_usage and hasattr(node_state.token_usage, "model_dump") else None
                    }

            node_outputs_dict = {}
            for node_id, node_output in state.node_outputs.items():
                if hasattr(node_output, "model_dump"):
                    node_outputs_dict[node_id] = node_output.model_dump()
                elif hasattr(node_output, "dict"):  # Pydantic v1 compatibility
                    node_outputs_dict[node_id] = node_output.dict()
                elif isinstance(node_output, dict):
                    node_outputs_dict[node_id] = node_output
                else:
                    # Fallback: convert to dict manually
                    node_outputs_dict[node_id] = {
                        "value": node_output.value,
                        "metadata": node_output.metadata if hasattr(node_output, "metadata") else {}
                    }

            await self._execute(
                """
                INSERT OR REPLACE INTO execution_states 
                (execution_id, status, diagram_id, started_at, ended_at,
                 node_states, node_outputs, token_usage, error, variables)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.id,
                    state.status.value
                    if isinstance(state.status, ExecutionStatus)
                    else state.status,
                    state.diagram_id,
                    state.started_at,
                    state.ended_at,
                    json.dumps(node_states_dict),
                    json.dumps(node_outputs_dict),
                    json.dumps(
                        state.token_usage.model_dump() if state.token_usage else {}
                    ),
                    state.error,
                    json.dumps(state.variables),
                ),
            )

    async def get_state(self, execution_id: str) -> Optional[ExecutionState]:
        """Get execution state by ID."""
        cursor = await self._execute(
            """
            SELECT execution_id, status, diagram_id, started_at, ended_at,
                   node_states, node_outputs, token_usage, error, variables
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

        # Parse JSON fields
        node_states_dict = json.loads(row[5])
        node_outputs_dict = json.loads(row[6])
        token_usage_dict = json.loads(row[7])

        # Convert dicts back to model instances
        node_states = {
            node_id: NodeState(**state_data)
            for node_id, state_data in node_states_dict.items()
        }
        node_outputs = {
            node_id: NodeOutput(**output_data)
            for node_id, output_data in node_outputs_dict.items()
        }

        return ExecutionState(
            id=ExecutionID(row[0]),
            status=ExecutionStatus(row[1]),
            diagram_id=DiagramID(row[2]) if row[2] else None,
            started_at=row[3],
            ended_at=row[4],
            node_states=node_states,
            node_outputs=node_outputs,
            token_usage=TokenUsage(**token_usage_dict)
            if token_usage_dict
            else TokenUsage(input=0, output=0, cached=None),
            error=row[8],
            variables=json.loads(row[9]),
        )

    async def update_status(
        self, execution_id: str, status: ExecutionStatus, error: Optional[str] = None
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
        output: NodeOutput
    ) -> None:
        """Store output, using references for large data."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        # For PersonJob outputs with conversation history
        if output.metadata and output.metadata.get("_type") == "personjob_output":
            # Store conversation in message store
            conversation = output.metadata.get("conversation_history", [])
            if conversation and self.message_store:
                message_ref = await self.message_store.store_message(
                    execution_id=execution_id,
                    node_id=node_id,
                    content={"conversation": conversation},
                    person_id=output.metadata.get("person_id"),
                    token_count=output.metadata.get("token_count")
                )
                # Replace conversation with reference
                output.metadata["conversation_ref"] = message_ref
                output.metadata.pop("conversation_history", None)

        # Store the output with reference
        state.node_outputs[node_id] = output
        await self.save_state(state)

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: NodeExecutionStatus,
        output: Optional[NodeOutput] = None,
        error: Optional[str] = None,
        skip_reason: Optional[str] = None,
    ):
        """Update node execution status."""
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
                skip_reason=None,
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

        # Update error or skip reason
        if error:
            state.node_states[node_id].error = error
        if skip_reason:
            state.node_states[node_id].skip_reason = skip_reason

        # Store output if completed
        if status == NodeExecutionStatus.COMPLETED and output is not None:
            state.node_outputs[node_id] = output
            if output.metadata and "tokenUsage" in output.metadata:
                token_usage_data = output.metadata["tokenUsage"]
                if isinstance(token_usage_data, dict):
                    state.node_states[node_id].token_usage = TokenUsage(
                        **token_usage_data
                    )

        await self.save_state(state)

    async def update_variables(self, execution_id: str, variables: Dict[str, Any]):
        """Update execution variables."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        state.variables.update(variables)
        await self.save_state(state)

    async def update_token_usage(self, execution_id: str, tokens: TokenUsage):
        """Update token usage statistics."""
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
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List recent executions with metadata."""
        cursor = await self._execute(
            """
            SELECT execution_id, status, started_at, ended_at, node_states, diagram_id
            FROM execution_states
            ORDER BY started_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

        rows = await asyncio.get_event_loop().run_in_executor(
            self._executor, cursor.fetchall
        )

        executions = []
        for row in rows:
            node_states = json.loads(row[4]) if row[4] else {}
            executions.append(
                {
                    "execution_id": row[0],
                    "status": row[1],
                    "started_at": row[2],
                    "ended_at": row[3],
                    "total_nodes": len(node_states),
                    "diagram_id": row[5],
                }
            )

        return executions

    async def cleanup_old_states(self, days: int = 7):
        """Remove states older than specified days."""
        cutoff_date = datetime.now()
        cutoff_date = cutoff_date.replace(microsecond=0)
        cutoff_iso = (cutoff_date - timedelta(days=days)).isoformat()

        await self._execute(
            "DELETE FROM execution_states WHERE started_at < ?",
            (cutoff_iso,),
        )

        await self._execute("VACUUM")


state_store = StateRegistry()
