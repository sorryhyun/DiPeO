"""Application context and dependency injection configuration."""

from .container import ServerContainer


# Global container instance
_container: ServerContainer | None = None


def get_container() -> ServerContainer:
    """Get the global DI container instance."""
    if _container is None:
        raise RuntimeError(
            "Container not initialized. Call initialize_container() first."
        )
    return _container


def initialize_container() -> ServerContainer:
    """Initialize the global DI container."""
    global _container

    if _container is None:
        _container = ServerContainer()
        # Configure from environment - no need to call from_env() for now
        # as we're using factory functions that handle env vars directly

        # Wire the container to necessary modules
        _container.wire(
            modules=[
                "dipeo_server.api.graphql.queries",
                "dipeo_server.api.graphql.mutations",
                "dipeo_server.api.graphql.subscriptions",
                "dipeo_server.api.graphql.resolvers",
                "dipeo.domain.services.execution",
            ]
        )

    return _container
