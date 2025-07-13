"""Server-specific infrastructure container."""

from pathlib import Path

from dependency_injector import providers
from dipeo.container.infrastructure_container import InfrastructureContainer
from dipeo.infra import MessageRouter, NotionAPIService
from dipeo.infra.persistence.file import ModularFileService
from dipeo.infra.persistence.keys.file_apikey_storage import FileAPIKeyStorage
from dipeo_server.infra.persistence.state_registry import state_store
from dipeo_server.shared.constants import BASE_DIR


class ServerInfrastructureContainer(InfrastructureContainer):
    # Server-specific infrastructure container with proper overrides

    # Override state_store with server implementation
    state_store = providers.Singleton(lambda: state_store)

    # Override message_router with actual implementation
    message_router = providers.Singleton(MessageRouter)

    # Override file_service with server base directory
    file_service = providers.Singleton(
        ModularFileService,
        base_dir=providers.Factory(lambda: BASE_DIR),
    )

    # Override notion_service with actual implementation
    notion_service = providers.Singleton(NotionAPIService)

    # Override api_key_storage with server-specific path
    api_key_storage = providers.Singleton(
        FileAPIKeyStorage,
        file_path=providers.Factory(lambda: Path(BASE_DIR) / "files" / "apikeys.json"),
    )
