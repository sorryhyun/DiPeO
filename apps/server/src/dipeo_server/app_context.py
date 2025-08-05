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
    )

    # Create event bus
    from dipeo.infrastructure.events import AsyncEventBus

    event_bus = AsyncEventBus()
    container.registry.register(EVENT_BUS, event_bus)

    # Create state store (keep existing StateRegistry for now)
    from dipeo_server.infra.state_registry import StateRegistry

    state_store = StateRegistry()
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

    # Start services
    await event_bus.start()
    await state_manager.start()

    from dipeo.infrastructure.adapters.messaging import MessageRouter

    container.registry.register(MESSAGE_ROUTER, MessageRouter())

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
