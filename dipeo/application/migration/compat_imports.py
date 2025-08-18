"""Compatibility imports for Wave 5 migration.

This module provides imports from the domain layer.
V2 (domain layer) is now the default and only implementation.
"""

from typing import TYPE_CHECKING


# State Management Ports
from dipeo.domain.execution.state.ports import (
    ExecutionStateRepository as StateStorePort,
    ExecutionStateService as StateServicePort,
    ExecutionCachePort as StateCachePort,
)


# Messaging Ports
from dipeo.domain.messaging.ports import (
    MessageBus as MessageRouterPort,
)


# LLM Ports
from dipeo.domain.llm.ports import (
    LLMService as LLMServicePort,
    LLMClient as LLMClientPort,
    MemoryService as MemoryServicePort,
)


# API Integration Ports
from dipeo.domain.integrations.ports import (
    ApiInvoker as IntegratedApiServicePort,
    ApiProvider as ApiProviderPort,
    ApiProviderRegistry as ApiProviderRegistryPort,
)


# Storage Ports
from dipeo.domain.storage.ports import (
    BlobStorePort as FileServicePort,  # Map BlobStore to FileService
    FileSystemPort,
)
# DiagramStoragePort doesn't exist yet in domain
DiagramStoragePort = FileServicePort


# Event/Observer Ports
from dipeo.domain.messaging.ports import DomainEventBus
# ExecutionObserver defined in application layer
from dipeo.application.execution.observer_protocol import ExecutionObserver


# API Key Port
from dipeo.application.ports.apikey_port import APIKeyPort


# Diagram Ports (still in core for now)
from dipeo.domain.diagram.ports import (  # type: ignore
    DiagramCompiler,
    DiagramPort,
    FormatStrategy,
    DiagramStorageSerializer,
)


# Export all compatibility imports
__all__ = [
    # State
    "StateStorePort",
    "StateServicePort",
    "StateCachePort",
    # Messaging
    "MessageRouterPort",
    # LLM
    "LLMServicePort",
    "LLMClientPort",
    "MemoryServicePort",
    # API
    "IntegratedApiServicePort",
    "ApiProviderPort",
    "ApiProviderRegistryPort",
    # Storage
    "FileServicePort",
    "DiagramStoragePort",
    "FileSystemPort",
    # Events
    "ExecutionObserver",
    "DomainEventBus",
    # Core (unchanged)
    "APIKeyPort",
    "DiagramCompiler",
    "DiagramPort",
    "FormatStrategy",
    "DiagramStorageSerializer",
]


# Registry token compatibility
if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry


def resolve_port(registry: "ServiceRegistry", port_type: str):
    """Resolve a port from the registry with V1/V2 compatibility.
    
    Args:
        registry: The service registry
        port_type: The type of port to resolve
        
    Returns:
        The resolved service instance
    """
    from dipeo.application.registry.registry_tokens import (
        STATE_REPOSITORY,
        STATE_SERVICE, 
        STATE_CACHE,
        MESSAGE_BUS,
        LLM_SERVICE,
        LLM_CLIENT,
        MEMORY_SERVICE,
        API_INVOKER,
        API_PROVIDER_REGISTRY,
        BLOB_STORAGE,
        DOMAIN_EVENT_BUS,
        API_KEY_SERVICE,
    )
    
    # Map port types to registry tokens (always use v2 tokens)
    token_map = {
        "state_store": STATE_REPOSITORY,
        "state_service": STATE_SERVICE,
        "state_cache": STATE_CACHE,
        "message_router": MESSAGE_BUS,
        "llm_service": LLM_SERVICE,
        "llm_client": LLM_CLIENT,
        "memory_service": MEMORY_SERVICE,
        "api_service": API_INVOKER,
        "api_registry": API_PROVIDER_REGISTRY,
        "file_service": BLOB_STORAGE,
        "event_bus": DOMAIN_EVENT_BUS,
        "apikey_service": API_KEY_SERVICE,
    }
    
    token = token_map.get(port_type.lower())
    if token is None:
        raise ValueError(f"No service available for port type: {port_type}")
    
    # For string tokens (V1), resolve directly
    if isinstance(token, str):
        return registry.resolve(token)
    
    # For ServiceKey tokens (V2), resolve with type safety
    return registry.resolve(token)