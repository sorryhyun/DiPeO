"""Dynamic objects that maintain state during diagram execution."""

from .conversation import Conversation, ConversationContext
from .person import Person

__all__ = [
    # Dynamic objects
    "Conversation",
    "ConversationContext", 
    "Person",
]