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
        profile = os.environ.get('DIPEO_CONTAINER_PROFILE', 'full')
        ServerContainer.set_profile(profile)
        print(f"Initializing server with container profile: {profile}")
        
        _container = ServerContainer()

        # Override the persistence container with server-specific implementation
        from dependency_injector import providers

        from dipeo_server.infra.persistence_container import ServerPersistenceContainer

        _container.persistence.override(
            providers.Container(
                ServerPersistenceContainer,
                config=_container.config,
                base_dir=_container.base_dir,
                business=_container.business,
            )
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
