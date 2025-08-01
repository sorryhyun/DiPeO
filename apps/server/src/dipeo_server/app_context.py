"""Application context and dependency injection configuration."""


from dipeo.application.bootstrap import Container
from dipeo.core.config import Config, LLMConfig, StorageConfig

from dipeo_server.shared.constants import BASE_DIR

_container: Container | None = None


def create_server_container() -> Container:
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
        MESSAGE_ROUTER,
        STATE_STORE,
    )

    from dipeo_server.infra.state_registry import StateRegistry

    container.registry.register(STATE_STORE, StateRegistry())

    from dipeo.infra import MessageRouter

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
        _container = create_server_container()

    return _container
