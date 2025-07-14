"""Dynamic objects that maintain state during diagram execution."""

from .conversation import Conversation, ConversationContext
from .person import Person
from .execution_context import ExecutionContext
from .conversation_manager import ConversationManager
from .person_manager import PersonManager

__all__ = [
    # Dynamic objects
    "Conversation",
    "ConversationContext", 
    "Person",
    
    # Protocols
    "ExecutionContext",
    "ConversationManager",
    "PersonManager",
]