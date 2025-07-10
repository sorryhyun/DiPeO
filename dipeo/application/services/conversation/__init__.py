"""Conversation application service for orchestration."""

from .memory_service import ConversationMemoryService
from .memory_service_v2 import ConversationMemoryServiceV2
from .conversation_manager_impl import ConversationManagerImpl
from .compatibility_adapter import (
    create_conversation_service,
    upgrade_conversation_service,
    ConversationServiceAdapter,
    is_using_legacy_conversation_service,
    migrate_to_conversation_manager
)

__all__ = [
    "ConversationMemoryService",
    "ConversationMemoryServiceV2", 
    "ConversationManagerImpl",
    "create_conversation_service",
    "upgrade_conversation_service",
    "ConversationServiceAdapter",
    "is_using_legacy_conversation_service",
    "migrate_to_conversation_manager"
]