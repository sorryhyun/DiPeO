"""Dynamic objects that maintain state during diagram execution."""

from .conversation import Conversation, ConversationContext
from .conversation_manager import ConversationManager
from .person import Person
from .person_manager import PersonManager

__all__ = [
    # Dynamic objects
    "Conversation",
    "ConversationContext", 
    "Person",
    
    # Protocols
    "ConversationManager",
    "PersonManager",
]