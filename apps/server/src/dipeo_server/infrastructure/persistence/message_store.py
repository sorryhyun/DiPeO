"""Message store for handling message persistence."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite


class MessageStore:
    """Stores actual message content, returns only references."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def initialize(self):
        """Create tables for message storage."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    person_id TEXT,
                    content TEXT NOT NULL,
                    token_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_execution ON messages(execution_id);
                CREATE INDEX IF NOT EXISTS idx_node ON messages(node_id);
            ''')
            await db.commit()

    async def store_message(
        self,
        execution_id: str,
        node_id: str,
        content: Dict[str, Any],
        person_id: Optional[str] = None,
        token_count: Optional[int] = None
    ) -> str:
        """Store message and return reference ID."""
        message_id = f"{execution_id}:{node_id}:{datetime.utcnow().timestamp()}"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT INTO messages 
                   (id, execution_id, node_id, person_id, content, token_count)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    message_id,
                    execution_id,
                    node_id,
                    person_id,
                    json.dumps(content),
                    token_count
                )
            )
            await db.commit()

        return message_id

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve message by reference ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT content FROM messages WHERE id = ?', 
                (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return json.loads(row[0]) if row else None

    async def get_conversation_messages(
        self, 
        execution_id: str, 
        person_id: str
    ) -> List[Dict[str, Any]]:
        """Get all messages for a person in an execution."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                '''SELECT id, content, token_count, created_at 
                   FROM messages 
                   WHERE execution_id = ? AND person_id = ?
                   ORDER BY created_at''',
                (execution_id, person_id)
            ) as cursor:
                messages = []
                async for row in cursor:
                    messages.append({
                        'id': row[0],
                        'content': json.loads(row[1]),
                        'token_count': row[2],
                        'timestamp': row[3]
                    })
                return messages
