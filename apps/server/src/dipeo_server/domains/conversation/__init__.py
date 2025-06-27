# Barrel exports for conversation domain
from .conversation import Message, PersonConversation
from .service import ConversationService

__all__ = [
    "ConversationService",
    # Services and utilities
    "Message",
    "PersonConversation",
]
