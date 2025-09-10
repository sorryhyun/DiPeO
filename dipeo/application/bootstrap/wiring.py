"""Minimal wiring for thin startup - only registers services actually used at runtime."""

import logging
import os
from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceKey, ServiceRegistry
from dipeo.application.registry.keys import (
    API_INVOKER,
    API_KEY_SERVICE,
    BLOB_STORE,
    DOMAIN_EVENT_BUS,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    MESSAGE_BUS,
    MESSAGE_ROUTER,
    STATE_CACHE,
    STATE_REPOSITORY,
    STATE_SERVICE,
)

logger = logging.getLogger(__name__)


def wire_state_services(registry: ServiceRegistry, redis_client: Any = None) -> None:
    """Wire state management services."""

    from dipeo.infrastructure.execution.adapters import (
        StateCacheAdapter,
        StateServiceAdapter,
    )
    from dipeo.infrastructure.execution.state import EventBasedStateStore

    use_redis = os.getenv("DIPEO_STATE_BACKEND", "memory").lower() == "redis"

    if use_redis and redis_client:
        # TODO: Redis state adapters need to be reimplemented in new architecture
        store = EventBasedStateStore()
        repository = store
        service = StateServiceAdapter(repository)
        cache = StateCacheAdapter(store)
    else:
        store = EventBasedStateStore()
        repository = store
        service = StateServiceAdapter(repository)
        cache = StateCacheAdapter(store)

    registry.register(STATE_REPOSITORY, repository)
    registry.register(STATE_SERVICE, service)
    registry.register(STATE_CACHE, cache)


def wire_messaging_services(registry: ServiceRegistry) -> None:
    """Wire messaging services."""

    from dipeo.infrastructure.events.adapters import InMemoryEventBus

    event_bus_backend = os.getenv("DIPEO_EVENT_BUS_BACKEND", "adapter").lower()

    if event_bus_backend == "in_memory":
        from dipeo.infrastructure.events.adapters import InMemoryEventBus

        domain_event_bus = InMemoryEventBus(
            max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
            enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true",
        )
    elif event_bus_backend == "redis":
        domain_event_bus = InMemoryEventBus(
            max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
            enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true",
        )
    else:
        domain_event_bus = InMemoryEventBus(
            max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
            enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true",
        )

    redis_url = os.getenv("DIPEO_REDIS_URL")
    if redis_url:
        try:
            from dipeo.infrastructure.execution.messaging.redis_message_router import (
                RedisMessageRouter,
            )

            router = RedisMessageRouter()
            logger.info("Using RedisMessageRouter for multi-worker subscription support")
        except ImportError as e:
            logger.warning(f"Failed to import RedisMessageRouter (missing redis dependency?): {e}")
            logger.warning("Falling back to in-memory MessageRouter")
            from dipeo.infrastructure.execution.messaging.message_router import MessageRouter

            router = MessageRouter()
    else:
        from dipeo.infrastructure.execution.messaging.message_router import MessageRouter

        router = MessageRouter()
        workers = int(os.getenv("DIPEO_WORKERS", "1"))
        if workers > 1:
            logger.warning(
                "Running with multiple workers without Redis. "
                "GraphQL subscriptions require Redis for multi-worker support. "
                "Set DIPEO_REDIS_URL to enable Redis-backed message routing."
            )

    registry.register(MESSAGE_ROUTER, router)
    registry.register(MESSAGE_BUS, router)
    registry.register(DOMAIN_EVENT_BUS, domain_event_bus)


def wire_llm_services(registry: ServiceRegistry, api_key_service: Any = None) -> None:
    """Wire LLM services."""
    if not api_key_service:
        if registry.has(API_KEY_SERVICE):
            api_key_service = registry.resolve(API_KEY_SERVICE)
        else:
            from dipeo.infrastructure.shared.keys.drivers.environment_service import (
                EnvironmentAPIKeyService,
            )

            api_key_service = EnvironmentAPIKeyService()

    use_simplified = os.getenv("DIPEO_USE_SIMPLIFIED_LLM", "true").lower() == "true"

    if use_simplified:
        from dipeo.infrastructure.llm.simplified_service import SimplifiedLLMService

        llm_infra = SimplifiedLLMService(api_key_service)
    else:
        from dipeo.infrastructure.llm.drivers.service import LLMInfraService

        llm_infra = LLMInfraService(api_key_service)

    registry.register(LLM_SERVICE, llm_infra)


