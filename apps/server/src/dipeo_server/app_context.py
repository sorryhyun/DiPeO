"""Application context and dependency injection configuration."""

import asyncio
import contextlib
import os

from dipeo.application.bootstrap import Container
from dipeo.config import BASE_DIR, get_settings
from dipeo.domain.events import EventType

_container: Container | None = None


async def create_server_container() -> Container:
    """Create a server container with appropriate configuration.

    This replaces the complex ServerContainer with a simple configuration-based approach.
    """
    # Get unified settings
    settings = get_settings()

    # Create container with unified settings
    container = Container(settings)
    # Use minimal wiring for thin startup
    from dipeo.application.bootstrap.wiring import (
        wire_feature_flags,
        wire_messaging_services,
        wire_minimal,
    )
    from dipeo.application.registry.keys import (
        CLI_SESSION_SERVICE,
        EVENT_BUS,
        MESSAGE_ROUTER,
        PROVIDER_REGISTRY,
        STATE_STORE,
    )

    # Wire only essential services
    wire_minimal(container.registry, redis_client=None)

    # Wire optional features if specified
    features = os.getenv("DIPEO_FEATURES", "").split(",") if os.getenv("DIPEO_FEATURES") else []
    if features:
        wire_feature_flags(container.registry, [f.strip() for f in features if f.strip()])

    # Wire messaging services for server operation
    wire_messaging_services(container.registry)

    # Get the message router from registry
    from dipeo.infrastructure.execution.messaging import MessageRouter

    if container.registry.has(MESSAGE_ROUTER):
        message_router = container.registry.resolve(MESSAGE_ROUTER)
    else:
        # Create and register message router if not found
        message_router = MessageRouter()
        container.registry.register(MESSAGE_ROUTER, message_router)

    # Get or create domain event bus
    # Event bus is already imported above as EVENT_BUS

    if container.registry.has(EVENT_BUS):
        domain_event_bus = container.registry.resolve(EVENT_BUS)
        event_bus = domain_event_bus
    else:
        # Fallback to InMemoryEventBus
        from dipeo.infrastructure.events.adapters import InMemoryEventBus

        queue_size = getattr(settings.messaging, "queue_size", 50000)
        event_bus = InMemoryEventBus(max_queue_size=queue_size)
        domain_event_bus = None
        container.registry.register(EVENT_BUS, event_bus)

    # Get state repository and initialize
    from dipeo.application.bootstrap.lifecycle import initialize_service
    from dipeo.application.registry import ServiceKey
    from dipeo.application.registry.keys import STATE_REPOSITORY

    state_store = container.registry.resolve(STATE_REPOSITORY)
    await initialize_service(state_store)

    # Register for backward compatibility
    container.registry.register(STATE_STORE, state_store)

    # AsyncStateManager is now wired and subscribed in wiring.py
    # Execute event subscriptions to activate AsyncStateManager
    from dipeo.application.bootstrap.wiring import execute_event_subscriptions

    await execute_event_subscriptions(container.registry)

    # Get async state manager if registered
    async_state_manager_key = ServiceKey("async_state_manager")
    state_manager = None
    if container.registry.has(async_state_manager_key):
        state_manager = container.registry.resolve(async_state_manager_key)

    # Initialize and wire MessageRouter
    await message_router.initialize()

    if domain_event_bus is not None:
        from dipeo.domain.events.types import EventPriority

        # UI-relevant event types
        ui_event_types = [
            EventType.EXECUTION_STARTED,
            EventType.EXECUTION_COMPLETED,
            EventType.EXECUTION_ERROR,
            EventType.NODE_STARTED,
            EventType.NODE_COMPLETED,
            EventType.NODE_ERROR,
            EventType.NODE_PROGRESS,
            EventType.EXECUTION_UPDATE,
            EventType.EXECUTION_LOG,
            EventType.METRICS_COLLECTED,
            EventType.WEBHOOK_RECEIVED,
        ]

        await domain_event_bus.subscribe(
            event_types=ui_event_types,
            handler=message_router,
            priority=EventPriority.NORMAL,
        )

    # Create and subscribe metrics observer
    from dipeo.application.execution.observers import MetricsObserver
    from dipeo.application.registry.keys import ServiceKey

    metrics_observer = MetricsObserver(event_bus=event_bus)

    # Register metrics observer in the container for external access
    METRICS_OBSERVER_KEY = ServiceKey[MetricsObserver]("metrics_observer")
    container.registry.register(METRICS_OBSERVER_KEY, metrics_observer)

    # Subscribe to metrics events
    metrics_events = [
        EventType.EXECUTION_STARTED,
        EventType.NODE_STARTED,
        EventType.NODE_COMPLETED,
        EventType.NODE_ERROR,
        EventType.EXECUTION_COMPLETED,
    ]

    if hasattr(event_bus, "subscribe"):
        for event_type in metrics_events:
            await event_bus.subscribe(event_type, metrics_observer)

    # Initialize provider registry for webhook integration
    from dipeo.infrastructure.integrations.drivers.integrated_api.registry import (
        ProviderRegistry,
    )

    provider_registry = ProviderRegistry()

    # Initialize the registry first
    await provider_registry.initialize()

    # Load providers from manifests
    try:
        # Load all provider manifests - use BASE_DIR to ensure correct path
        await provider_registry.load_manifests(str(BASE_DIR / "integrations/**/provider.yaml"))
        await provider_registry.load_manifests(str(BASE_DIR / "integrations/**/provider.yml"))
        await provider_registry.load_manifests(str(BASE_DIR / "integrations/**/provider.json"))

        # Log what was loaded
        import logging

        logger = logging.getLogger(__name__)
        loaded_providers = provider_registry.list_providers()
        logger.info(f"Loaded {len(loaded_providers)} providers: {loaded_providers}")
    except Exception as e:
        # Log but don't fail if no providers found
        import logging

        logging.getLogger(__name__).warning(f"Failed to load provider manifests: {e}")

    container.registry.register(PROVIDER_REGISTRY, provider_registry)

    # Start services
    if domain_event_bus is not None and hasattr(domain_event_bus, "start"):
        await domain_event_bus.start()
    if hasattr(event_bus, "start"):
        await event_bus.start()
    # state_manager is initialized via execute_event_subscriptions
    if hasattr(metrics_observer, "start"):
        await metrics_observer.start()

    # Register CLI session service if not already registered
    from dipeo.application.execution.use_cases import CliSessionService

    if not container.registry.has(CLI_SESSION_SERVICE):
        container.registry.register(CLI_SESSION_SERVICE, CliSessionService())

    # Report unused services
    import logging

    logger = logging.getLogger(__name__)
    unused = container.registry.report_unused()
    if unused:
        logger.info(f"🔎 Unused registrations this run ({len(unused)}): {', '.join(unused)}")

    return container


def get_container() -> Container:
    if _container is None:
        raise RuntimeError("Container not initialized. Call initialize_container() first.")
    return _container


def initialize_container() -> Container:
    global _container

    if _container is None:
        # Initializing server with simplified container system
        # Run the async function in a new event loop if needed
        try:
            asyncio.get_running_loop()
            # If we're already in an event loop, this is an error
            raise RuntimeError("initialize_container must be called before the event loop starts")
        except RuntimeError:
            # No event loop running, create container synchronously
            _container = asyncio.run(create_server_container())

    return _container


async def initialize_container_async() -> Container:
    """Async version of initialize_container for use within async contexts."""
    global _container

    if _container is None:
        # Initializing server with simplified container system
        _container = await create_server_container()

    return _container
