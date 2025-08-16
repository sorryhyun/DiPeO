"""Application context and dependency injection configuration."""

import asyncio

from dipeo.application.bootstrap import Container
from dipeo.core.config import Config, LLMConfig, StorageConfig
from dipeo.core.events import EventType

from dipeo_server.shared.constants import BASE_DIR

_container: Container | None = None


async def create_server_container() -> Container:
    """Create a server container with appropriate configuration.

    This replaces the complex ServerContainer with a simple configuration-based approach.
    """
    config = Config(
        base_dir=str(BASE_DIR),
        storage=StorageConfig(
            type="local",
            local_path=str(BASE_DIR / "files"),
        ),
        llm=LLMConfig(provider="openai", default_model="gpt-4.1-nano"),
        debug=True,
    )

    container = Container(config)
    from dipeo.application.registry.keys import (
        CLI_SESSION_SERVICE,
        EVENT_BUS,
        MESSAGE_ROUTER,
        STATE_STORE,
        PROVIDER_REGISTRY,
        INTEGRATED_API_SERVICE,
    )
    from dipeo.infrastructure.config import get_settings
    from dipeo.infrastructure.events import AsyncEventBus

    # Create event bus with configuration

    settings = get_settings()
    event_bus = AsyncEventBus(queue_size=settings.event_queue_size)
    container.registry.register(EVENT_BUS, event_bus)

    # Create event-based state store (no global lock)
    from dipeo.infrastructure.state import EventBasedStateStore

    state_store = EventBasedStateStore()
    await state_store.initialize()
    container.registry.register(STATE_STORE, state_store)

    # Create state manager as separate service
    from dipeo.infrastructure.state import AsyncStateManager

    state_manager = AsyncStateManager(state_store)

    # Subscribe state manager to relevant events
    event_bus.subscribe(EventType.EXECUTION_STARTED, state_manager)
    event_bus.subscribe(EventType.NODE_STARTED, state_manager)
    event_bus.subscribe(EventType.NODE_COMPLETED, state_manager)
    event_bus.subscribe(EventType.NODE_FAILED, state_manager)
    event_bus.subscribe(EventType.EXECUTION_COMPLETED, state_manager)

    # Create message router for real-time updates
    from dipeo.infrastructure.adapters.messaging import MessageRouter
    message_router = MessageRouter()
    container.registry.register(MESSAGE_ROUTER, message_router)

    # Create streaming monitor for real-time UI updates
    from dipeo.infrastructure.monitoring import StreamingMonitor
    streaming_monitor = StreamingMonitor(message_router, queue_size=settings.monitoring_queue_size)

    # Subscribe streaming monitor to all events
    event_bus.subscribe(EventType.EXECUTION_STARTED, streaming_monitor)
    event_bus.subscribe(EventType.NODE_STARTED, streaming_monitor)
    event_bus.subscribe(EventType.NODE_COMPLETED, streaming_monitor)
    event_bus.subscribe(EventType.NODE_FAILED, streaming_monitor)
    event_bus.subscribe(EventType.EXECUTION_COMPLETED, streaming_monitor)
    event_bus.subscribe(EventType.METRICS_COLLECTED, streaming_monitor)

    # Create metrics observer for performance analysis
    from dipeo.application.execution.observers import MetricsObserver
    metrics_observer = MetricsObserver(event_bus=event_bus)

    # Subscribe metrics observer to execution events
    event_bus.subscribe(EventType.EXECUTION_STARTED, metrics_observer)
    event_bus.subscribe(EventType.NODE_STARTED, metrics_observer)
    event_bus.subscribe(EventType.NODE_COMPLETED, metrics_observer)
    event_bus.subscribe(EventType.NODE_FAILED, metrics_observer)
    event_bus.subscribe(EventType.EXECUTION_COMPLETED, metrics_observer)

    # Initialize provider registry for webhook integration
    from dipeo.infrastructure.services.integrated_api.registry import ProviderRegistry
    provider_registry = ProviderRegistry()
    
    # Load providers from manifests
    try:
        import glob
        manifest_pattern = str(BASE_DIR / "integrations" / "*" / "provider.yaml")
        for manifest_path in glob.glob(manifest_pattern):
            await provider_registry.load_manifest(manifest_path)
    except Exception as e:
        # Log but don't fail if no providers found
        import logging
        logging.getLogger(__name__).warning(f"Failed to load provider manifests: {e}")
    
    container.registry.register(PROVIDER_REGISTRY, provider_registry)
    
    # Subscribe webhook events to streaming monitor
    event_bus.subscribe(EventType.WEBHOOK_RECEIVED, streaming_monitor)

    # Start services
    await event_bus.start()
    await state_manager.start()
    await streaming_monitor.start()
    await metrics_observer.start()


    # Register CLI session service if not already registered
    from dipeo.application.services.cli_session_service import CliSessionService

    if not container.registry.has(CLI_SESSION_SERVICE):
        container.registry.register(CLI_SESSION_SERVICE, CliSessionService())

    return container


def get_container() -> Container:
    if _container is None:
        raise RuntimeError(
            "Container not initialized. Call initialize_container() first."
        )
    return _container


def initialize_container() -> Container:
    global _container

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
    global _container

    if _container is None:
        # Initializing server with simplified container system
        _container = await create_server_container()

    return _container
