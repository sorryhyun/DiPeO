"""Server-specific persistence container with state store and message router."""

from pathlib import Path
from dependency_injector import providers
from dipeo.container.runtime.persistence_container import PersistenceServicesContainer
from dipeo.infra import MessageRouter
from dipeo.infra.persistence.keys.file_apikey_storage import FileAPIKeyStorage
from dipeo_server.infra.persistence.state_registry import state_store
from dipeo_server.shared.constants import BASE_DIR


def _create_initialized_state_store():
    """Create and initialize the state store."""
    return state_store


def _create_server_api_key_storage():
    """Create API key storage with server-specific path."""
    file_path = Path(BASE_DIR) / "files" / "apikeys.json"
    return FileAPIKeyStorage(file_path=file_path)


class ServerPersistenceContainer(PersistenceServicesContainer):
    """Server-specific persistence container with proper overrides."""

    # Override state_store with server implementation
    state_store = providers.Singleton(_create_initialized_state_store)

    # Override message_router with actual implementation
    message_router = providers.Singleton(MessageRouter)
    
    # Override api_key_storage with server-specific path
    api_key_storage = providers.Singleton(_create_server_api_key_storage)
