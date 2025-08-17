"""Application context and dependency injection configuration."""

import asyncio

from dipeo.application.bootstrap import Container
from dipeo.core.bak.config import Config, LLMConfig, StorageConfig
from dipeo.core.bak.events import EventType

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
    from dipeo.application.wiring.port_v2_wiring import is_v2_enabled
    
    settings = get_settings()
    
    # Check if V2 messaging is enabled
    if is_v2_enabled("messaging"):
        # Use V2 domain ports wiring
        from dipeo.application.wiring.port_v2_wiring import wire_messaging_services
        from dipeo.application.registry.registry_tokens import MESSAGE_BUS
        
        # Wire V2 messaging services (includes MessageBus and optionally DomainEventBus)
        wire_messaging_services(container.registry)
        
        # Get the message bus from V2 wiring
        if container.registry.has(MESSAGE_BUS):
            message_router = container.registry.resolve(MESSAGE_BUS)
            # Also register as MESSAGE_ROUTER for backward compatibility
            container.registry.register(MESSAGE_ROUTER, message_router)
        else:
            # Fallback to direct creation if wiring failed
            from dipeo.infrastructure.adapters.messaging import MessageRouter
            message_router = MessageRouter()
            container.registry.register(MESSAGE_ROUTER, message_router)
    else:
        # Use V1 direct creation
        from dipeo.infrastructure.adapters.messaging import MessageRouter
        message_router = MessageRouter()
        container.registry.register(MESSAGE_ROUTER, message_router)
    
    # Check if V2 events are enabled
    if is_v2_enabled("events"):
        # Use V2 domain events wiring
        from dipeo.application.wiring.port_v2_wiring import wire_event_services
        from dipeo.application.registry.registry_tokens import DOMAIN_EVENT_BUS
        
        # Wire V2 event services
        wire_event_services(container.registry)
        
        # Get the domain event bus from V2 wiring
        if container.registry.has(DOMAIN_EVENT_BUS):
            # V2 uses domain event bus through adapters
            from dipeo.application.registry import ServiceKey
            event_bus = container.registry.resolve(ServiceKey("execution_observer"))  # ObserverToEventAdapter
        else:
            # Fallback to AsyncEventBus
            from dipeo.infrastructure.adapters.events import AsyncEventBus
            event_bus = AsyncEventBus(queue_size=settings.event_queue_size)
            container.registry.register(EVENT_BUS, event_bus)
    else:
        # Use V1 direct creation
        from dipeo.infrastructure.adapters.events import AsyncEventBus
        event_bus = AsyncEventBus(queue_size=settings.event_queue_size)
        container.registry.register(EVENT_BUS, event_bus)

    # Check if V2 state is enabled
    if is_v2_enabled("state"):
        # Use V2 domain ports wiring
        from dipeo.application.wiring.port_v2_wiring import wire_state_services
        from dipeo.application.registry.registry_tokens import STATE_REPOSITORY, STATE_SERVICE, STATE_CACHE
        
        # Wire V2 state services (includes repository, service, and cache)
        wire_state_services(container.registry, redis_client=None)  # No Redis for now
        
        # Get the state repository for state manager
        state_store = container.registry.resolve(STATE_REPOSITORY)
        
        # Initialize if needed
        if hasattr(state_store, 'initialize'):
            await state_store.initialize()
            
        # Also register as STATE_STORE for backward compatibility
        container.registry.register(STATE_STORE, state_store)
    else:
        # Use V1 direct creation
        from dipeo.infrastructure.state import EventBasedStateStore
        
        state_store = EventBasedStateStore()
        await state_store.initialize()
        container.registry.register(STATE_STORE, state_store)

    # Create state manager as separate service
    from dipeo.infrastructure.state import AsyncStateManager

    state_manager = AsyncStateManager(state_store)

    # Subscribe state manager to relevant events (works with both V1 and V2)
    if hasattr(event_bus, 'subscribe'):
        event_bus.subscribe(EventType.EXECUTION_STARTED, state_manager)
        event_bus.subscribe(EventType.NODE_STARTED, state_manager)
        event_bus.subscribe(EventType.NODE_COMPLETED, state_manager)
        event_bus.subscribe(EventType.NODE_FAILED, state_manager)
        event_bus.subscribe(EventType.EXECUTION_COMPLETED, state_manager)

    # Create streaming monitor for real-time UI updates
    from dipeo.infrastructure.monitoring import StreamingMonitor
    streaming_monitor = StreamingMonitor(message_router, queue_size=settings.monitoring_queue_size)

    # Subscribe streaming monitor to all events (works with both V1 and V2)
    if hasattr(event_bus, 'subscribe'):
        event_bus.subscribe(EventType.EXECUTION_STARTED, streaming_monitor)
        event_bus.subscribe(EventType.NODE_STARTED, streaming_monitor)
        event_bus.subscribe(EventType.NODE_COMPLETED, streaming_monitor)
        event_bus.subscribe(EventType.NODE_FAILED, streaming_monitor)
        event_bus.subscribe(EventType.EXECUTION_COMPLETED, streaming_monitor)
        event_bus.subscribe(EventType.METRICS_COLLECTED, streaming_monitor)

    # Create metrics observer for performance analysis
    from dipeo.application.execution.observers import MetricsObserver
    
    # For V2, we might need to get the actual event bus from the registry
    actual_event_bus = event_bus
    if is_v2_enabled("events") and container.registry.has(EVENT_BUS):
        # Try to get the actual AsyncEventBus if it's registered
        try:
            actual_event_bus = container.registry.resolve(EVENT_BUS)
        except:
            pass  # Use the adapter if resolution fails
    
    metrics_observer = MetricsObserver(event_bus=actual_event_bus)

    # Subscribe metrics observer to execution events (works with both V1 and V2)
    if hasattr(event_bus, 'subscribe'):
        event_bus.subscribe(EventType.EXECUTION_STARTED, metrics_observer)
        event_bus.subscribe(EventType.NODE_STARTED, metrics_observer)
        event_bus.subscribe(EventType.NODE_COMPLETED, metrics_observer)
        event_bus.subscribe(EventType.NODE_FAILED, metrics_observer)
        event_bus.subscribe(EventType.EXECUTION_COMPLETED, metrics_observer)

    # Initialize provider registry for webhook integration
    from dipeo.infrastructure.services.integrated_api.registry import ProviderRegistry
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
    
    # Subscribe webhook events to streaming monitor (works with both V1 and V2)
    if hasattr(event_bus, 'subscribe'):
        event_bus.subscribe(EventType.WEBHOOK_RECEIVED, streaming_monitor)

    # Start services (check for start method for compatibility)
    if hasattr(event_bus, 'start'):
        await event_bus.start()
    if hasattr(state_manager, 'start'):
        await state_manager.start()
    if hasattr(streaming_monitor, 'start'):
        await streaming_monitor.start()
    if hasattr(metrics_observer, 'start'):
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
