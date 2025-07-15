"""Dynamic objects that maintain state during diagram execution."""

from .conversation import Conversation, ConversationContext
from .conversation_manager import ConversationManager
from .execution_context import ExecutionContext
from .person import Person
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