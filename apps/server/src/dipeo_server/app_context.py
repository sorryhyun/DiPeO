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
    features = (
        os.getenv("DIPEO_FEATURES", "").split(",")
        if os.getenv("DIPEO_FEATURES")
        else []
    )
    if features:
        wire_feature_flags(
            container.registry, [f.strip() for f in features if f.strip()]
        )

    # Wire messaging services for server operation
    wire_messaging_services(container.registry)
    from dipeo.application.registry.keys import MESSAGE_BUS

    # Get the message router from wiring (registered as both MESSAGE_BUS and MESSAGE_ROUTER)
    if container.registry.has(MESSAGE_ROUTER):
        message_router = container.registry.resolve(MESSAGE_ROUTER)
    elif container.registry.has(MESSAGE_BUS):
        # Fallback to MESSAGE_BUS if MESSAGE_ROUTER not found
        message_router = container.registry.resolve(MESSAGE_BUS)
        # Also register as MESSAGE_ROUTER for consistency
        container.registry.register(MESSAGE_ROUTER, message_router)
    else:
        # Fallback to direct creation if wiring failed
        from dipeo.infrastructure.execution.messaging import MessageRouter

        message_router = MessageRouter()
        container.registry.register(MESSAGE_ROUTER, message_router)
        container.registry.register(MESSAGE_BUS, message_router)

    # Event services are already wired by minimal wiring

    from dipeo.application.registry.keys import DOMAIN_EVENT_BUS

    # Get the domain event bus from wiring
    domain_event_bus = None
    if container.registry.has(DOMAIN_EVENT_BUS):
        # Use the EventBus directly
        domain_event_bus = container.registry.resolve(DOMAIN_EVENT_BUS)
        # Use domain event bus directly (no adapter needed)
        event_bus = domain_event_bus
    else:
        # Fallback to InMemoryEventBus (use canonical location)
        from dipeo.infrastructure.events.adapters import InMemoryEventBus

        # Use unified config for queue size (use a reasonable default)
        queue_size = getattr(settings.messaging, "queue_size", 50000)
        event_bus = InMemoryEventBus(max_queue_size=queue_size)
        container.registry.register(EVENT_BUS, event_bus)

    # State services are already wired by minimal wiring

    from dipeo.application.registry.keys import (
        STATE_REPOSITORY,
    )

    # Get the state repository for state manager
    state_store = container.registry.resolve(STATE_REPOSITORY)

    # Initialize if needed (using Lifecycle protocol)
    from dipeo.application.bootstrap.lifecycle import initialize_service

    await initialize_service(state_store)

    # Also register as STATE_STORE for backward compatibility
    container.registry.register(STATE_STORE, state_store)

    # Create state manager as separate service
    from dipeo.infrastructure.execution.state import AsyncStateManager

    state_manager = AsyncStateManager(state_store)

    # Subscribe state manager to the EventBus
    if domain_event_bus is not None:
        from dipeo.domain.events.types import EventPriority

        # Subscribe state manager to event bus so it persists state changes
        await domain_event_bus.subscribe(
            event_types=[
                EventType.EXECUTION_STARTED,
                EventType.NODE_STARTED,
                EventType.NODE_COMPLETED,
                EventType.NODE_ERROR,
                EventType.EXECUTION_COMPLETED,
                EventType.METRICS_COLLECTED,
            ],
            handler=state_manager,
            priority=EventPriority.LOW,  # Process after other handlers
        )
    else:
        # Fallback to legacy event bus subscription (for backward compatibility)
        if hasattr(event_bus, "subscribe"):
            await event_bus.subscribe(EventType.EXECUTION_STARTED, state_manager)
            await event_bus.subscribe(EventType.NODE_STARTED, state_manager)
            await event_bus.subscribe(EventType.NODE_COMPLETED, state_manager)
            await event_bus.subscribe(EventType.NODE_ERROR, state_manager)
            await event_bus.subscribe(EventType.EXECUTION_COMPLETED, state_manager)

    # StreamingMonitor removed - MessageRouter handles all event routing directly

    # Initialize MessageRouter before wiring
    await message_router.initialize()

    # Wire MessageRouter as EventHandler to EventBus
    if domain_event_bus is not None:
        # MessageRouter now implements EventHandler, subscribe it directly to the bus
        from dipeo.domain.events.types import EventPriority

        # Subscribe to all UI-relevant event types
        ui_event_types = [
            EventType.EXECUTION_STARTED,
            EventType.EXECUTION_COMPLETED,
            EventType.EXECUTION_ERROR,
            EventType.NODE_STARTED,
            EventType.NODE_COMPLETED,
            EventType.NODE_ERROR,
            EventType.NODE_PROGRESS,
            EventType.EXECUTION_UPDATE,
            EventType.EXECUTION_LOG,  # Add EXECUTION_LOG for monitor mode logs
            EventType.METRICS_COLLECTED,
            EventType.WEBHOOK_RECEIVED,
        ]

        # Subscribe router to domain event bus with normal priority
        await domain_event_bus.subscribe(
            event_types=ui_event_types,
            handler=message_router,
            priority=EventPriority.NORMAL,
        )

    # Streaming monitor removed - events flow directly through MessageRouter

    # Create metrics observer for performance analysis
    from dipeo.application.execution.observers import MetricsObserver

    # Get the actual event bus from the registry if available
    actual_event_bus = event_bus
    if container.registry.has(EVENT_BUS):
        # Try to get the actual AsyncEventBus if it's registered
        with contextlib.suppress(Exception):
            actual_event_bus = container.registry.resolve(EVENT_BUS)

    metrics_observer = MetricsObserver(event_bus=actual_event_bus)

    # Subscribe metrics observer to execution events (works with both V1 and V2)
    if hasattr(event_bus, "subscribe"):
        await event_bus.subscribe(EventType.EXECUTION_STARTED, metrics_observer)
        await event_bus.subscribe(EventType.NODE_STARTED, metrics_observer)
        await event_bus.subscribe(EventType.NODE_COMPLETED, metrics_observer)
        await event_bus.subscribe(EventType.NODE_ERROR, metrics_observer)
        await event_bus.subscribe(EventType.EXECUTION_COMPLETED, metrics_observer)

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
        await provider_registry.load_manifests(
            str(BASE_DIR / "integrations/**/provider.yaml")
        )
        await provider_registry.load_manifests(
            str(BASE_DIR / "integrations/**/provider.yml")
        )
        await provider_registry.load_manifests(
            str(BASE_DIR / "integrations/**/provider.json")
        )

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

    # Webhook events now handled directly by MessageRouter

    # Start services (check for start method for compatibility)
    # Start the domain event bus FIRST (before other services that depend on it)
    if domain_event_bus is not None and hasattr(domain_event_bus, "start"):
        await domain_event_bus.start()
    if hasattr(event_bus, "start"):
        await event_bus.start()
    if hasattr(state_manager, "initialize"):
        await state_manager.initialize()
    # StreamingMonitor removed - no startup needed
    if hasattr(metrics_observer, "start"):
        await metrics_observer.start()

    # Register CLI session service if not already registered
    from dipeo.application.execution.use_cases import CliSessionService

    if not container.registry.has(CLI_SESSION_SERVICE):
        container.registry.register(CLI_SESSION_SERVICE, CliSessionService())

    # Duplicate service keys have been removed in cleanup

    # Report unused services for DI cleanup
    import logging

    logger = logging.getLogger(__name__)
    unused = container.registry.report_unused()
    if unused:
        logger.info(
            f"🔎 Unused registrations this run ({len(unused)}): {', '.join(unused)}"
        )

    return container


def get_container() -> Container:
    if _container is None:
        raise RuntimeError(
            "Container not initialized. Call initialize_container() first."
        )
    return _container


def initialize_container() -> Container:
    global _container  # noqa: PLW0603

    if _container is None:
        # Initializing server with simplified container system
        # Run the async function in a new event loop if needed
        try:
            asyncio.get_running_loop()
            # If we're already in an event loop, this is an error
            raise RuntimeError(
                "initialize_container must be called before the event loop starts"
            )
        except RuntimeError:
            # No event loop running, create container synchronously
            _container = asyncio.run(create_server_container())

    return _container


async def initialize_container_async() -> Container:
    """Async version of initialize_container for use within async contexts."""
    global _container  # noqa: PLW0603

    if _container is None:
        # Initializing server with simplified container system
        _container = await create_server_container()

    return _container
