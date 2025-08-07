"""Memory filter system for managing different views of the global conversation."""

from enum import Enum
from typing import Protocol

from dipeo.diagram_generated import Message, PersonID


class MemoryView(Enum):
    
    ALL_INVOLVED = "all_involved"
    SENT_BY_ME = "sent_by_me"
    SENT_TO_ME = "sent_to_me"
    SYSTEM_AND_ME = "system_and_me"
    CONVERSATION_PAIRS = "conversation_pairs"
    ALL_MESSAGES = "all_messages"


class MemoryFilter(Protocol):
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        ...
    
    def describe(self) -> str:
        ...


class AllInvolvedFilter:
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [
            msg for msg in messages
            if msg.from_person_id == person_id or msg.to_person_id == person_id
        ]
    
    def describe(self) -> str:
        return "Messages where I am sender or recipient"


class SentByMeFilter:
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [msg for msg in messages if msg.from_person_id == person_id]
    
    def describe(self) -> str:
        return "Messages I sent"


class SentToMeFilter:
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [msg for msg in messages if msg.to_person_id == person_id]
    
    def describe(self) -> str:
        return "Messages sent to me"


class SystemAndMeFilter:
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return [
            msg for msg in messages
            if (msg.from_person_id == PersonID("system") and msg.to_person_id == person_id)
            or msg.from_person_id == person_id
        ]
    
    def describe(self) -> str:
        return "System messages to me and my responses"


class ConversationPairsFilter:
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        result = []
        
        for i, msg in enumerate(messages):
            if msg.to_person_id == person_id:
                result.append(msg)
                
                if i + 1 < len(messages) and messages[i + 1].from_person_id == person_id:
                    result.append(messages[i + 1])
            elif msg.from_person_id == person_id and (not result or result[-1].from_person_id != person_id):
                result.append(msg)
        
        return result
    
    def describe(self) -> str:
        return "Messages grouped as request/response pairs"


class AllMessagesFilter:
    
    def filter(self, messages: list[Message], person_id: PersonID) -> list[Message]:
        return messages
    
    def describe(self) -> str:
        return "All messages in the conversation"


class MemoryFilterFactory:
    
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
        filter_class = cls._filters.get(view)
        if not filter_class:
            raise ValueError(f"Unknown memory view: {view}")
        
        return filter_class()


class MemoryLimiter:
    
    def __init__(self, max_messages: int, preserve_system: bool = True):
        self.max_messages = max_messages
        self.preserve_system = preserve_system
    
    def limit(self, messages: list[Message]) -> list[Message]:
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
            
            available_slots = self.max_messages - len(system_messages)
            if available_slots <= 0:
                return system_messages[-self.max_messages:]
            return system_messages + non_system_messages[-available_slots:]
        else:
            return messages[-self.max_messages:]
    
    def describe(self) -> str:
        return f"Limit to {self.max_messages} messages" + (
            " (preserving system messages)" if self.preserve_system else ""
        )