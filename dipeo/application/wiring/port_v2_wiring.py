"""Application wiring for V2 domain ports with feature flag support."""

import os
from pathlib import Path
from typing import Any, Optional

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.registry_tokens import (
    API_INVOKER,
    API_KEY_SERVICE,
    API_PROVIDER_REGISTRY,
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


def is_v2_enabled(service_name: str) -> bool:
    """Check if V2 is enabled for a specific service via feature flags."""
    # Check specific service flag first
    specific_flag = os.getenv(f"{service_name.upper()}_PORT_V2", "").lower()
    if specific_flag in ["1", "true", "yes", "on"]:
        return True
    if specific_flag in ["0", "false", "no", "off"]:
        return False
    
    # Check global flag
    global_flag = os.getenv("DIPEO_PORT_V2", "0").lower()
    return global_flag in ["1", "true", "yes", "on"]


def wire_state_services(registry: ServiceRegistry, redis_client: Any = None) -> None:
    """Wire state management services based on feature flags."""
    
    if is_v2_enabled("state"):
        # Use V2 domain ports
        from dipeo.infrastructure.adapters.state import (
            StateRepositoryAdapter,
            StateServiceAdapter,
            StateCacheAdapter,
        )
        
        # Choose implementation based on config
        use_redis = os.getenv("DIPEO_STATE_BACKEND", "memory").lower() == "redis"
        
        if use_redis and redis_client:
            from dipeo.infrastructure.adapters.state.redis_state_adapter import (
                RedisStateRepository,
                RedisStateService,
                RedisStateCache,
            )
            repository = RedisStateRepository(redis_client)
            service = RedisStateService(repository)
            cache = RedisStateCache(redis_client, repository)
        else:
            # Use existing EventBasedStateStore via adapters
            from dipeo.infrastructure.state import EventBasedStateStore
            store = EventBasedStateStore()
            repository = StateRepositoryAdapter(store)
            service = StateServiceAdapter(repository)
            cache = StateCacheAdapter(store)
        
        registry.register(STATE_REPOSITORY, repository)
        registry.register(STATE_SERVICE, service)
        registry.register(STATE_CACHE, cache)
    else:
        # Use V1 core ports (existing behavior)
        from dipeo.infrastructure.state import EventBasedStateStore
        store = EventBasedStateStore()
        # Register as core port (not domain port)
        registry.register("state_store", store)


def wire_messaging_services(registry: ServiceRegistry) -> None:
    """Wire messaging services based on feature flags."""
    
    if is_v2_enabled("messaging"):
        # Use V2 domain ports
        from dipeo.infrastructure.adapters.messaging.messaging_adapter import (
            MessageBusAdapter,
            DomainEventBusAdapter,
        )
        from dipeo.infrastructure.adapters.messaging import MessageRouter
        from dipeo.infrastructure.events import AsyncEventBus
        
        # Create underlying infrastructure
        router = MessageRouter()
        event_bus = AsyncEventBus()
        
        # Wrap with domain adapters
        message_bus = MessageBusAdapter(router)
        domain_event_bus = DomainEventBusAdapter(event_bus)
        
        registry.register(MESSAGE_BUS, message_bus)
        registry.register(DOMAIN_EVENT_BUS, domain_event_bus)
    else:
        # Use V1 core ports
        from dipeo.infrastructure.adapters.messaging import MessageRouter
        from dipeo.infrastructure.events import AsyncEventBus
        
        registry.register("message_router", MessageRouter())
        registry.register("event_bus", AsyncEventBus())


def wire_llm_services(registry: ServiceRegistry, api_key_service: Any = None) -> None:
    """Wire LLM services based on feature flags."""
    
    if is_v2_enabled("llm"):
        # Use V2 domain ports
        from dipeo.infrastructure.adapters.llm.llm_adapter import (
            LLMClientAdapter,
            LLMServiceAdapter,
            InMemoryMemoryService,
        )
        
        # Get or create API key service
        if not api_key_service:
            if registry.has(API_KEY_SERVICE):
                api_key_service = registry.resolve(API_KEY_SERVICE)
            else:
                from dipeo.infrastructure.services.keys.environment_service import EnvironmentAPIKeyService
                api_key_service = EnvironmentAPIKeyService()
        
        # Create LLM infrastructure service
        from dipeo.infrastructure.services.llm import LLMInfraService
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
    else:
        # Use V1 core ports
        from dipeo.infrastructure.services.llm import LLMInfraService
        from dipeo.infrastructure.services.keys.environment_service import EnvironmentAPIKeyService
        
        if not api_key_service:
            api_key_service = EnvironmentAPIKeyService()
        
        llm_service = LLMInfraService(api_key_service)
        registry.register("llm_service", llm_service)


def wire_api_services(registry: ServiceRegistry) -> None:
    """Wire integrated API services based on feature flags."""
    
    if is_v2_enabled("api"):
        # Use V2 domain ports
        from dipeo.infrastructure.adapters.api.api_adapter import (
            ApiProviderRegistryAdapter,
            ApiInvokerAdapter,
            SimpleApiProvider,
        )
        from dipeo.infrastructure.services.integrated_api.service import IntegratedApiService
        
        # Create underlying service
        api_service = IntegratedApiService()
        
        # Wrap with domain adapters
        provider_registry = ApiProviderRegistryAdapter(api_service)
        api_invoker = ApiInvokerAdapter(api_service)
        
        # Register some default providers for testing
        # Note: actual registration should be done asynchronously when the service is initialized
        
        registry.register(API_PROVIDER_REGISTRY, provider_registry)
        registry.register(API_INVOKER, api_invoker)
    else:
        # Use V1 core ports
        from dipeo.infrastructure.services.integrated_api.service import IntegratedApiService
        api_service = IntegratedApiService()
        registry.register("integrated_api_service", api_service)


def wire_storage_services(registry: ServiceRegistry) -> None:
    """Wire storage services based on feature flags."""
    
    if is_v2_enabled("storage"):
        # Use V2 domain ports
        from dipeo.application.registry.registry_tokens import (
            BLOB_STORAGE,
            FILE_SYSTEM,
            ARTIFACT_STORE,
        )
        from dipeo.infrastructure.adapters.storage import (
            LocalBlobAdapter,
            LocalFileSystemAdapter,
            ArtifactStoreAdapter,
        )
        
        # Choose storage backend based on config
        storage_backend = os.getenv("DIPEO_STORAGE_BACKEND", "local").lower()
        
        if storage_backend == "s3":
            from dipeo.infrastructure.adapters.storage import S3Adapter
            bucket = os.getenv("DIPEO_S3_BUCKET", "dipeo-storage")
            region = os.getenv("DIPEO_S3_REGION", "us-east-1")
            blob_store = S3Adapter(bucket=bucket, region=region)
        else:
            # Default to local storage
            base_dir = os.getenv("DIPEO_BASE_DIR", str(Path.cwd()))
            storage_path = Path(base_dir) / "storage"
            blob_store = LocalBlobAdapter(base_path=storage_path)
            
        # File system adapter
        filesystem = LocalFileSystemAdapter(base_path=Path.cwd())
        
        # Artifact store built on blob store
        artifact_store = ArtifactStoreAdapter(blob_store=blob_store)
        
        registry.register(BLOB_STORAGE, blob_store)
        registry.register(FILE_SYSTEM, filesystem)
        registry.register(ARTIFACT_STORE, artifact_store)
    else:
        # Use V1 core ports (existing behavior)
        from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter
        filesystem = LocalFileSystemAdapter(base_path=Path.cwd())
        registry.register("filesystem_adapter", filesystem)


def wire_all_v2_services(
    registry: ServiceRegistry,
    redis_client: Optional[Any] = None,
    api_key_service: Optional[Any] = None,
) -> None:
    """Wire all V2 services with feature flag support.
    
    Args:
        registry: Service registry to register services with
        redis_client: Optional Redis client for state persistence
        api_key_service: Optional API key service for LLM services
    """
    # Wire each service group
    wire_state_services(registry, redis_client)
    wire_messaging_services(registry)
    wire_llm_services(registry, api_key_service)
    wire_api_services(registry)
    wire_storage_services(registry)
    
    # Log configuration
    import logging
    logger = logging.getLogger(__name__)
    
    v2_services = []
    if is_v2_enabled("state"):
        v2_services.append("state")
    if is_v2_enabled("messaging"):
        v2_services.append("messaging")
    if is_v2_enabled("llm"):
        v2_services.append("llm")
    if is_v2_enabled("api"):
        v2_services.append("api")
    if is_v2_enabled("storage"):
        v2_services.append("storage")
    
    if v2_services:
        logger.info(f"V2 ports enabled for: {', '.join(v2_services)}")
    else:
        logger.info("Using V1 core ports (V2 disabled)")


def get_feature_flag_status() -> dict[str, bool]:
    """Get the status of all V2 feature flags."""
    return {
        "state": is_v2_enabled("state"),
        "messaging": is_v2_enabled("messaging"),
        "llm": is_v2_enabled("llm"),
        "api": is_v2_enabled("api"),
        "storage": is_v2_enabled("storage"),
        "global": is_v2_enabled("_global"),
    }