"""
Memory manager for handling conversation history and context.
Separates memory concerns from execution logic.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

from ...services.memory_service import MemoryService
from ...constants import ContentType
from ..core.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonMemory:
    """Memory state for a specific person."""
    person_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class MemoryManager:
    """Manages memory and conversation history for person nodes."""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self._person_memories: Dict[str, PersonMemory] = {}
        self._conversation_cache: Dict[str, List[Dict]] = {}
    
    def initialize_person(self, person_id: str, initial_context: Optional[Dict] = None):
        """Initialize memory for a person."""
        if person_id not in self._person_memories:
            self._person_memories[person_id] = PersonMemory(
                person_id=person_id,
                context=initial_context or {}
            )
            logger.info(f"Initialized memory for person: {person_id}")
    
    def add_message(self, person_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to a person's conversation history."""
        self.initialize_person(person_id)
        
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self._person_memories[person_id].messages.append(message)
        self._person_memories[person_id].last_updated = datetime.now()
        
        # Invalidate cache
        self._conversation_cache.pop(person_id, None)
        
        # Sync with memory service
        self.memory_service.add_message(person_id, role, content)
        
        logger.debug(f"Added {role} message to person {person_id}")
    
    def get_conversation_history(self, person_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history for a person."""
        # Check cache first
        if person_id in self._conversation_cache and not limit:
            return self._conversation_cache[person_id]
        
        # Get from memory service
        history = self.memory_service.get_conversation_history(person_id)
        
        # Apply limit if specified
        if limit and limit > 0:
            history = history[-limit:]
        
        # Cache if no limit
        if not limit:
            self._conversation_cache[person_id] = history
        
        return history
    
    def clear_person_memory(self, person_id: str):
        """Clear all memory for a person."""
        self._person_memories.pop(person_id, None)
        self._conversation_cache.pop(person_id, None)
        self.memory_service.clear_person_memory(person_id)
        logger.info(f"Cleared memory for person: {person_id}")
    
    def update_person_context(self, person_id: str, context_updates: Dict[str, Any]):
        """Update the context for a person."""
        self.initialize_person(person_id)
        
        memory = self._person_memories[person_id]
        memory.context.update(context_updates)
        memory.last_updated = datetime.now()
        
        logger.debug(f"Updated context for person {person_id}: {list(context_updates.keys())}")
    
    def get_person_context(self, person_id: str) -> Dict[str, Any]:
        """Get the current context for a person."""
        if person_id in self._person_memories:
            return self._person_memories[person_id].context.copy()
        return {}
    
    def extract_conversation_state(self, node_output: Any) -> Optional[List[Dict]]:
        """Extract conversation state from node output."""
        if isinstance(node_output, dict):
            # Check for conversation_history in metadata
            metadata = node_output.get('metadata', {})
            if 'conversation_history' in metadata:
                return metadata['conversation_history']
            
            # Check for conversation_state in output
            if 'conversation_state' in node_output:
                return node_output['conversation_state']
        
        return None
    
    def format_conversation_for_prompt(self, conversation: List[Dict[str, str]]) -> str:
        """Format conversation history for inclusion in prompts."""
        if not conversation:
            return ""
        
        formatted = []
        for msg in conversation:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def transfer_conversation(self, from_person: str, to_person: str, clean_target: bool = True):
        """Transfer conversation history from one person to another."""
        if clean_target:
            self.clear_person_memory(to_person)
        
        # Get source conversation
        source_history = self.get_conversation_history(from_person)
        
        # Transfer to target
        for msg in source_history:
            self.add_message(
                to_person,
                msg.get('role', 'user'),
                msg.get('content', ''),
                {'transferred_from': from_person}
            )
        
        logger.info(f"Transferred {len(source_history)} messages from {from_person} to {to_person}")
    
    def merge_conversations(self, person_ids: List[str], target_person: str):
        """Merge multiple conversation histories into one person."""
        all_messages = []
        
        # Collect all messages with timestamps
        for person_id in person_ids:
            if person_id in self._person_memories:
                memory = self._person_memories[person_id]
                for msg in memory.messages:
                    all_messages.append((msg.timestamp, person_id, msg))
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x[0])
        
        # Clear target and add merged messages
        self.clear_person_memory(target_person)
        
        for timestamp, source_person, msg in all_messages:
            metadata = msg.metadata.copy()
            metadata['merged_from'] = source_person
            self.add_message(
                target_person,
                msg.role,
                msg.content,
                metadata
            )
        
        logger.info(f"Merged {len(all_messages)} messages from {person_ids} into {target_person}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        stats = {
            'total_persons': len(self._person_memories),
            'total_messages': 0,
            'persons': {}
        }
        
        for person_id, memory in self._person_memories.items():
            message_count = len(memory.messages)
            stats['total_messages'] += message_count
            stats['persons'][person_id] = {
                'message_count': message_count,
                'last_updated': memory.last_updated.isoformat(),
                'context_keys': list(memory.context.keys())
            }
        
        return stats
    
    def cleanup_old_memories(self, max_age_hours: int = 24):
        """Clean up memories older than specified hours."""
        current_time = datetime.now()
        cleaned = []
        
        for person_id, memory in list(self._person_memories.items()):
            age_hours = (current_time - memory.last_updated).total_seconds() / 3600
            if age_hours > max_age_hours:
                self.clear_person_memory(person_id)
                cleaned.append(person_id)
        
        if cleaned:
            logger.info(f"Cleaned up old memories for: {cleaned}")
        
        return cleaned