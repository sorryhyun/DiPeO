"""Memory persistence adapters."""

from .conversation_store import InMemoryConversationStore

# Keep MemoryService as an alias for backward compatibility
MemoryService = InMemoryConversationStore

__all__ = ["InMemoryConversationStore", "MemoryService"]