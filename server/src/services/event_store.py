"""Event-sourced execution state persistence using SQLite."""
import asyncio
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncIterator
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of execution events."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_ABORTED = "execution_aborted"
    
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_SKIPPED = "node_skipped"
    NODE_PAUSED = "node_paused"
    NODE_RESUMED = "node_resumed"
    
    INTERACTIVE_PROMPT = "interactive_prompt"
    INTERACTIVE_RESPONSE = "interactive_response"
    
    VARIABLE_SET = "variable_set"
    OUTPUT_PRODUCED = "output_produced"
    TOKEN_USAGE = "token_usage"


@dataclass
class ExecutionEvent:
    """Represents a single execution event."""
    execution_id: str
    sequence: int
    event_type: EventType
    node_id: Optional[str]
    data: Dict[str, Any]
    timestamp: float
    

@dataclass
class ExecutionState:
    """Current state of an execution rebuilt from events."""
    execution_id: str
    status: str  # started, completed, failed, aborted
    diagram: Dict[str, Any]
    options: Dict[str, Any]
    node_outputs: Dict[str, Any]
    node_statuses: Dict[str, str]
    paused_nodes: set
    skipped_nodes: set
    variables: Dict[str, Any]
    total_tokens: Dict[str, int]
    start_time: float
    end_time: Optional[float]
    error: Optional[str]
    
    @classmethod
    def from_events(cls, events: List[ExecutionEvent]) -> 'ExecutionState':
        """Rebuild execution state from a list of events."""
        if not events:
            raise ValueError("Cannot rebuild state from empty event list")
            
        # Start with initial state
        first_event = events[0]
        if first_event.event_type != EventType.EXECUTION_STARTED:
            raise ValueError("First event must be EXECUTION_STARTED")
            
        state = cls(
            execution_id=first_event.execution_id,
            status="started",
            diagram=first_event.data.get("diagram", {}),
            options=first_event.data.get("options", {}),
            node_outputs={},
            node_statuses={},
            paused_nodes=set(),
            skipped_nodes=set(),
            variables={},
            total_tokens={"input": 0, "output": 0, "cached": 0},
            start_time=first_event.timestamp,
            end_time=None,
            error=None
        )
        
        # Apply each event to update state
        for event in events[1:]:
            state._apply_event(event)
            
        return state
        
    def _apply_event(self, event: ExecutionEvent):
        """Apply a single event to update the state."""
        match event.event_type:
            case EventType.EXECUTION_COMPLETED:
                self.status = "completed"
                self.end_time = event.timestamp
                
            case EventType.EXECUTION_FAILED:
                self.status = "failed"
                self.error = event.data.get("error")
                self.end_time = event.timestamp
                
            case EventType.EXECUTION_ABORTED:
                self.status = "aborted"
                self.end_time = event.timestamp
                
            case EventType.NODE_STARTED:
                self.node_statuses[event.node_id] = "started"
                
            case EventType.NODE_COMPLETED:
                self.node_statuses[event.node_id] = "completed"
                if "output" in event.data:
                    self.node_outputs[event.node_id] = event.data["output"]
                    
            case EventType.NODE_FAILED:
                self.node_statuses[event.node_id] = "failed"
                
            case EventType.NODE_SKIPPED:
                self.node_statuses[event.node_id] = "skipped"
                self.skipped_nodes.add(event.node_id)
                
            case EventType.NODE_PAUSED:
                self.paused_nodes.add(event.node_id)
                
            case EventType.NODE_RESUMED:
                self.paused_nodes.discard(event.node_id)
                
            case EventType.VARIABLE_SET:
                self.variables.update(event.data.get("variables", {}))
                
            case EventType.OUTPUT_PRODUCED:
                node_id = event.node_id
                if node_id:
                    self.node_outputs[node_id] = event.data.get("output")
                    
            case EventType.TOKEN_USAGE:
                tokens = event.data.get("tokens", {})
                self.total_tokens["input"] += tokens.get("input", 0)
                self.total_tokens["output"] += tokens.get("output", 0)
                self.total_tokens["cached"] += tokens.get("cached", 0)


