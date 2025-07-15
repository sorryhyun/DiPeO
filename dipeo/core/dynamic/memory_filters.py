"""Memory filter system for managing different views of the global conversation."""

from enum import Enum
from typing import Protocol

from dipeo.models import Message, PersonID


class MemoryView(Enum):
    """Different views/filters for a person's memory of the global conversation."""
    
    # Core views
    ALL_INVOLVED = "all_involved"  # Messages where person is sender or recipient (current default)
    SENT_BY_ME = "sent_by_me"  # Messages I sent
    SENT_TO_ME = "sent_to_me"  # Messages sent to me
    
    # Specialized views
    SYSTEM_AND_ME = "system_and_me"  # System messages and my interactions
    CONVERSATION_PAIRS = "conversation_pairs"  # Messages grouped as request/response pairs
    ALL_MESSAGES = "all_messages"  # All messages in the conversation (for judges/observers)


class MemoryFilter(Protocol):
    """Protocol for memory filters."""
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        """Filter messages based on the person's perspective."""
        ...
    
    def describe(self) -> str:
        """Return a human-readable description of this filter."""
        ...


class AllInvolvedFilter:
    """Filter for messages where person is sender or recipient."""
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [
            msg for msg in messages
            if msg.from_person_id == person_id or msg.to_person_id == person_id
        ]
    
    def describe(self) -> str:
        return "Messages where I am sender or recipient"


class SentByMeFilter:
    """Filter for messages sent by this person."""
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [msg for msg in messages if msg.from_person_id == person_id]
    
    def describe(self) -> str:
        return "Messages I sent"


class SentToMeFilter:
    """Filter for messages sent to this person."""
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [msg for msg in messages if msg.to_person_id == person_id]
    
    def describe(self) -> str:
        return "Messages sent to me"


class SystemAndMeFilter:
    """Filter for system messages and this person's interactions."""
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [
            msg for msg in messages
            if (msg.from_person_id == PersonID("system") and msg.to_person_id == person_id)
            or msg.from_person_id == person_id
        ]
    
    def describe(self) -> str:
        return "System messages to me and my responses"


class ConversationPairsFilter:
    """Filter that groups messages as request/response pairs."""
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        result = []
        
        # Track messages to this person and look for responses
        for i, msg in enumerate(messages):
            if msg.to_person_id == person_id:
                result.append(msg)
                
                # Look for immediate response
                if i + 1 < len(messages) and messages[i + 1].from_person_id == person_id:
                    result.append(messages[i + 1])
            elif msg.from_person_id == person_id and (not result or result[-1].from_person_id != person_id):
                # Include orphaned responses from this person
                result.append(msg)
        
        return result
    
    def describe(self) -> str:
        return "Messages grouped as request/response pairs"


class AllMessagesFilter:
    """Filter that shows all messages in the conversation (for judges/observers)."""
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        # Return all messages unfiltered
        return messages
    
    def describe(self) -> str:
        return "All messages in the conversation"


class MemoryFilterFactory:
    """Factory for creating memory filters."""
    
    _filters = {
        MemoryView.ALL_INVOLVED: AllInvolvedFilter,
        MemoryView.SENT_BY_ME: SentByMeFilter,
        MemoryView.SENT_TO_ME: SentToMeFilter,
        MemoryView.SYSTEM_AND_ME: SystemAndMeFilter,
        MemoryView.CONVERSATION_PAIRS: ConversationPairsFilter,
        MemoryView.ALL_MESSAGES: AllMessagesFilter,
    }
    
    @classmethod
    def create(cls, view: MemoryView, **kwargs) -> MemoryFilter:
        """Create a memory filter for the specified view."""
        filter_class = cls._filters.get(view)
        if not filter_class:
            raise ValueError(f"Unknown memory view: {view}")
        
        return filter_class()


class MemoryLimiter:
    """Applies memory limits while preserving important messages."""
    
    def __init__(self, max_messages: int, preserve_system: bool = True):
        self.max_messages = max_messages
        self.preserve_system = preserve_system
    
    def limit(self, messages: list[Message]) -> list[Message]:
        """Apply memory limit to messages, preserving system messages if configured."""
        if len(messages) <= self.max_messages:
            return messages
        
        if self.preserve_system:
            # Separate system and non-system messages
            system_messages = [
                msg for msg in messages 
                if msg.from_person_id == PersonID("system")
            ]
            non_system_messages = [
                msg for msg in messages 
                if msg.from_person_id != PersonID("system")
            ]
            
            # Calculate how many non-system messages we can keep
            available_slots = self.max_messages - len(system_messages)
            if available_slots <= 0:
                # Only system messages fit
                return system_messages[-self.max_messages:]
            
            # Keep system messages and most recent non-system messages
            return system_messages + non_system_messages[-available_slots:]
        else:
            # Simply keep the most recent messages
            return messages[-self.max_messages:]
    
    def describe(self) -> str:
        return f"Limit to {self.max_messages} messages" + (
            " (preserving system messages)" if self.preserve_system else ""
        )