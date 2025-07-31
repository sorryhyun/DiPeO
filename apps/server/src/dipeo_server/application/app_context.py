"""Application context and dependency injection configuration."""

from dipeo.container import Container
from .simple_container import create_server_container

# Global container instance
_container: Container | None = None


def get_container() -> Container:
    if _container is None:
        raise RuntimeError(
            "Container not initialized. Call initialize_container() first."
        )
    return _container


def initialize_container() -> Container:
    global _container

    if _container is None:
        # Use new simplified container system
        print("Initializing server with simplified container system")
        _container = create_server_container()

    return _container
