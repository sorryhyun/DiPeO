"""Server bootstrap module - composition root for dependency injection.

This module contains all the infrastructure wiring that was previously
in application/bootstrap/wiring.py. The application layer should not
import infrastructure directly - that's the responsibility of the
composition root at the edge of the system (server/CLI).
"""

import logging
import os
from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceKey, ServiceRegistry
from dipeo.application.registry.keys import (
    API_INVOKER,
    API_KEY_SERVICE,
    AST_PARSER,
    BLOB_STORE,
    EVENT_BUS,
    FILESYSTEM_ADAPTER,
    IR_BUILDER_REGISTRY,
    IR_CACHE,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    STATE_CACHE,
    STATE_REPOSITORY,
    STATE_SERVICE,
    TEMPLATE_PROCESSOR,
    TEMPLATE_RENDERER,
)

logger = logging.getLogger(__name__)


def wire_state_services(registry: ServiceRegistry, redis_client: Any = None) -> None:
    """Wire state management services."""
    from dipeo.infrastructure.execution.state import CacheFirstStateStore

    # Configuration
    cache_size = int(os.getenv("DIPEO_STATE_CACHE_SIZE", "1000"))
    checkpoint_interval = int(os.getenv("DIPEO_STATE_CHECKPOINT_INTERVAL", "10"))
    warm_cache_size = int(os.getenv("DIPEO_STATE_WARM_CACHE_SIZE", "20"))
    persistence_delay = float(os.getenv("DIPEO_STATE_PERSISTENCE_DELAY", "5.0"))

    # Create state store that implements all three protocols
    store = CacheFirstStateStore(
        cache_size=cache_size,
        checkpoint_interval=checkpoint_interval,
        warm_cache_size=warm_cache_size,
        persistence_delay=persistence_delay,
        write_through_critical=True,
    )

    # Register the same store instance for all three services
    # CacheFirstStateStore now implements all three protocols directly
    registry.register(STATE_REPOSITORY, store)
    registry.register(STATE_SERVICE, store)
    registry.register(STATE_CACHE, store)


def wire_messaging_services(registry: ServiceRegistry) -> None:
    """Wire messaging services."""
    from dipeo.infrastructure.events.adapters import InMemoryEventBus
    from dipeo.infrastructure.execution.messaging.message_router import MessageRouter

    # Create event bus
    event_bus = InMemoryEventBus(
        max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "10000")),
        enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true",
    )

    # Create message router (Redis support if available)
    redis_url = os.getenv("DIPEO_REDIS_URL")
    if redis_url:
        try:
            from dipeo.infrastructure.execution.messaging.redis_message_router import (
                RedisMessageRouter,
            )

            router = RedisMessageRouter()
            logger.info("Using RedisMessageRouter for multi-worker subscription support")
        except ImportError:
            router = MessageRouter()
            logger.info("Using in-memory MessageRouter")
    else:
        router = MessageRouter()

    # Register services
    registry.register(EVENT_BUS, event_bus)
    registry.register(MESSAGE_ROUTER, router)


def wire_llm_services(registry: ServiceRegistry, api_key_service: Any) -> None:
    """Wire LLM services."""
    from dipeo.infrastructure.llm.drivers.service import LLMInfraService

    llm_infra = LLMInfraService(api_key_service)
    registry.register(LLM_SERVICE, llm_infra)


def wire_api_services(registry: ServiceRegistry) -> None:
    """Wire integrated API services."""
    from dipeo.infrastructure.integrations.adapters.api_adapter import ApiInvokerAdapter
    from dipeo.infrastructure.integrations.drivers.integrated_api.service import (
        IntegratedApiService,
    )

    api_key_port = registry.resolve(API_KEY_SERVICE)
    api_service = IntegratedApiService(api_key_port=api_key_port)
    api_invoker = ApiInvokerAdapter(api_service)

    registry.register(API_INVOKER, api_invoker)


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
        storage_path = base_dir / "files"
        blob_store = LocalBlobAdapter(base_path=storage_path)

    from dipeo.config import get_settings

    settings = get_settings()
    filesystem = LocalFileSystemAdapter(base_path=Path(settings.storage.base_dir).resolve())

    registry.register(BLOB_STORE, blob_store)
    registry.register(FILESYSTEM_ADAPTER, filesystem)


