"""Server-specific dependency injection container."""

from pathlib import Path
from dependency_injector import providers
from dipeo.container import Container as BaseContainer
from dipeo.container.utilities import init_resources, shutdown_resources
from dipeo.container.runtime.dynamic_container import DynamicServicesContainer
from dipeo.container.runtime.integration_container import IntegrationServicesContainer
from dipeo.container.core.static_container import StaticServicesContainer
from dipeo.container.application_container import ApplicationContainer

from dipeo_server.shared.constants import BASE_DIR
from dipeo_server.infra.persistence_container import ServerPersistenceContainer


class ServerContainer(BaseContainer):
    # Server-specific dependency injection container

    # Override base directory to use server-specific constant
    base_dir = providers.Factory(lambda: BASE_DIR)
    
    # Override persistence container with server-specific implementation
    persistence = providers.Container(
        ServerPersistenceContainer,
        config=BaseContainer.config,
        base_dir=base_dir,
        business=BaseContainer.business,
    )
    
    # Override integration container to use our persistence
    integration = providers.Container(
        IntegrationServicesContainer,  
        config=BaseContainer.config,
        base_dir=base_dir,
        business=BaseContainer.business,
        persistence=persistence,  # Use our overridden persistence with correct api_key_service
    )
    
    # Override static container to use our persistence  
    static = providers.Container(
        StaticServicesContainer,
        config=BaseContainer.config,
        persistence=persistence,  # Use our overridden persistence
    )
    
    # Need to recreate containers that depend on persistence
    # Dynamic container needs updated persistence
    dynamic = providers.Container(
        DynamicServicesContainer,
        config=BaseContainer.config,
        static=static,  # Use our overridden static
        business=BaseContainer.business,
        persistence=persistence,  # Use our overridden persistence
        integration=integration,  # Use our overridden integration
    )
    
    # Application container needs updated persistence and dynamic
    application = providers.Container(
        ApplicationContainer,
        config=BaseContainer.config,
        static=static,  # Use our overridden static
        business=BaseContainer.business,
        dynamic=dynamic,  # Use our updated dynamic
        persistence=persistence,  # Use our overridden persistence
        integration=integration,  # Use our overridden integration
    )


async def init_server_resources(container: ServerContainer) -> None:
    # Use the base container's init_resources utility
    await init_resources(container)


async def shutdown_server_resources(container: ServerContainer) -> None:
    # Use the base container's shutdown_resources utility
    await shutdown_resources(container)
