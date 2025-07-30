"""Simplified server container using the new 3-container architecture.

Enable with: export DIPEO_USE_SIMPLE_CONTAINERS=true
"""

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
    
    # Server-specific service overrides can be added here
    # For example, if the server needs a different state store:
    # from dipeo_server.infra.state_store import ServerStateStore
    # container.registry.register(STATE_STORE, ServerStateStore())
    
    return container


# Usage in app_context.py:
# if USE_SIMPLE_CONTAINERS:
#     _container = create_server_container()
# else:
#     _container = ServerContainer()  # Legacy