def wire_template_services(registry: ServiceRegistry) -> None:
    """Wire template and processing services for code generation and prompt processing."""
    from dipeo.infrastructure.codegen.parsers.parser_service import ParserService
    from dipeo.infrastructure.codegen.templates.drivers.factory import get_template_service
    from dipeo.infrastructure.template.simple_processor import SimpleTemplateProcessor

    # Create the codegen template service for the TEMPLATE_RENDERER port
    template_service = get_template_service(template_dirs=[])
    registry.register(TEMPLATE_RENDERER, template_service)

    # Register the simple template processor for prompt building
    registry.register(TEMPLATE_PROCESSOR, SimpleTemplateProcessor())

    # Register the TypeScript AST parser service
    from dipeo.config import get_settings

    settings = get_settings()
    ast_parser = ParserService(
        config={
            "project_root": settings.storage.base_dir,
            "cache_enabled": True,
        }
    )
    registry.register(AST_PARSER, ast_parser)


def wire_ir_services(registry: ServiceRegistry) -> None:
    """Wire IR builder and cache services."""
    from dipeo.infrastructure.codegen.ir_cache import IRCache
    from dipeo.infrastructure.codegen.ir_registry import IRBuilderRegistry

    # Create and register IR cache
    ir_cache = IRCache()
    registry.register(IR_CACHE, ir_cache)

    # Create and register IR builder registry
    ir_registry = IRBuilderRegistry()
    registry.register(IR_BUILDER_REGISTRY, ir_registry)


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
                max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "10000")),
                enable_event_store=os.getenv("DIPEO_ENABLE_EVENT_STORE", "false").lower() == "true",
            )
        else:
            domain_event_bus = InMemoryEventBus(
                max_queue_size=int(os.getenv("DIPEO_EVENT_QUEUE_SIZE", "10000")),
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
            ]

            async def subscribe_state_store():
                from dipeo.domain.events.types import EventPriority

                # Subscribe with LOW priority so state updates happen after other handlers
                await domain_event_bus.subscribe(
                    event_types=state_events,
                    handler=state_store,
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


def bootstrap_services(registry: ServiceRegistry, redis_client: object | None = None) -> None:
    """Single consolidated bootstrap function for all services.

    This is the composition root for the server - it wires all infrastructure
    implementations to the domain ports and application services.

    Args:
        registry: The service registry to wire services into
        redis_client: Optional Redis client for distributed state
    """
    from dipeo.application.diagram.wiring import (
        wire_diagram_port,
        wire_diagram_use_cases,
    )
    from dipeo.application.execution.wiring import wire_execution
    from dipeo.infrastructure.shared.keys.drivers.api_key_service import APIKeyService

    # Core services (always required)
    wire_state_services(registry, redis_client)
    wire_messaging_services(registry)

    # Storage services
    wire_storage_services(registry)
    wire_template_services(registry)
    wire_ir_services(registry)

    # API and integration services
    from pathlib import Path

    from dipeo.config import get_settings

    settings = get_settings()
    api_key_path = Path(settings.storage.base_dir) / settings.storage.data_dir / "apikeys.json"
    api_key_service = APIKeyService(file_path=api_key_path)
    registry.register(API_KEY_SERVICE, api_key_service)

    wire_llm_services(registry, api_key_service)
    wire_api_services(registry)

    # Diagram services
    wire_diagram_port(registry)
    wire_diagram_use_cases(registry)

    # Execution services (includes conversation repositories)
    wire_execution(registry)

    # Event services must be last to connect everything
    wire_event_services(registry)

    logger.info("All services bootstrapped successfully")


async def execute_event_subscriptions(registry: ServiceRegistry) -> None:
    """Execute all event subscription callbacks registered in the registry.

    This activates event handling for services that need to subscribe to the event bus.
    """
    # Execute state store subscription if registered
    if registry.has(ServiceKey("state_store_subscription")):
        subscribe_fn = registry.resolve(ServiceKey("state_store_subscription"))
        # Check if it's already a coroutine or needs to be called
        import inspect

        if inspect.iscoroutinefunction(subscribe_fn):
            await subscribe_fn()
        elif inspect.iscoroutine(subscribe_fn):
            await subscribe_fn
        else:
            await subscribe_fn()

    # Execute router subscription if registered
    if registry.has(ServiceKey("router_subscription")):
        subscribe_fn = registry.resolve(ServiceKey("router_subscription"))
        # Check if it's already a coroutine or needs to be called
        import inspect

        if inspect.iscoroutinefunction(subscribe_fn):
            await subscribe_fn()
        elif inspect.iscoroutine(subscribe_fn):
            await subscribe_fn
        else:
            await subscribe_fn()


def wire_feature_flags(registry: ServiceRegistry, features: list[str]) -> None:
    """Wire optional features based on feature flags.

    Args:
        registry: The service registry
        features: List of enabled feature names
    """
    logger.info(f"Wiring feature flags: {features}")

    # Add feature-specific wiring here as needed
    for feature in features:
        if feature == "experimental_llm":
            # Wire experimental LLM features
            logger.info("Enabling experimental LLM features")
        elif feature == "distributed_state":
            # Wire distributed state features
            logger.info("Enabling distributed state features")
        # Add more feature flags as needed
