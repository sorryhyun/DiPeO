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
    EVENT_BUS,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    STATE_CACHE,
    STATE_REPOSITORY,
    STATE_SERVICE,
)

logger = logging.getLogger(__name__)


def wire_state_services(registry: ServiceRegistry, redis_client: Any = None) -> None:
    """Wire state management services with enhanced durability options."""

    from dipeo.infrastructure.execution.adapters import (
        StateCacheAdapter,
        StateServiceAdapter,
    )
    from dipeo.infrastructure.execution.state import CacheFirstStateStore

    # Get configuration parameters
    cache_size = int(os.getenv("DIPEO_STATE_CACHE_SIZE", "1000"))
    checkpoint_interval = int(os.getenv("DIPEO_STATE_CHECKPOINT_INTERVAL", "10"))
    warm_cache_size = int(os.getenv("DIPEO_STATE_WARM_CACHE_SIZE", "20"))
    persistence_delay = float(os.getenv("DIPEO_STATE_PERSISTENCE_DELAY", "5.0"))

    # Check for DIPEO_STATE_BACKEND for backward compatibility
    backend = os.getenv("DIPEO_STATE_BACKEND", "").lower()
    if backend == "redis":
        raise RuntimeError(
            "Redis state store not yet implemented. "
            "CacheFirstStateStore will be used for all environments."
        )

    # Always use CacheFirstStateStore for both dev and production
    store = CacheFirstStateStore(
        cache_size=cache_size,
        checkpoint_interval=checkpoint_interval,
        warm_cache_size=warm_cache_size,
        persistence_delay=persistence_delay,
        write_through_critical=True,  # Enable write-through for critical events
    )
    logger.info(
        f"Using CacheFirstStateStore with durability enhancements "
        f"(cache_size={cache_size}, persistence_delay={persistence_delay}s)"
    )

    # Create adapters
    repository = store
    service = StateServiceAdapter(repository)
    cache = StateCacheAdapter(store)

    # Register services
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
    registry.register(EVENT_BUS, domain_event_bus)


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

    if registry.has(EVENT_BUS):
        domain_event_bus = registry.resolve(EVENT_BUS)
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

    if not registry.has(EVENT_BUS):
        registry.register(EVENT_BUS, domain_event_bus)

    # Wire CacheFirstStateStore to event bus for async state persistence
    if registry.has(STATE_REPOSITORY):
        state_store = registry.resolve(STATE_REPOSITORY)

        # Only subscribe if it's CacheFirstStateStore with handle_event method
        from dipeo.infrastructure.execution.state import CacheFirstStateStore

        if isinstance(state_store, CacheFirstStateStore):
            # State-related events that CacheFirstStateStore should handle
            state_events = [
                EventType.EXECUTION_STARTED,
                EventType.NODE_STARTED,
                EventType.NODE_COMPLETED,
                EventType.NODE_ERROR,
                EventType.EXECUTION_COMPLETED,
                EventType.METRICS_COLLECTED,
            ]

            async def subscribe_state_store():
                from dipeo.domain.events.types import EventPriority

                # Subscribe with LOW priority so state updates happen after other handlers
                await domain_event_bus.subscribe(
                    event_types=state_events,
                    handler=state_store.handle_event,
                    priority=EventPriority.LOW,
                )

                # Initialize the state store if needed
                if hasattr(state_store, "initialize"):
                    await state_store.initialize()

            registry.register(ServiceKey("state_store_subscription"), subscribe_state_store)

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


async def execute_event_subscriptions(registry: ServiceRegistry) -> None:
    """Execute all registered event subscriptions.

    This should be called after all services are wired to actually subscribe
    handlers to the event bus.
    """
    import inspect

    # Execute state manager subscription if registered
    state_manager_sub_key = ServiceKey("state_manager_subscription")
    if registry.has(state_manager_sub_key):
        subscribe_fn = registry.resolve(state_manager_sub_key)
        # Check if it's a coroutine function or already a coroutine
        if inspect.iscoroutinefunction(subscribe_fn):
            await subscribe_fn()
        elif inspect.iscoroutine(subscribe_fn):
            await subscribe_fn
        else:
            logger.warning(f"Unexpected type for state_manager_subscription: {type(subscribe_fn)}")

    # Execute router subscription if registered
    router_sub_key = ServiceKey("router_subscription")
    if registry.has(router_sub_key):
        subscribe_fn = registry.resolve(router_sub_key)
        # Check if it's a coroutine function or already a coroutine
        if inspect.iscoroutinefunction(subscribe_fn):
            await subscribe_fn()
        elif inspect.iscoroutine(subscribe_fn):
            await subscribe_fn
        else:
            logger.warning(f"Unexpected type for router_subscription: {type(subscribe_fn)}")


wire_all_services = wire_minimal
