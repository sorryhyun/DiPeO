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
    """Create a server container with appropriate configuration.

    This replaces the complex ServerContainer with a simple configuration-based approach.
    """
    # Get unified settings
    settings = get_settings()

    # Create container with unified settings
    container = Container(settings)
    # Use minimal wiring for thin startup
    from apps.server.bootstrap import (
        bootstrap_services,
        execute_event_subscriptions,
        wire_feature_flags,
    )
    from dipeo.application.registry.keys import (
        CLI_SESSION_SERVICE,
        EVENT_BUS,
        MESSAGE_ROUTER,
        PROVIDER_REGISTRY,
        STATE_STORE,
    )
    # Bootstrap all services
    bootstrap_services(container.registry, redis_client=None)

    # Wire optional features if specified
    features = os.getenv("DIPEO_FEATURES", "").split(",") if os.getenv("DIPEO_FEATURES") else []
    if features:
        wire_feature_flags(container.registry, [f.strip() for f in features if f.strip()])

    # Messaging services are already wired by bootstrap_services
    # No need to wire separately

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

    # Event bus is required - no fallback
    domain_event_bus = container.registry.resolve(EVENT_BUS)
    event_bus = domain_event_bus

    # Get state repository and initialize
    from dipeo.application.bootstrap.lifecycle import initialize_service
    from dipeo.application.registry import ServiceKey
    from dipeo.application.registry.keys import STATE_REPOSITORY

    state_store = container.registry.resolve(STATE_REPOSITORY)
    await initialize_service(state_store)

    # Register for backward compatibility
    # Guard against duplicate registration (STATE_STORE is marked as immutable)
    if not container.registry.has(STATE_STORE):
        container.registry.register(STATE_STORE, state_store)
    else:
        logger.debug("STATE_STORE already registered, skipping")

    # CacheFirstStateStore is now wired and subscribed in bootstrap.py
    # Execute event subscriptions to activate state store event handling
    await execute_event_subscriptions(container.registry)

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
            EventType.EXECUTION_LOG,
        ]

        await domain_event_bus.subscribe(
            event_types=ui_event_types,
            handler=message_router,
            priority=EventPriority.NORMAL,
        )

    # Create and subscribe metrics observer
    from dipeo.application.execution.observers import MetricsObserver

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

    # Subscribe metrics observer to events
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
        loaded_providers = provider_registry.list_providers()
    except Exception as e:
        # Log but don't fail if no providers found
        logger.warning(f"Failed to load provider manifests: {e}")

    container.registry.register(PROVIDER_REGISTRY, provider_registry)

    # Initialize services
    if domain_event_bus is not None:
        await domain_event_bus.initialize()
    await event_bus.initialize()
    # state_manager is initialized via execute_event_subscriptions
    # metrics_observer doesn't require initialization

    # Register CLI session service if not already registered
    from dipeo.application.execution.use_cases import CliSessionService

    if not container.registry.has(CLI_SESSION_SERVICE):
        container.registry.register(CLI_SESSION_SERVICE, CliSessionService())

    # Report unused services
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
