"""DiPeO infrastructure layer.

This module provides concrete implementations of the port interfaces
defined in the core layer. It includes adapters for external services
and infrastructure components.
"""

from .adapters import LLMInfraService, create_adapter
from .persistence import AsyncFileAdapter, ModularFileService, MemoryService
from .external.apikey import EnvironmentAPIKeyService

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
    "MemoryService",
    # API Key management
    "EnvironmentAPIKeyService",
]