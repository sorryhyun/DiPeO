"""Memory filter system for managing different views of the global conversation."""

from typing import List, Callable, Optional, Protocol, Set
from enum import Enum
from dipeo.models import Message, PersonID


class MemoryView(Enum):
    """Different views/filters for a person's memory of the global conversation."""
    
    # Core views
    ALL_INVOLVED = "all_involved"  # Messages where person is sender or recipient (current default)
    SENT_BY_ME = "sent_by_me"  # Messages I sent
    SENT_TO_ME = "sent_to_me"  # Messages sent to me
    WITNESSED = "witnessed"  # Messages between others that I can see
    
    # Combined views
    DIRECT_ONLY = "direct_only"  # Only direct messages (sent by me or to me)
    GROUP_CONTEXT = "group_context"  # All messages in my execution context
    
    # Specialized views
    SYSTEM_AND_ME = "system_and_me"  # System messages and my interactions
    LAST_EXCHANGE = "last_exchange"  # Last message to me and my response
    CONVERSATION_PAIRS = "conversation_pairs"  # Messages grouped as request/response pairs


class MemoryFilter(Protocol):
    """Protocol for memory filters."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        """Filter messages based on the person's perspective."""
        ...
    
    def describe(self) -> str:
        """Return a human-readable description of this filter."""
        ...


class AllInvolvedFilter:
    """Filter for messages where person is sender or recipient."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        return [
            msg for msg in messages
            if msg.from_person_id == person_id or msg.to_person_id == person_id
        ]
    
    def describe(self) -> str:
        return "Messages where I am sender or recipient"


class SentByMeFilter:
    """Filter for messages sent by this person."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        return [msg for msg in messages if msg.from_person_id == person_id]
    
    def describe(self) -> str:
        return "Messages I sent"


class SentToMeFilter:
    """Filter for messages sent to this person."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        return [msg for msg in messages if msg.to_person_id == person_id]
    
    def describe(self) -> str:
        return "Messages sent to me"


class WitnessedFilter:
    """Filter for messages between others that this person can witness."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        return [
            msg for msg in messages
            if msg.from_person_id != person_id and msg.to_person_id != person_id
        ]
    
    def describe(self) -> str:
        return "Messages between others"


class DirectOnlyFilter:
    """Filter for only direct messages (sent by or to this person)."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        return [
            msg for msg in messages
            if (msg.from_person_id == person_id or msg.to_person_id == person_id)
            and msg.from_person_id != PersonID("system")
        ]
    
    def describe(self) -> str:
        return "Direct messages only (excluding system)"


class GroupContextFilter:
    """Filter for all messages in the same execution context."""
    
    def __init__(self, execution_id: Optional[str] = None):
        self.execution_id = execution_id
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        if not self.execution_id:
            # Without execution context, return all messages
            return messages
        
        # Filter by execution context
        return [
            msg for msg in messages
            if msg.execution_id == self.execution_id
        ]
    
    def describe(self) -> str:
        return f"All messages in execution context {self.execution_id or 'current'}"


class SystemAndMeFilter:
    """Filter for system messages and this person's interactions."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        return [
            msg for msg in messages
            if (msg.from_person_id == PersonID("system") and msg.to_person_id == person_id)
            or msg.from_person_id == person_id
        ]
    
    def describe(self) -> str:
        return "System messages to me and my responses"


class LastExchangeFilter:
    """Filter for the last message to this person and their response."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        # Find all messages to this person
        to_me = [(i, msg) for i, msg in enumerate(messages) if msg.to_person_id == person_id]
        
        if not to_me:
            return []
        
        # Get the last message to this person
        last_to_me_idx, last_to_me = to_me[-1]
        
        # Look for the response from this person after that message
        response = None
        for i in range(last_to_me_idx + 1, len(messages)):
            if messages[i].from_person_id == person_id:
                response = messages[i]
                break
        
        result = [last_to_me]
        if response:
            result.append(response)
        
        return result
    
    def describe(self) -> str:
        return "Last message to me and my response"


class ConversationPairsFilter:
    """Filter that groups messages as request/response pairs."""
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
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


class CompositeFilter:
    """Combines multiple filters with AND/OR logic."""
    
    def __init__(self, filters: List[MemoryFilter], combine_mode: str = "AND"):
        self.filters = filters
        self.combine_mode = combine_mode
    
    def filter(self, messages: List[Message], person_id: PersonID) -> List[Message]:
        if self.combine_mode == "AND":
            # All filters must match
            result = messages
            for f in self.filters:
                result = f.filter(result, person_id)
            return result
        else:  # OR
            # Any filter can match
            seen: Set[str] = set()
            result = []
            for f in self.filters:
                for msg in f.filter(messages, person_id):
                    if msg.id not in seen:
                        seen.add(msg.id)
                        result.append(msg)
            return result
    
    def describe(self) -> str:
        descriptions = [f.describe() for f in self.filters]
        return f" {self.combine_mode} ".join(descriptions)


class MemoryFilterFactory:
    """Factory for creating memory filters."""
    
    _filters = {
        MemoryView.ALL_INVOLVED: AllInvolvedFilter,
        MemoryView.SENT_BY_ME: SentByMeFilter,
        MemoryView.SENT_TO_ME: SentToMeFilter,
        MemoryView.WITNESSED: WitnessedFilter,
        MemoryView.DIRECT_ONLY: DirectOnlyFilter,
        MemoryView.GROUP_CONTEXT: GroupContextFilter,
        MemoryView.SYSTEM_AND_ME: SystemAndMeFilter,
        MemoryView.LAST_EXCHANGE: LastExchangeFilter,
        MemoryView.CONVERSATION_PAIRS: ConversationPairsFilter,
    }
    
    @classmethod
    def create(cls, view: MemoryView, **kwargs) -> MemoryFilter:
        """Create a memory filter for the specified view."""
        filter_class = cls._filters.get(view)
        if not filter_class:
            raise ValueError(f"Unknown memory view: {view}")
        
        # Handle filters that need constructor arguments
        if view == MemoryView.GROUP_CONTEXT:
            return filter_class(execution_id=kwargs.get("execution_id"))
        
        return filter_class()
    
    @classmethod
    def create_composite(
        cls, 
        views: List[MemoryView], 
        combine_mode: str = "AND",
        **kwargs
    ) -> MemoryFilter:
        """Create a composite filter combining multiple views."""
        filters = [cls.create(view, **kwargs) for view in views]
        return CompositeFilter(filters, combine_mode)


class MemoryLimiter:
    """Applies memory limits while preserving important messages."""
    
    def __init__(self, max_messages: int, preserve_system: bool = True):
        self.max_messages = max_messages
        self.preserve_system = preserve_system
    
    def limit(self, messages: List[Message]) -> List[Message]:
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