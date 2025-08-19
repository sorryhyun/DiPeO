"""Application context and dependency injection configuration."""

import asyncio
import os

from dipeo.application.bootstrap import Container
from dipeo.config import get_settings
from dipeo.domain.events import EventType

from dipeo_server.shared.constants import BASE_DIR

_container: Container | None = None


async def create_server_container() -> Container:
    """Create a server container with appropriate configuration.

    This replaces the complex ServerContainer with a simple configuration-based approach.
    """
    # Get unified settings
    settings = get_settings()
    
    # Create container with unified settings
    container = Container(settings)
    from dipeo.application.registry.keys import (
        CLI_SESSION_SERVICE,
        EVENT_BUS,
        MESSAGE_ROUTER,
        STATE_STORE,
        PROVIDER_REGISTRY,
        INTEGRATED_API_SERVICE,
    )
    # Check if we should use minimal wiring for faster startup
    use_minimal_wiring = os.getenv("DIPEO_MINIMAL_WIRING", "").lower() in ("1", "true", "yes")
    
    if use_minimal_wiring:
        # Use minimal wiring for thin startup
        from dipeo.application.bootstrap.wiring_minimal import wire_minimal, wire_feature_flags
        
        # Wire only essential services
        wire_minimal(container.registry, redis_client=None)
        
        # Wire optional features if specified
        features = os.getenv("DIPEO_FEATURES", "").split(",") if os.getenv("DIPEO_FEATURES") else []
        if features:
            wire_feature_flags(container.registry, [f.strip() for f in features if f.strip()])
        
        # Still need messaging services for server operation
        from dipeo.application.bootstrap.wiring import wire_messaging_services
        wire_messaging_services(container.registry)
    else:
        # Use full wiring (existing behavior)
        from dipeo.application.bootstrap.wiring import wire_messaging_services
        
        # Wire messaging services
        wire_messaging_services(container.registry)
    from dipeo.application.registry.keys import MESSAGE_BUS
    
    # Get the message bus from wiring
    if container.registry.has(MESSAGE_BUS):
        message_bus = container.registry.resolve(MESSAGE_BUS)
        # Extract the actual MessageRouter from the adapter
        from dipeo.infrastructure.execution.messaging.messaging_adapter import MessageBusAdapter
        if isinstance(message_bus, MessageBusAdapter):
            message_router = message_bus._router
        else:
            message_router = message_bus
        # Also register as MESSAGE_ROUTER for backward compatibility
        container.registry.register(MESSAGE_ROUTER, message_router)
    else:
        # Fallback to direct creation if wiring failed
        from dipeo.infrastructure.execution.messaging import MessageRouter
        message_router = MessageRouter()
        container.registry.register(MESSAGE_ROUTER, message_router)
    
    # Wire event services (if not already done by minimal wiring)
    if not use_minimal_wiring:
        from dipeo.application.bootstrap.wiring import wire_event_services
        wire_event_services(container.registry)
    
    from dipeo.application.registry.keys import DOMAIN_EVENT_BUS
    
    # Get the domain event bus from wiring
    domain_event_bus = None
    if container.registry.has(DOMAIN_EVENT_BUS):
        # Use the new DomainEventBus directly
        domain_event_bus = container.registry.resolve(DOMAIN_EVENT_BUS)
        # Uses domain event bus through adapters for backward compatibility
        from dipeo.application.registry import ServiceKey
        event_bus = container.registry.resolve(ServiceKey("execution_observer"))  # ObserverToEventAdapter
    else:
        # Fallback to InMemoryEventBus (use canonical location)
        from dipeo.infrastructure.events.adapters import InMemoryEventBus
        # Use unified config for queue size (use a reasonable default)
        queue_size = getattr(settings.messaging, 'queue_size', 50000)
        event_bus = InMemoryEventBus(max_queue_size=queue_size)
        container.registry.register(EVENT_BUS, event_bus)

    # Wire state services (if not already done by minimal wiring)
    if not use_minimal_wiring:
        from dipeo.application.bootstrap.wiring import wire_state_services
        wire_state_services(container.registry, redis_client=None)  # No Redis for now
    
    from dipeo.application.registry.keys import STATE_REPOSITORY, STATE_SERVICE, STATE_CACHE
    
    # Get the state repository for state manager
    state_store = container.registry.resolve(STATE_REPOSITORY)
    
    # Initialize if needed
    if hasattr(state_store, 'initialize'):
        await state_store.initialize()
        
    # Also register as STATE_STORE for backward compatibility
    container.registry.register(STATE_STORE, state_store)

    # Create state manager as separate service
    from dipeo.infrastructure.execution.state import AsyncStateManager

    state_manager = AsyncStateManager(state_store)

    # Subscribe state manager to relevant events (works with both V1 and V2)
    if hasattr(event_bus, 'subscribe'):
        event_bus.subscribe(EventType.EXECUTION_STARTED, state_manager)
        event_bus.subscribe(EventType.NODE_STARTED, state_manager)
        event_bus.subscribe(EventType.NODE_COMPLETED, state_manager)
        event_bus.subscribe(EventType.NODE_ERROR, state_manager)
        event_bus.subscribe(EventType.EXECUTION_COMPLETED, state_manager)

    # Create streaming monitor for real-time UI updates
    from dipeo.infrastructure.execution.monitoring import StreamingMonitor
    # Use unified config for monitoring queue size (use a reasonable default)
    monitoring_queue_size = getattr(settings.messaging, 'monitoring_queue_size', 50000)
    streaming_monitor = StreamingMonitor(message_router, queue_size=monitoring_queue_size)
    
    # Initialize MessageRouter before wiring
    await message_router.initialize()
    
    # Wire MessageRouter as EventHandler to DomainEventBus (Phase 1 refactoring)
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
            EventType.METRICS_COLLECTED,
            EventType.WEBHOOK_RECEIVED,
        ]
        
        # Subscribe router to domain event bus with normal priority
        await domain_event_bus.subscribe(
            event_types=ui_event_types,
            handler=message_router,
            priority=EventPriority.NORMAL
        )

    # Subscribe streaming monitor to all events (works with both V1 and V2)
    if hasattr(event_bus, 'subscribe'):
        event_bus.subscribe(EventType.EXECUTION_STARTED, streaming_monitor)
        event_bus.subscribe(EventType.NODE_STARTED, streaming_monitor)
        event_bus.subscribe(EventType.NODE_COMPLETED, streaming_monitor)
        event_bus.subscribe(EventType.NODE_ERROR, streaming_monitor)
        event_bus.subscribe(EventType.EXECUTION_COMPLETED, streaming_monitor)
        event_bus.subscribe(EventType.METRICS_COLLECTED, streaming_monitor)

    # Create metrics observer for performance analysis
    from dipeo.application.execution.observers import MetricsObserver
    
    # Get the actual event bus from the registry if available
    actual_event_bus = event_bus
    if container.registry.has(EVENT_BUS):
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
        event_bus.subscribe(EventType.NODE_ERROR, metrics_observer)
        event_bus.subscribe(EventType.EXECUTION_COMPLETED, metrics_observer)

    # Initialize provider registry for webhook integration
    from dipeo.infrastructure.integrations.drivers.integrated_api.registry import ProviderRegistry
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
    # Start the domain event bus FIRST (before other services that depend on it)
    if domain_event_bus is not None and hasattr(domain_event_bus, 'start'):
        await domain_event_bus.start()
    if hasattr(event_bus, 'start'):
        await event_bus.start()
    if hasattr(state_manager, 'start'):
        await state_manager.start()
    if hasattr(streaming_monitor, 'start'):
        await streaming_monitor.start()
    if hasattr(metrics_observer, 'start'):
        await metrics_observer.start()


    # Register CLI session service if not already registered
    from dipeo.application.execution.use_cases import CliSessionService

    if not container.registry.has(CLI_SESSION_SERVICE):
        container.registry.register(CLI_SESSION_SERVICE, CliSessionService())

    # Consolidate duplicate service keys for backward compatibility
    from dipeo.application.registry.keys import consolidate_duplicate_keys
    consolidate_duplicate_keys(container.registry)
    
    # Report unused services for DI cleanup
    import logging
    logger = logging.getLogger(__name__)
    unused = container.registry.report_unused()
    if unused:
        logger.info(f"🔎 Unused registrations this run ({len(unused)}): {', '.join(unused)}")

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
