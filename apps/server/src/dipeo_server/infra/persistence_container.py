"""Server-specific persistence container with state store and message router."""

from pathlib import Path

from dependency_injector import providers
from dipeo.container.runtime.persistence_container import PersistenceServicesContainer
from dipeo.infra import MessageRouter
from dipeo.infra.persistence.keys.file_apikey_storage import FileAPIKeyStorage

from dipeo_server.shared.constants import BASE_DIR


def _create_initialized_state_store():
    """Create and initialize the state store."""
    # Import the class instead of the singleton instance
    from dipeo_server.infra.persistence.state_registry import StateRegistry
    # Create a new instance that will be initialized by init_resources
    return StateRegistry()


def _create_server_api_key_storage():
    """Create API key storage with server-specific path."""
    file_path = Path(BASE_DIR) / "files" / "apikeys.json"
    return FileAPIKeyStorage(file_path=file_path)


def _create_server_api_key_service():
    """Create API key service with server-specific storage."""
    from dipeo.application.services.apikey_service import APIKeyService
    storage = _create_server_api_key_storage()
    return APIKeyService(storage=storage)


class ServerPersistenceContainer(PersistenceServicesContainer):
    """Server-specific persistence container with proper overrides."""

    # Override state_store with server implementation
    state_store = providers.Singleton(_create_initialized_state_store)

    # Override message_router with actual implementation
    message_router = providers.Singleton(MessageRouter)

    # Override api_key_storage with server-specific path
    api_key_storage = providers.Singleton(_create_server_api_key_storage)

    # Override api_key_service to use our storage
    api_key_service = providers.Singleton(_create_server_api_key_service)
