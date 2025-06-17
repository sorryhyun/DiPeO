from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from pathlib import Path
import json
import redis
import os


@dataclass
class Message:
    """Enhanced message with metadata."""
    id: str
    role: str
    content: str
    timestamp: datetime
    sender_person_id: Optional[str] = None
    execution_id: Optional[str] = None
    node_id: Optional[str] = None
    node_label: Optional[str] = None
    token_count: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "sender_person_id": self.sender_person_id,
            "execution_id": self.execution_id,
            "node_id": self.node_id,
            "node_label": self.node_label,
            "token_count": self.token_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens
        }
    
    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON string."""
        data = json.loads(json_str)
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sender_person_id=data.get("sender_person_id"),
            execution_id=data.get("execution_id"),
            node_id=data.get("node_id"),
            node_label=data.get("node_label"),
            token_count=data.get("token_count"),
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            cached_tokens=data.get("cached_tokens")
        )


@dataclass
class PersonMemory:
    """Memory state for a specific person."""
    person_id: str
    messages: List[Message] = field(default_factory=list)
    forgotten_message_ids: set[str] = field(default_factory=set)
    last_execution_id: Optional[str] = None
    MAX_MESSAGES = 1000

    def add_message(self, message: Message) -> None:
        """Add a message to memory."""
        self.messages.append(message)
        if len(self.messages) > self.MAX_MESSAGES:
            messages_to_forget = len(self.messages) - self.MAX_MESSAGES
            for msg in self.messages[:messages_to_forget]:
                self.forgotten_message_ids.add(msg.id)

    def forget_messages_from_execution(self, execution_id: str) -> None:
        """Mark messages from a specific execution as forgotten for this person."""
        for message in self.messages:
            if message.execution_id == execution_id:
                self.forgotten_message_ids.add(message.id)

    def forget_own_messages(self) -> None:
        """Mark all messages sent BY this person as forgotten (but keep messages TO this person)."""
        for message in self.messages:
            if message.sender_person_id == self.person_id:
                self.forgotten_message_ids.add(message.id)

    def forget_own_messages_from_execution(self, execution_id: str) -> None:
        """Mark messages sent BY this person from a specific execution as forgotten."""
        for message in self.messages:
            if message.execution_id == execution_id and message.sender_person_id == self.person_id:
                self.forgotten_message_ids.add(message.id)

    def get_visible_messages(self, current_person_id: str) -> List[Dict[str, Any]]:
        """Get messages visible to this person, with roles adjusted based on perspective."""
        visible_messages = []

        for message in self.messages:
            if message.id in self.forgotten_message_ids:
                continue

            role = "assistant" if message.sender_person_id == current_person_id else "user"
            
            # Add speaker label for user messages to clarify who is speaking
            if role == "user" and message.node_label:
                content = f"[{message.node_label}]: {message.content}"
            else:
                content = message.content

            visible_messages.append({
                "role": role,
                "content": content
            })

        return visible_messages


class MemoryService:
    """Service for managing conversation memory across persons and jobs."""

    def __init__(self, redis_url: Optional[str] = None):
        # Fallback to in-memory storage if Redis not available
        self.redis_client = None
        if redis_url or os.getenv('REDIS_URL'):
            try:
                self.redis_client = redis.Redis.from_url(
                    redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379'),
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
            except (redis.ConnectionError, redis.RedisError):
                self.redis_client = None
        
        # Fallback in-memory storage
        self.person_memories: Dict[str, PersonMemory] = {}
        self.all_messages: Dict[str, Message] = {}
        self.execution_metadata: Dict[str, Dict[str, Any]] = {}
    
    def _store_message_redis(self, message: Message) -> None:
        """Store message in Redis with TTL."""
        if self.redis_client:
            try:
                # Store with 24 hour TTL for automatic cleanup
                self.redis_client.setex(
                    f"msg:{message.id}",
                    86400,
                    message.to_json()
                )
            except redis.RedisError:
                # Fallback to in-memory if Redis fails
                self.all_messages[message.id] = message
        else:
            self.all_messages[message.id] = message
    
    def _get_message_redis(self, message_id: str) -> Optional[Message]:
        """Get message from Redis or fallback storage."""
        if self.redis_client:
            try:
                json_str = self.redis_client.get(f"msg:{message_id}")
                if json_str:
                    return Message.from_json(json_str)
            except redis.RedisError:
                pass
        
        return self.all_messages.get(message_id)

    def get_or_create_person_memory(self, person_id: str) -> PersonMemory:
        """Get or create memory for a person."""
        if person_id not in self.person_memories:
            self.person_memories[person_id] = PersonMemory(person_id=person_id)
        return self.person_memories[person_id]

    def add_message_to_conversation(self,
        content: str,
        sender_person_id: str,
        execution_id: str,
        participant_person_ids: List[str],
        role: str = "assistant",
        node_id: Optional[str] = None,
        node_label: Optional[str] = None,
        token_count: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None) -> Message:
        """Create and add message to conversation."""
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            sender_person_id=sender_person_id,
            execution_id=execution_id,
            node_id=node_id,
            node_label=node_label,
            token_count=token_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens
        )

        self._store_message_redis(message)

        for person_id in participant_person_ids:
            person_memory = self.get_or_create_person_memory(person_id)
            person_memory.add_message(message)

        if execution_id not in self.execution_metadata:
            self.execution_metadata[execution_id] = {
                "start_time": datetime.now(),
                "message_count": 0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0
            }

        self.execution_metadata[execution_id]["message_count"] += 1
        if token_count:
            self.execution_metadata[execution_id]["total_tokens"] += token_count
        if input_tokens:
            self.execution_metadata[execution_id]["input_tokens"] += input_tokens
        if output_tokens:
            self.execution_metadata[execution_id]["output_tokens"] += output_tokens
        if cached_tokens:
            self.execution_metadata[execution_id]["cached_tokens"] += cached_tokens

        return message

    def forget_for_person(self, person_id: str, execution_id: Optional[str] = None) -> None:
        """Make a person forget messages."""
        person_memory = self.get_or_create_person_memory(person_id)

        if execution_id:
            person_memory.forget_messages_from_execution(execution_id)
        else:
            for message in person_memory.messages:
                person_memory.forgotten_message_ids.add(message.id)

    def forget_own_messages_for_person(self, person_id: str, execution_id: Optional[str] = None) -> None:
        """Make a person forget only their own messages (selective forgetting)."""
        person_memory = self.get_or_create_person_memory(person_id)

        if execution_id:
            person_memory.forget_own_messages_from_execution(execution_id)
        else:
            person_memory.forget_own_messages()

    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        """Get the conversation history as visible to a specific person."""
        person_memory = self.get_or_create_person_memory(person_id)
        return person_memory.get_visible_messages(person_id)

    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str:
        """Save the current conversation state to a JSONL log file."""
        from ..shared.utils.app_context import get_file_service
        
        file_service = get_file_service()
        
        log_lines = []
        
        metadata = self.execution_metadata.get(execution_id, {})
        metadata_record = {
            "type": "execution_metadata",
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "start_time": metadata.get('start_time').isoformat() if metadata.get('start_time') else None,
            "message_count": metadata.get('message_count', 0),
            "total_tokens": metadata.get('total_tokens', 0),
            "input_tokens": metadata.get('input_tokens', 0),
            "output_tokens": metadata.get('output_tokens', 0),
            "cached_tokens": metadata.get('cached_tokens', 0)
        }
        log_lines.append(json.dumps(metadata_record, ensure_ascii=False))
            
        for person_id, memory in self.person_memories.items():
            person_stats = {
                "type": "person_stats",
                "person_id": person_id,
                "execution_id": execution_id,
                "total_messages": len(memory.messages),
                "forgotten_messages": len(memory.forgotten_message_ids),
                "visible_messages": len(memory.messages) - len(memory.forgotten_message_ids),
                "forgotten_message_ids": list(memory.forgotten_message_ids)
            }
            log_lines.append(json.dumps(person_stats, ensure_ascii=False))
            
        all_execution_messages = [
            msg for msg in self.all_messages.values() 
            if msg.execution_id == execution_id
        ]
        
        all_execution_messages.sort(key=lambda m: m.timestamp)
        
        for msg in all_execution_messages:
            is_forgotten = any(
                msg.id in memory.forgotten_message_ids 
                for memory in self.person_memories.values()
            )
            
            message_record = {
                "type": "message",
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sender_person_id": msg.sender_person_id,
                "execution_id": msg.execution_id,
                "node_id": msg.node_id,
                "node_label": msg.node_label,
                "token_count": msg.token_count,
                "input_tokens": msg.input_tokens,
                "output_tokens": msg.output_tokens,
                "cached_tokens": msg.cached_tokens,
                "is_forgotten": is_forgotten
            }
            log_lines.append(json.dumps(message_record, ensure_ascii=False))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}_{execution_id[:8]}.jsonl"
        
        content = "\n".join(log_lines)
        
        relative_path = await file_service.write(
            path=filename,
            content=content,
            relative_to="logs",
            format="text"
        )
        
        return relative_path