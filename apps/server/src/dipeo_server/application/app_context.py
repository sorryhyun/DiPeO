"""Application context and dependency injection configuration."""

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
        _container = ServerContainer()

        # Override the infrastructure container with server-specific implementation
        from dependency_injector import providers

        from dipeo_server.infra.container import ServerInfrastructureContainer

        _container.infra.override(
            providers.Container(
                ServerInfrastructureContainer,
                config=_container.config,
                base_dir=_container.base_dir,
                api_key_service=_container.domain.api_key_service,
                api_business_logic=_container.domain.api_business_logic,
                file_business_logic=_container.domain.file_business_logic,
                diagram_business_logic=_container.domain.diagram_business_logic,
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
