"""Application context and dependency injection configuration."""

import asyncio
import contextlib
import os

from dipeo.application.bootstrap import Container
from dipeo.config import BASE_DIR, get_settings
from dipeo.config.base_logger import get_module_logger
from dipeo.domain.events import EventType

logger = get_module_logger(__name__)
_container: Container | None = None


async def create_server_container() -> Container:
    """Create a server container with appropriate configuration."""
    import time

    start_time = time.time()

    settings = get_settings()
    container = Container(settings)

    from dipeo.application.registry.keys import (
        CLI_SESSION_SERVICE,
        EVENT_BUS,
        MESSAGE_ROUTER,
        PROVIDER_REGISTRY,
        STATE_STORE,
    )

    from .bootstrap import (
        bootstrap_services,
        execute_event_subscriptions,
        wire_feature_flags,
    )

    bootstrap_services(container.registry, redis_client=None)

    features = os.getenv("DIPEO_FEATURES", "").split(",") if os.getenv("DIPEO_FEATURES") else []
    if features:
        wire_feature_flags(container.registry, [f.strip() for f in features if f.strip()])

    from dipeo.infrastructure.execution.messaging import MessageRouter

    if container.registry.has(MESSAGE_ROUTER):
        message_router = container.registry.resolve(MESSAGE_ROUTER)
    else:
        message_router = MessageRouter()
        container.registry.register(MESSAGE_ROUTER, message_router)

    domain_event_bus = container.registry.resolve(EVENT_BUS)
    event_bus = domain_event_bus

    from dipeo.application.bootstrap.lifecycle import initialize_service
    from dipeo.application.registry import ServiceKey
    from dipeo.application.registry.keys import STATE_REPOSITORY

    state_store = container.registry.resolve(STATE_REPOSITORY)
    await initialize_service(state_store)

    if not container.registry.has(STATE_STORE):
        container.registry.register(STATE_STORE, state_store)

    await execute_event_subscriptions(container.registry)

    await message_router.initialize()

    if domain_event_bus is not None:
        from dipeo.domain.events.types import EventPriority

        ui_event_types = [
            EventType.EXECUTION_STARTED,
            EventType.EXECUTION_COMPLETED,
            EventType.EXECUTION_ERROR,
            EventType.NODE_STARTED,
            EventType.NODE_COMPLETED,
            EventType.NODE_ERROR,
            EventType.EXECUTION_LOG,
        ]

        await domain_event_bus.subscribe(
            event_types=ui_event_types,
            handler=message_router,
            priority=EventPriority.NORMAL,
        )

    from dipeo.application.execution.observers import MetricsObserver

    metrics_observer = MetricsObserver(event_bus=event_bus, state_store=state_store)

    METRICS_OBSERVER_KEY = ServiceKey[MetricsObserver]("metrics_observer")
    container.registry.register(METRICS_OBSERVER_KEY, metrics_observer)

    metrics_events = [
        EventType.EXECUTION_STARTED,
        EventType.NODE_STARTED,
        EventType.NODE_COMPLETED,
        EventType.NODE_ERROR,
        EventType.EXECUTION_COMPLETED,
    ]

    for event_type in metrics_events:
        await event_bus.subscribe(event_type, metrics_observer)

    await metrics_observer.start()

    from dipeo.infrastructure.integrations.drivers.integrated_api.registry import (
        ProviderRegistry,
    )

    provider_registry = ProviderRegistry()
    await provider_registry.initialize()

    try:
        await provider_registry.load_manifests(str(BASE_DIR / "integrations/**/provider.yaml"))
        await provider_registry.load_manifests(str(BASE_DIR / "integrations/**/provider.yml"))
        await provider_registry.load_manifests(str(BASE_DIR / "integrations/**/provider.json"))
        loaded_providers = provider_registry.list_providers()
    except Exception as e:
        logger.warning(f"Failed to load provider manifests: {e}")

    container.registry.register(PROVIDER_REGISTRY, provider_registry)

    if domain_event_bus is not None:
        await domain_event_bus.initialize()
    await event_bus.initialize()

    from dipeo.application.execution.use_cases import CliSessionService

    if not container.registry.has(CLI_SESSION_SERVICE):
        container.registry.register(CLI_SESSION_SERVICE, CliSessionService())

    unused = container.registry.report_unused()
    if unused:
        logger.info(f"🔎 Unused registrations this run ({len(unused)}): {', '.join(unused)}")

    total_time = (time.time() - start_time) * 1000
    logger.info(f"✅ Server container initialized in {total_time:.1f}ms")

    return container


def get_container() -> Container:
    if _container is None:
        raise RuntimeError("Container not initialized. Call initialize_container() first.")
    return _container


def initialize_container() -> Container:
    global _container

    if _container is None:
        try:
            asyncio.get_running_loop()
            raise RuntimeError("initialize_container must be called before the event loop starts")
        except RuntimeError:
            _container = asyncio.run(create_server_container())

    return _container


async def initialize_container_async() -> Container:
    """Async version of initialize_container for use within async contexts."""
    global _container

    if _container is None:
        _container = await create_server_container()

    return _container
