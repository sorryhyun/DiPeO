"""Server-specific dependency injection container."""

from dependency_injector import providers
from dipeo.container import Container as BaseContainer
from dipeo.container.utilities import init_resources, shutdown_resources

from dipeo_server.infra.persistence_container import ServerPersistenceContainer
from dipeo_server.shared.constants import BASE_DIR


# Create ServerContainer using the new with_overrides helper
# This automatically handles updating all dependent containers
ServerContainer = BaseContainer.with_overrides(
    # Override base directory to use server-specific constant
    base_dir=providers.Factory(lambda: BASE_DIR),
    
    # Override persistence container with server-specific implementation
    persistence=providers.Container(
        ServerPersistenceContainer,
        config=BaseContainer.config,
        base_dir=providers.Factory(lambda: BASE_DIR),
        business=BaseContainer.business,
    )
)


async def init_server_resources(container: ServerContainer) -> None:
    # Use the base container's init_resources utility
    await init_resources(container)


async def shutdown_server_resources(container: ServerContainer) -> None:
    # Use the base container's shutdown_resources utility
    await shutdown_resources(container)
