"""Application wiring for all services.

This module provides wiring for all application services including state, messaging,
LLM, API, storage, and diagram services.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    API_INVOKER,
    API_KEY_SERVICE,
    API_PROVIDER_REGISTRY,
    BLOB_STORAGE,
    FILE_SYSTEM,
    ARTIFACT_STORE,
    DOMAIN_EVENT_BUS,
    LLM_CLIENT,
    LLM_REGISTRY,
    LLM_SERVICE,
    MEMORY_SERVICE,
    MESSAGE_BUS,
    STATE_CACHE,
    STATE_REPOSITORY,
    STATE_SERVICE,
)

logger = logging.getLogger(__name__)


def wire_state_services(registry: ServiceRegistry, redis_client: Any = None) -> None:
    """Wire state management services."""
    
    logger.info("🔄 Wiring state services with domain ports")
    from dipeo.infrastructure.execution.adapters import (
        StateRepositoryAdapter,
        StateServiceAdapter,
        StateCacheAdapter,
    )
    
    # Choose implementation based on config
    use_redis = os.getenv("DIPEO_STATE_BACKEND", "memory").lower() == "redis"
    
    if use_redis and redis_client:
        # TODO: Redis state adapters need to be reimplemented in new architecture
        # For now, fall back to in-memory adapters
        from dipeo.infrastructure.execution.adapters.state_adapter import (
            StateRepositoryAdapter,
            StateServiceAdapter,
            StateCacheAdapter,
        )
        repository = StateRepositoryAdapter()
        service = StateServiceAdapter(repository)
        cache = StateCacheAdapter()
    else:
        # Use existing EventBasedStateStore via adapters
        from dipeo.infrastructure.execution.state import EventBasedStateStore
        store = EventBasedStateStore()
        repository = StateRepositoryAdapter(store)
        service = StateServiceAdapter(repository)
        cache = StateCacheAdapter(store)
    
    registry.register(STATE_REPOSITORY, repository)
    registry.register(STATE_SERVICE, service)
    registry.register(STATE_CACHE, cache)
    
    logger.info(f"✅ State services wired: backend={use_redis and 'redis' or 'memory'}")


def wire_messaging_services(registry: ServiceRegistry) -> None:
    """Wire messaging services."""
    
    from dipeo.infrastructure.execution.messaging.messaging_adapter import MessageBusAdapter
    from dipeo.infrastructure.execution.messaging import MessageRouter
    from dipeo.infrastructure.events.adapters import InMemoryEventBus
    
    # Choose event bus implementation based on config
    event_bus_backend = os.getenv("DIPEO_EVENT_BUS_BACKEND", "adapter").lower()
    
    if event_bus_backend == "in_memory":
        # Use pure in-memory implementation
        from dipeo.infrastructure.events.adapters import InMemoryEventBus
        domain_event_bus = InMemoryEventBus(
            max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
            enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true"
        )
    elif event_bus_backend == "redis":
        # Redis not yet implemented, use in-memory fallback
        logger.info("Redis event bus not yet implemented, using in-memory fallback")
        domain_event_bus = InMemoryEventBus(
            max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
            enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true"
        )
    else:
        # Default to in-memory implementation
        domain_event_bus = InMemoryEventBus(
            max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
            enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true"
        )
    
    # Create message router
    router = MessageRouter()
    message_bus = MessageBusAdapter(router)
    
    registry.register(MESSAGE_BUS, message_bus)
    registry.register(DOMAIN_EVENT_BUS, domain_event_bus)


def wire_llm_services(registry: ServiceRegistry, api_key_service: Any = None) -> None:
    """Wire LLM services."""
    
    from dipeo.infrastructure.llm.adapters.llm_adapter import (
        LLMClientAdapter,
        LLMServiceAdapter,
        InMemoryMemoryService,
    )
    
    # Get or create API key service
    if not api_key_service:
        if registry.has(API_KEY_SERVICE):
            api_key_service = registry.resolve(API_KEY_SERVICE)
        else:
            from dipeo.infrastructure.shared.keys.drivers.environment_service import EnvironmentAPIKeyService
            api_key_service = EnvironmentAPIKeyService()
    
    # Create LLM infrastructure service
    from dipeo.infrastructure.llm.drivers.service import LLMInfraService
    llm_infra = LLMInfraService(api_key_service)
    
    # Wrap with domain adapters
    llm_client = LLMClientAdapter(llm_infra)
    llm_service = LLMServiceAdapter(llm_infra)
    memory_service = InMemoryMemoryService()
    
    # Register LLM registry for multi-provider support
    llm_registry = {
        "openai": llm_client,
        "anthropic": llm_client,
        "google": llm_client,
        "ollama": llm_client,
    }
    
    registry.register(LLM_CLIENT, llm_client)
    registry.register(LLM_SERVICE, llm_service)
    registry.register(LLM_REGISTRY, llm_registry)
    registry.register(MEMORY_SERVICE, memory_service)


def wire_api_services(registry: ServiceRegistry) -> None:
    """Wire integrated API services."""
    
    from dipeo.infrastructure.integrations.adapters.api_adapter import (
        ApiProviderRegistryAdapter,
        ApiInvokerAdapter,
    )
    
    # Check if V2 is enabled
    use_v2 = os.getenv("INTEGRATIONS_PORT_V2", "0") == "1"
    
    if use_v2:
        # V2 implementation with separate HTTP client, rate limiter, etc.
        from dipeo.infrastructure.integrations.adapters.api_invoker import HttpApiInvoker
        from dipeo.infrastructure.integrations.drivers.http_client import HttpClient
        from dipeo.infrastructure.integrations.drivers.rate_limiter import RateLimiter
        from dipeo.infrastructure.integrations.drivers.manifest_registry import ManifestRegistry
        
        http_client = HttpClient()
        rate_limiter = RateLimiter()
        manifest_registry = ManifestRegistry()
        
        api_invoker = HttpApiInvoker(
            http=http_client,
            limiter=rate_limiter,
            manifests=manifest_registry
        )
        
        # For V2, also need provider registry
        from dipeo.infrastructure.integrations.drivers.api_provider_registry import APIProviderRegistry
        provider_registry = APIProviderRegistry()
    else:
        # Use existing integrated API service
        from dipeo.infrastructure.integrations.drivers.integrated_api.service import IntegratedApiService
        
        # If API key service is registered, use it
        if registry.has(API_KEY_SERVICE):
            api_key_port = registry.resolve(API_KEY_SERVICE)
            api_service = IntegratedApiService(api_key_port=api_key_port)
        else:
            api_service = IntegratedApiService()
        
        # Wrap with domain adapters
        provider_registry = ApiProviderRegistryAdapter(api_service)
        api_invoker = ApiInvokerAdapter(api_service)
    
    registry.register(API_PROVIDER_REGISTRY, provider_registry)
    registry.register(API_INVOKER, api_invoker)


def wire_event_services(registry: ServiceRegistry) -> None:
    """Wire event services for observer migration."""
    
    from dipeo.infrastructure.events.adapters import InMemoryEventBus
    from dipeo.infrastructure.execution.messaging import ObserverToEventAdapter
    
    # Get or create domain event bus
    if registry.has(DOMAIN_EVENT_BUS):
        domain_event_bus = registry.resolve(DOMAIN_EVENT_BUS)
    else:
        # Create based on backend config
        event_bus_backend = os.getenv("DIPEO_EVENT_BUS_BACKEND", "adapter").lower()
        
        if event_bus_backend == "in_memory":
            domain_event_bus = InMemoryEventBus(
                max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
                enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true"
            )
        else:
            # Default to in-memory implementation
            domain_event_bus = InMemoryEventBus(
                max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
                enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true"
            )
    
    # Create observer adapter for backward compatibility
    observer_adapter = ObserverToEventAdapter(domain_event_bus)
    
    # Register services
    registry.register(DOMAIN_EVENT_BUS, domain_event_bus)
    
    # Also register as string key for backward compatibility
    from dipeo.application.registry import ServiceKey
    registry.register(ServiceKey("execution_observer"), observer_adapter)
    
    logger.info("Events/Observers migration: Using domain events with observer adapter")


def wire_storage_services(registry: ServiceRegistry) -> None:
    """Wire storage services."""
    
    from dipeo.infrastructure.shared.adapters import (
        LocalBlobAdapter,
        LocalFileSystemAdapter,
        ArtifactStoreAdapter,
    )
    
    # Choose storage backend based on config
    storage_backend = os.getenv("DIPEO_STORAGE_BACKEND", "local").lower()
    
    if storage_backend == "s3":
        from dipeo.infrastructure.shared.adapters import S3Adapter
        bucket = os.getenv("DIPEO_S3_BUCKET", "dipeo-storage")
        region = os.getenv("DIPEO_S3_REGION", "us-east-1")
        blob_store = S3Adapter(bucket=bucket, region=region)
    else:
        # Default to local storage using config
        from dipeo.config import get_settings
        settings = get_settings()
        base_dir = Path(settings.storage.base_dir).resolve()
        storage_path = base_dir / "storage"
        blob_store = LocalBlobAdapter(base_path=storage_path)
        
    # File system adapter - use config base_dir
    from dipeo.config import get_settings
    settings = get_settings()
    filesystem = LocalFileSystemAdapter(base_path=Path(settings.storage.base_dir).resolve())
    
    # Artifact store built on blob store
    artifact_store = ArtifactStoreAdapter(blob_store=blob_store)
    
    registry.register(BLOB_STORAGE, blob_store)
    registry.register(FILE_SYSTEM, filesystem)
    registry.register(ARTIFACT_STORE, artifact_store)


def wire_all_services(
    registry: ServiceRegistry,
    redis_client: Optional[Any] = None,
    api_key_service: Optional[Any] = None,
) -> None:
    """Wire all application services.
    
    Args:
        registry: Service registry to register services with
        redis_client: Optional Redis client for state persistence
        api_key_service: Optional API key service for LLM services
    """
    # Wire each service group
    wire_state_services(registry, redis_client)
    wire_messaging_services(registry)
    wire_event_services(registry)
    wire_llm_services(registry, api_key_service)
    wire_api_services(registry)
    wire_storage_services(registry)
    
    # Wire diagram services
    from dipeo.application.diagram.wiring import wire_diagram
    wire_diagram(registry)
    
    logger.info("✅ All application services wired")