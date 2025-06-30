"""DiPeO Infrastructure - Infrastructure adapters and services."""

__version__ = "0.1.0"

# Import from organized structure
from .persistence.file.file_service import FileService
from .persistence.file.file_operations import FileOperationsService
from .persistence.memory.memory_service import MemoryService
from .external.llm.conversation_adapter import ConversationService
from .external.notion.notion_adapter import NotionIntegrationDomainService
from .messaging.websocket_router import MessageRouter, message_router
from .config import Settings, Environment, settings, get_settings, reload_settings

__all__ = [
    "FileService",
    "MemoryService",
    "FileOperationsService",
    "ConversationService",
    "NotionIntegrationDomainService",
    "MessageRouter",
    "message_router",
    "Settings",
    "Environment",
    "settings",
    "get_settings",
    "reload_settings",
]
