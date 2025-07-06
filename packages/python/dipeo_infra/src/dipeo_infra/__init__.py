"""DiPeO Infrastructure - Infrastructure adapters and services."""

__version__ = "0.1.0"

# Import from organized structure
from .persistence.file.modular_file_service import ModularFileService as ConsolidatedFileService
from .persistence.memory.memory_service import MemoryService
from .external.llm.services import LLMInfraService
from .external.notion.service import NotionAPIService
from .external.apikey.environment_adapter import EnvironmentAPIKeyService
from .messaging.websocket_router import MessageRouter, message_router
from .config import Settings, Environment, settings, get_settings, reload_settings

__all__ = [
    "ConsolidatedFileService",
    "MemoryService",
    "LLMInfraService",
    "NotionAPIService",
    "EnvironmentAPIKeyService",
    "MessageRouter",
    "message_router",
    "Settings",
    "Environment",
    "settings",
    "get_settings",
    "reload_settings",
]