class EventStore:
    """Append-only event store for execution state."""
    
    def __init__(self, db_path: Optional[str] = None, redis_url: Optional[str] = None):
        self.db_path = db_path or os.getenv("EVENT_STORE_PATH", "dipeo_events.db")
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._conn: Optional[sqlite3.Connection] = None
        self._redis_client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        self._sequence_counters: Dict[str, int] = {}
        
    async def initialize(self):
        """Initialize database connection and schema."""
        await self._connect()
        await self._init_schema()
        await self._connect_redis()
        
    async def cleanup(self):
        """Close database and Redis connections."""
        if self._conn:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            
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
        
    async def _connect_redis(self):
        """Connect to Redis for event publishing."""
        try:
            self._redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._redis_client.ping()
            logger.info("Connected to Redis for event publishing")
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.warning(f"Failed to connect to Redis: {e}. Event publishing will be disabled.")
            self._redis_client = None
        
    async def _init_schema(self):
        """Initialize database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            node_id TEXT,
            data TEXT NOT NULL,
            timestamp REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(execution_id, sequence)
        );
        
        CREATE INDEX IF NOT EXISTS idx_execution_id ON events(execution_id);
        CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);
        
        CREATE TABLE IF NOT EXISTS execution_metadata (
            execution_id TEXT PRIMARY KEY,
            diagram_hash TEXT,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        await asyncio.to_thread(self._conn.executescript, schema)
        
    async def append(self, event: ExecutionEvent) -> int:
        """Append an event to the store."""
        async with self._lock:
            # Get next sequence number
            if event.execution_id not in self._sequence_counters:
                # Load max sequence from database
                cursor = await asyncio.to_thread(
                    self._conn.execute,
                    "SELECT MAX(sequence) FROM events WHERE execution_id = ?",
                    (event.execution_id,)
                )
                result = await asyncio.to_thread(cursor.fetchone)
                self._sequence_counters[event.execution_id] = (result[0] or -1) + 1
            
            event.sequence = self._sequence_counters[event.execution_id]
            self._sequence_counters[event.execution_id] += 1
            
            # Insert event
            await asyncio.to_thread(
                self._conn.execute,
                """
                INSERT INTO events (execution_id, sequence, event_type, node_id, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.execution_id,
                    event.sequence,
                    event.event_type.value,
                    event.node_id,
                    json.dumps(event.data),
                    event.timestamp
                )
            )
            
            # Publish event to Redis for real-time subscriptions
            if self._redis_client:
                try:
                    # Publish to execution-specific channel
                    channel = f"execution:{event.execution_id}"
                    event_dict = {
                        "execution_id": event.execution_id,
                        "sequence": event.sequence,
                        "event_type": event.event_type.value,
                        "node_id": event.node_id,
                        "data": event.data,
                        "timestamp": event.timestamp
                    }
                    await self._redis_client.publish(channel, json.dumps(event_dict))
                    
                    # Also publish to a general events channel for monitoring
                    await self._redis_client.publish("events:all", json.dumps(event_dict))
                    
                    logger.debug(f"Published event {event.event_type} to Redis channel {channel}")
                except Exception as e:
                    logger.error(f"Failed to publish event to Redis: {e}")
                    # Don't fail the append operation if Redis publish fails
            
            return event.sequence
            
    async def get_events(self, execution_id: str) -> List[ExecutionEvent]:
        """Get all events for an execution."""
        cursor = await asyncio.to_thread(
            self._conn.execute,
            """
            SELECT execution_id, sequence, event_type, node_id, data, timestamp
            FROM events
            WHERE execution_id = ?
            ORDER BY sequence
            """,
            (execution_id,)
        )
        
        rows = await asyncio.to_thread(cursor.fetchall)
        
        events = []
        for row in rows:
            events.append(ExecutionEvent(
                execution_id=row[0],
                sequence=row[1],
                event_type=EventType(row[2]),
                node_id=row[3],
                data=json.loads(row[4]),
                timestamp=row[5]
            ))
            
        return events
        
    async def replay(self, execution_id: str) -> Optional[ExecutionState]:
        """Rebuild execution state by replaying events."""
        events = await self.get_events(execution_id)
        if not events:
            return None
            
        return ExecutionState.from_events(events)
        
    async def list_executions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List recent executions with metadata."""
        cursor = await asyncio.to_thread(
            self._conn.execute,
            """
            SELECT 
                e1.execution_id,
                e1.timestamp as start_time,
                e2.timestamp as end_time,
                e2.event_type as final_status,
                COUNT(DISTINCT e.node_id) as total_nodes
            FROM events e1
            LEFT JOIN events e ON e.execution_id = e1.execution_id
            LEFT JOIN events e2 ON e2.execution_id = e1.execution_id 
                AND e2.event_type IN ('execution_completed', 'execution_failed', 'execution_aborted')
            WHERE e1.event_type = 'execution_started'
            GROUP BY e1.execution_id
            ORDER BY e1.timestamp DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        
        rows = await asyncio.to_thread(cursor.fetchall)
        
        executions = []
        for row in rows:
            executions.append({
                "execution_id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "status": row[3].replace("execution_", "") if row[3] else "running",
                "total_nodes": row[4]
            })
            
        return executions
        
    async def cleanup_old_events(self, days: int = 7):
        """Remove events older than specified days."""
        cutoff_timestamp = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        await asyncio.to_thread(
            self._conn.execute,
            "DELETE FROM events WHERE timestamp < ?",
            (cutoff_timestamp,)
        )
        
        # Vacuum to reclaim space
        await asyncio.to_thread(self._conn.execute, "VACUUM")


# Global event store instance
event_store = EventStore()