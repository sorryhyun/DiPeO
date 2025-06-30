"""DiPeO Infrastructure - Infrastructure adapters and services."""

__version__ = "0.1.0"

# Import from organized structure
from .persistence.file.file_service import SimpleFileService
from .persistence.file.file_operations import SimpleFileOperationsService
from .persistence.memory.memory_service import SimpleMemoryService
from .external.llm.conversation_adapter import SimpleConversationService
from .external.http.http_client import APIIntegrationDomainService
from .external.notion.notion_adapter import NotionIntegrationDomainService
from .messaging.websocket_router import MessageRouter, message_router
from .text import SimpleTextService
from .config import Settings, Environment, settings, get_settings, reload_settings

__all__ = [
    "SimpleFileService", 
    "SimpleMemoryService",
    "SimpleTextService",
    "SimpleFileOperationsService",
    "SimpleConversationService",
    "APIIntegrationDomainService",
    "NotionIntegrationDomainService",
    "MessageRouter",
    "message_router",
    "Settings",
    "Environment",
    "settings",
    "get_settings",
    "reload_settings",
]