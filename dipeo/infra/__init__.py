"""DiPeO infrastructure layer.

This module provides concrete implementations of the port interfaces
defined in the core layer. It includes adapters for external services
and infrastructure components.
"""

from .adapters import LLMInfraService, create_adapter
from .persistence import AsyncFileAdapter, ModularFileService, InMemoryConversationStore
# Import MemoryService alias for backward compatibility
from .persistence.memory import MemoryService
from .adapters.apikey import EnvironmentAPIKeyService
from .adapters.notion import NotionAPIService
from .messaging import MessageRouter

# For backward compatibility
ConsolidatedFileService = ModularFileService

__all__ = [
    # LLM adapters
    "LLMInfraService",
    "create_adapter",
    # File persistence
    "AsyncFileAdapter",
    "ModularFileService",
    "ConsolidatedFileService",  # Backward compatibility alias
    # Memory persistence
    "InMemoryConversationStore",
    "MemoryService",  # Backward compatibility alias
    # API Key management
    "EnvironmentAPIKeyService",
    # Messaging
    "MessageRouter",
    # External services
    "NotionAPIService",
]