"""Simple state tracking for executions using SQLite."""
import asyncio
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class StoredExecutionState:
    """Current state of an execution stored in SQLite."""
    execution_id: str
    status: str  # started, completed, failed, aborted, paused
    diagram: Dict[str, Any]
    options: Dict[str, Any]
    node_outputs: Dict[str, Any]
    node_statuses: Dict[str, str]
    paused_nodes: List[str]
    skipped_nodes: List[str]
    variables: Dict[str, Any]
    total_tokens: Dict[str, int]
    start_time: float
    end_time: Optional[float]
    error: Optional[str]
    last_updated: float
    current_node_id: Optional[str] = None
    interactive_prompt: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "diagram": self.diagram,
            "options": self.options,
            "node_outputs": self.node_outputs,
            "node_statuses": self.node_statuses,
            "paused_nodes": self.paused_nodes,
            "skipped_nodes": self.skipped_nodes,
            "variables": self.variables,
            "total_tokens": self.total_tokens,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error": self.error,
            "last_updated": self.last_updated,
            "current_node_id": self.current_node_id,
            "interactive_prompt": self.interactive_prompt
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredExecutionState':
        """Create from dictionary."""
        return cls(**data)


class SimpleStateStore:
    """Simple state storage for execution tracking."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("STATE_STORE_PATH", "dipeo_state.db")
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize database connection and schema."""
        await self._connect()
        await self._init_schema()
        
    async def cleanup(self):
        """Close database connection."""
        if self._conn:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
            
    async def _connect(self):
        """Create database connection."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection with proper settings
        self._conn = await asyncio.to_thread(
            sqlite3.connect,
            self.db_path,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode
        )
        
        # Enable WAL mode for better concurrency
        await asyncio.to_thread(
            self._conn.execute,
            "PRAGMA journal_mode=WAL"
        )
        
    async def _init_schema(self):
        """Initialize database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS execution_states (
            execution_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            diagram TEXT NOT NULL,
            options TEXT NOT NULL,
            node_outputs TEXT NOT NULL,
            node_statuses TEXT NOT NULL,
            paused_nodes TEXT NOT NULL,
            skipped_nodes TEXT NOT NULL,
            variables TEXT NOT NULL,
            total_tokens TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL,
            error TEXT,
            last_updated REAL NOT NULL,
            current_node_id TEXT,
            interactive_prompt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_status ON execution_states(status);
        CREATE INDEX IF NOT EXISTS idx_start_time ON execution_states(start_time);
        CREATE INDEX IF NOT EXISTS idx_last_updated ON execution_states(last_updated);
        """
        
        await asyncio.to_thread(self._conn.executescript, schema)
        
    async def create_execution(self, execution_id: str, diagram: Dict[str, Any], 
                            options: Dict[str, Any]) -> StoredExecutionState:
        """Create a new execution state."""
        state = StoredExecutionState(
            execution_id=execution_id,
            status="started",
            diagram=diagram,
            options=options,
            node_outputs={},
            node_statuses={},
            paused_nodes=[],
            skipped_nodes=[],
            variables={},
            total_tokens={"input": 0, "output": 0, "cached": 0},
            start_time=datetime.now().timestamp(),
            end_time=None,
            error=None,
            last_updated=datetime.now().timestamp()
        )
        
        await self._save_state(state)
        return state
        
    async def _save_state(self, state: StoredExecutionState):
        """Save execution state to database."""
        async with self._lock:
            await asyncio.to_thread(
                self._conn.execute,
                """
                INSERT OR REPLACE INTO execution_states 
                (execution_id, status, diagram, options, node_outputs, node_statuses,
                 paused_nodes, skipped_nodes, variables, total_tokens, start_time,
                 end_time, error, last_updated, current_node_id, interactive_prompt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.execution_id,
                    state.status,
                    json.dumps(state.diagram),
                    json.dumps(state.options),
                    json.dumps(state.node_outputs),
                    json.dumps(state.node_statuses),
                    json.dumps(state.paused_nodes),
                    json.dumps(state.skipped_nodes),
                    json.dumps(state.variables),
                    json.dumps(state.total_tokens),
                    state.start_time,
                    state.end_time,
                    state.error,
                    datetime.now().timestamp(),
                    state.current_node_id,
                    json.dumps(state.interactive_prompt) if state.interactive_prompt else None
                )
            )
            
    async def get_state(self, execution_id: str) -> Optional[StoredExecutionState]:
        """Get execution state by ID."""
        cursor = await asyncio.to_thread(
            self._conn.execute,
            """
            SELECT execution_id, status, diagram, options, node_outputs, node_statuses,
                   paused_nodes, skipped_nodes, variables, total_tokens, start_time,
                   end_time, error, last_updated, current_node_id, interactive_prompt
            FROM execution_states
            WHERE execution_id = ?
            """,
            (execution_id,)
        )
        
        row = await asyncio.to_thread(cursor.fetchone)
        if not row:
            return None
            
        return StoredExecutionState(
            execution_id=row[0],
            status=row[1],
            diagram=json.loads(row[2]),
            options=json.loads(row[3]),
            node_outputs=json.loads(row[4]),
            node_statuses=json.loads(row[5]),
            paused_nodes=json.loads(row[6]),
            skipped_nodes=json.loads(row[7]),
            variables=json.loads(row[8]),
            total_tokens=json.loads(row[9]),
            start_time=row[10],
            end_time=row[11],
            error=row[12],
            last_updated=row[13],
            current_node_id=row[14],
            interactive_prompt=json.loads(row[15]) if row[15] else None
        )
        
    async def update_status(self, execution_id: str, status: str, error: Optional[str] = None):
        """Update execution status."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
            
        state.status = status
        state.error = error
        if status in ["completed", "failed", "aborted"]:
            state.end_time = datetime.now().timestamp()
            
        await self._save_state(state)
        
    async def update_node_status(self, execution_id: str, node_id: str, status: str, 
                               output: Optional[Any] = None):
        """Update node execution status."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
            
        state.node_statuses[node_id] = status
        state.current_node_id = node_id if status == "started" else None
        
        if status == "completed" and output is not None:
            state.node_outputs[node_id] = output
        elif status == "skipped":
            if node_id not in state.skipped_nodes:
                state.skipped_nodes.append(node_id)
        elif status == "paused":
            if node_id not in state.paused_nodes:
                state.paused_nodes.append(node_id)
        elif status == "resumed":
            if node_id in state.paused_nodes:
                state.paused_nodes.remove(node_id)
                
        await self._save_state(state)
        
    async def set_interactive_prompt(self, execution_id: str, node_id: str, prompt: str):
        """Set interactive prompt for user response."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
            
        state.interactive_prompt = {
            "node_id": node_id,
            "prompt": prompt,
            "timestamp": datetime.now().timestamp()
        }
        state.status = "paused"
        
        await self._save_state(state)
        
    async def clear_interactive_prompt(self, execution_id: str):
        """Clear interactive prompt after response."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
            
        state.interactive_prompt = None
        if state.status == "paused":
            state.status = "started"
            
        await self._save_state(state)
        
    async def update_variables(self, execution_id: str, variables: Dict[str, Any]):
        """Update execution variables."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
            
        state.variables.update(variables)
        await self._save_state(state)
        
    async def update_token_usage(self, execution_id: str, tokens: Dict[str, int]):
        """Update token usage statistics."""
        state = await self.get_state(execution_id)
        if not state:
            raise ValueError(f"Execution {execution_id} not found")
            
        state.total_tokens["input"] += tokens.get("input", 0)
        state.total_tokens["output"] += tokens.get("output", 0)
        state.total_tokens["cached"] += tokens.get("cached", 0)
        
        await self._save_state(state)
        
    async def list_executions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List recent executions with metadata."""
        cursor = await asyncio.to_thread(
            self._conn.execute,
            """
            SELECT execution_id, status, start_time, end_time, last_updated,
                   json_extract(node_statuses, '$') as node_statuses
            FROM execution_states
            ORDER BY start_time DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        
        rows = await asyncio.to_thread(cursor.fetchall)
        
        executions = []
        for row in rows:
            node_statuses = json.loads(row[5]) if row[5] else {}
            executions.append({
                "execution_id": row[0],
                "status": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "last_updated": row[4],
                "total_nodes": len(node_statuses)
            })
            
        return executions
        
    async def cleanup_old_states(self, days: int = 7):
        """Remove states older than specified days."""
        cutoff_timestamp = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        await asyncio.to_thread(
            self._conn.execute,
            "DELETE FROM execution_states WHERE start_time < ?",
            (cutoff_timestamp,)
        )
        
        # Vacuum to reclaim space
        await asyncio.to_thread(self._conn.execute, "VACUUM")


# Global state store instance
state_store = SimpleStateStore()