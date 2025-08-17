"""Compatibility imports for Wave 5 migration.

This module provides backward-compatible imports that automatically
select between old core/ports and new domain ports based on feature flags.
"""

import os
from typing import TYPE_CHECKING

# Check feature flags
def _is_v2_enabled(service: str) -> bool:
    """Check if V2 is enabled for a service."""
    specific = os.getenv(f"{service.upper()}_PORT_V2", "").lower()
    if specific in ["1", "true"]:
        return True
    if specific in ["0", "false"]:
        return False
    return os.getenv("DIPEO_PORT_V2", "0").lower() in ["1", "true"]


# State Management Ports
if _is_v2_enabled("state"):
    from dipeo.domain.execution.state.ports import (
        ExecutionStateRepository as StateStorePort,
        ExecutionStateService as StateServicePort,
        ExecutionCachePort as StateCachePort,
    )
else:
    from dipeo.domain.ports import StateStorePort  # type: ignore
    StateServicePort = StateStorePort  # Legacy doesn't have separate service
    StateCachePort = StateStorePort  # Legacy doesn't have cache


# Messaging Ports
if _is_v2_enabled("messaging"):
    from dipeo.domain.messaging.ports import (
        MessageBus as MessageRouterPort,
    )
else:
    from dipeo.domain.ports import MessageRouterPort  # type: ignore


# LLM Ports
if _is_v2_enabled("llm"):
    from dipeo.domain.llm.ports import (
        LLMService as LLMServicePort,
        LLMClient as LLMClientPort,
        MemoryService as MemoryServicePort,
    )
else:
    from dipeo.domain.ports import LLMServicePort  # type: ignore
    LLMClientPort = LLMServicePort  # Legacy doesn't separate client/service
    MemoryServicePort = None  # Legacy doesn't have memory service


# API Integration Ports
if _is_v2_enabled("api"):
    from dipeo.domain.integrations.ports import (
        ApiInvoker as IntegratedApiServicePort,
        ApiProvider as ApiProviderPort,
        ApiProviderRegistry as ApiProviderRegistryPort,
    )
else:
    from dipeo.domain.ports import (  # type: ignore
        IntegratedApiServicePort,
        ApiProviderPort,
    )
    ApiProviderRegistryPort = None  # Legacy doesn't have registry


# Storage Ports
if _is_v2_enabled("storage"):
    from dipeo.domain.storage.ports import (
        BlobStorePort as FileServicePort,  # Map BlobStore to FileService
        FileSystemPort,
    )
    # DiagramStoragePort doesn't exist yet in domain
    DiagramStoragePort = FileServicePort
else:
    from dipeo.core.bak.ports import FileServicePort  # type: ignore
    DiagramStoragePort = FileServicePort  # Legacy doesn't separate
    FileSystemPort = FileServicePort  # Legacy doesn't separate


# Event/Observer Ports
if _is_v2_enabled("events"):
    from dipeo.domain.messaging.ports import DomainEventBus
    # Avoid circular import - just use the core observer for now
    from dipeo.core.bak.ports import ExecutionObserver  # type: ignore
else:
    from dipeo.core.bak.ports import ExecutionObserver  # type: ignore
    DomainEventBus = None  # Legacy doesn't have event bus


# API Key Port (still in core for now)
from dipeo.core.bak.ports import APIKeyPort  # type: ignore


# Diagram Ports (still in core for now)
from dipeo.domain.diagram.ports import (  # type: ignore
    DiagramCompiler,
    DiagramConverter,
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
    "DiagramConverter",
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
    
    # Map port types to registry tokens
    token_map = {
        "state_store": STATE_REPOSITORY if _is_v2_enabled("state") else "state_store",
        "state_service": STATE_SERVICE if _is_v2_enabled("state") else "state_store",
        "state_cache": STATE_CACHE if _is_v2_enabled("state") else "state_store",
        "message_router": MESSAGE_BUS if _is_v2_enabled("messaging") else "message_router",
        "llm_service": LLM_SERVICE if _is_v2_enabled("llm") else "llm_service",
        "llm_client": LLM_CLIENT if _is_v2_enabled("llm") else "llm_service",
        "memory_service": MEMORY_SERVICE if _is_v2_enabled("llm") else None,
        "api_service": API_INVOKER if _is_v2_enabled("api") else "integrated_api_service",
        "api_registry": API_PROVIDER_REGISTRY if _is_v2_enabled("api") else None,
        "file_service": BLOB_STORAGE if _is_v2_enabled("storage") else "file_service",
        "event_bus": DOMAIN_EVENT_BUS if _is_v2_enabled("events") else None,
        "apikey_service": API_KEY_SERVICE,  # Always use new token
    }
    
    token = token_map.get(port_type.lower())
    if token is None:
        raise ValueError(f"No service available for port type: {port_type}")
    
    # For string tokens (V1), resolve directly
    if isinstance(token, str):
        return registry.resolve(token)
    
    # For ServiceKey tokens (V2), resolve with type safety
    return registry.resolve(token)