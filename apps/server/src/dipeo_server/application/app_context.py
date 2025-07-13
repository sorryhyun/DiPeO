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

        _container = ServerContainer()

        # Override specific providers in the persistence container
        from dependency_injector import providers
        from dipeo_server.infra.persistence_container import (
            _create_initialized_state_store,
            _create_server_api_key_storage,
        )
        from dipeo.infra import MessageRouter

        # Override specific providers instead of the whole container
        _container.persistence.state_store.override(
            providers.Singleton(_create_initialized_state_store)
        )
        _container.persistence.message_router.override(
            providers.Singleton(MessageRouter)
        )
        _container.persistence.api_key_storage.override(
            providers.Singleton(_create_server_api_key_storage)
        )

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
