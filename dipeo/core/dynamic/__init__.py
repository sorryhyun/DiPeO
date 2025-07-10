"""Dynamic objects that maintain state during diagram execution."""

from .conversation import Conversation, ConversationContext
from .person import Person
from .execution_context import ExecutionContext, ExecutionCoordinator
from .conversation_manager import ConversationManager, ConversationPersistence
from .person_manager import PersonManager, PersonPersistence
from .execution_observer import ExecutionObserver, ExecutionMetrics

__all__ = [
    # Dynamic objects
    "Conversation",
    "ConversationContext", 
    "Person",
    
    # Protocols
    "ExecutionContext",
    "ExecutionCoordinator",
    "ConversationManager",
    "ConversationPersistence",
    "PersonManager",
    "PersonPersistence",
    "ExecutionObserver",
    "ExecutionMetrics"
]