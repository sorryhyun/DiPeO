"""Application context and dependency injection configuration."""

import os
from .container import ServerContainer

# Global container instance
_container: ServerContainer | None = None


def get_container() -> ServerContainer:
    if _container is None:
        raise RuntimeError(
            "Container not initialized. Call initialize_container() first."
        )
    return _container


def initialize_container() -> ServerContainer:
    global _container

    if _container is None:
        # Set container profile based on environment variable
        profile = os.environ.get("DIPEO_CONTAINER_PROFILE", "full")
        ServerContainer.set_profile(profile)
        print(f"Initializing server with container profile: {profile}")

        # Create container - ServerContainer already uses ServerPersistenceContainer
        # which has the proper state_store, message_router, and api_key_storage overrides
        _container = ServerContainer()

        # Wire the container to necessary modules
        _container.wire(
            modules=[
                "dipeo_server.api.graphql.queries",
                "dipeo_server.api.graphql.mutations",
                "dipeo_server.api.graphql.subscriptions",
                "dipeo_server.api.graphql.resolvers",
            ]
        )

    return _container