def wire_api_services(registry: ServiceRegistry) -> None:
    """Wire integrated API services."""

    from dipeo.infrastructure.integrations.adapters.api_adapter import (
        ApiInvokerAdapter,
    )

    use_v2 = os.getenv("INTEGRATIONS_PORT_V2", "0") == "1"

    if use_v2:
        from dipeo.infrastructure.integrations.adapters.api_invoker import HttpApiInvoker
        from dipeo.infrastructure.integrations.drivers.http_client import HttpClient
        from dipeo.infrastructure.integrations.drivers.manifest_registry import ManifestRegistry
        from dipeo.infrastructure.integrations.drivers.rate_limiter import RateLimiter

        http_client = HttpClient()
        rate_limiter = RateLimiter()
        manifest_registry = ManifestRegistry()

        api_invoker = HttpApiInvoker(
            http=http_client, limiter=rate_limiter, manifests=manifest_registry
        )
    else:
        from dipeo.infrastructure.integrations.drivers.integrated_api.service import (
            IntegratedApiService,
        )

        if registry.has(API_KEY_SERVICE):
            api_key_port = registry.resolve(API_KEY_SERVICE)
            api_service = IntegratedApiService(api_key_port=api_key_port)
        else:
            api_service = IntegratedApiService()

        api_invoker = ApiInvokerAdapter(api_service)

    registry.register(API_INVOKER, api_invoker)


def wire_event_services(registry: ServiceRegistry) -> None:
    """Wire event services and connect router to event bus."""

    from dipeo.diagram_generated.enums import EventType
    from dipeo.infrastructure.events.adapters import InMemoryEventBus

    if registry.has(DOMAIN_EVENT_BUS):
        domain_event_bus = registry.resolve(DOMAIN_EVENT_BUS)
    else:
        event_bus_backend = os.getenv("DIPEO_EVENT_BUS_BACKEND", "adapter").lower()

        if event_bus_backend == "in_memory":
            domain_event_bus = InMemoryEventBus(
                max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
                enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true",
            )
        else:
            domain_event_bus = InMemoryEventBus(
                max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "1000")),
                enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true",
            )

    if not registry.has(DOMAIN_EVENT_BUS):
        registry.register(DOMAIN_EVENT_BUS, domain_event_bus)

    if registry.has(MESSAGE_ROUTER):
        router = registry.resolve(MESSAGE_ROUTER)

        async def subscribe_router():
            await domain_event_bus.subscribe(
                event_types=[et for et in EventType],
                handler=router,
            )

        registry.register(ServiceKey("router_subscription"), subscribe_router)


def wire_storage_services(registry: ServiceRegistry) -> None:
    """Wire storage services."""

    from dipeo.infrastructure.shared.adapters import (
        LocalBlobAdapter,
        LocalFileSystemAdapter,
    )

    storage_backend = os.getenv("DIPEO_STORAGE_BACKEND", "local").lower()

    if storage_backend == "s3":
        from dipeo.infrastructure.shared.adapters import S3Adapter

        bucket = os.getenv("DIPEO_S3_BUCKET", "dipeo-storage")
        region = os.getenv("DIPEO_S3_REGION", "us-east-1")
        blob_store = S3Adapter(bucket=bucket, region=region)
    else:
        from dipeo.config import get_settings

        settings = get_settings()
        base_dir = Path(settings.storage.base_dir).resolve()
        storage_path = base_dir / "storage"
        blob_store = LocalBlobAdapter(base_path=storage_path)

    from dipeo.config import get_settings

    settings = get_settings()
    filesystem = LocalFileSystemAdapter(base_path=Path(settings.storage.base_dir).resolve())

    registry.register(BLOB_STORE, blob_store)
    registry.register(FILESYSTEM_ADAPTER, filesystem)


def wire_minimal(registry: ServiceRegistry, redis_client: object | None = None) -> None:
    """Wire only the minimal set of services actually used at runtime.

    This avoids registering ~37 unused services identified by runtime analysis.
    Services are wired lazily on first use where possible.

    Args:
        registry: The service registry to wire services into
        redis_client: Optional Redis client for distributed state
    """
    from dipeo.application.conversation.wiring import wire_conversation
    from dipeo.application.diagram.wiring import (
        wire_diagram_port,
        wire_diagram_use_cases,
    )
    from dipeo.application.execution.wiring import wire_execution

    wire_state_services(registry, redis_client)
    wire_event_services(registry)
    wire_storage_services(registry)

    if not registry.has(API_KEY_SERVICE):
        from dipeo.infrastructure.shared.keys.drivers.api_key_service import APIKeyService

        api_key_service = APIKeyService()
        registry.register(API_KEY_SERVICE, api_key_service)
    else:
        api_key_service = registry.resolve(API_KEY_SERVICE)

    wire_llm_services(registry, api_key_service)
    wire_diagram_port(registry)
    wire_diagram_use_cases(registry)
    wire_execution(registry)
    wire_conversation(registry)


def wire_feature_flags(registry: ServiceRegistry, features: list[str]) -> None:
    """Wire optional features based on feature flags.

    Args:
        registry: The service registry
        features: List of feature names to enable
    """
    if "ast_parser" in features:
        from dipeo.application.bootstrap.infrastructure_container import wire_ast_parser

        wire_ast_parser(registry)

    if "blob_storage" in features:
        wire_storage_services(registry)


wire_all_services = wire_minimal
