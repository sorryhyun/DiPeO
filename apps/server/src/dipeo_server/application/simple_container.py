"""Server container using the simplified 3-container architecture."""

from pathlib import Path

from dipeo.container import Container
from dipeo.core.config import Config, StorageConfig, LLMConfig
from dipeo_server.shared.constants import BASE_DIR


def create_server_container() -> Container:
    """Create a server container with appropriate configuration.
    
    This replaces the complex ServerContainer with a simple configuration-based approach.
    """
    # Server-specific configuration
    config = Config(
        base_dir=str(BASE_DIR),
        storage=StorageConfig(
            type="local",  # Can be overridden by env vars
            local_path=str(BASE_DIR / "files")
        ),
        llm=LLMConfig(
            provider="openai",
            default_model="gpt-4.1-nano"
        ),
        debug=True  # Enable debug mode for development
    )
    
    # Create container with server configuration
    container = Container(config)
    
    # Server-specific service overrides
    from dipeo.application.registry.keys import STATE_STORE, MESSAGE_ROUTER
    
    # Override state store with server implementation
    from dipeo_server.infra.state_registry import StateRegistry
    container.registry.register(STATE_STORE, StateRegistry())
    
    # Override message router with server implementation
    from dipeo.infra import MessageRouter
    container.registry.register(MESSAGE_ROUTER, MessageRouter())
    
    return container


# This container is used by app_context.py to initialize the server