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


# File service removed - use filesystem_adapter instead


def _create_server_filesystem_adapter():
    """Create filesystem adapter for basic file operations."""
    from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter

    # Use BASE_DIR as base, not files/ directory
    adapter = LocalFileSystemAdapter(base_path=str(BASE_DIR))
    return adapter


def _create_server_blob_adapter():
    """Create blob storage adapter for versioned storage."""
    from dipeo.infrastructure.adapters.storage import LocalBlobAdapter

    # Use blobs/ directory for versioned storage
    blobs_dir = Path(BASE_DIR) / "blobs"
    adapter = LocalBlobAdapter(base_path=str(blobs_dir))
    return adapter


def _create_server_artifact_adapter(blob_store):
    """Create artifact store adapter for high-level artifact management."""
    from dipeo.infrastructure.adapters.storage import ArtifactStoreAdapter

    return ArtifactStoreAdapter(blob_store=blob_store)


def _create_server_diagram_storage_adapter(filesystem_adapter):
    """Create diagram storage adapter with server-specific paths."""
    from dipeo.infrastructure.adapters.storage import DiagramStorageAdapter

    return DiagramStorageAdapter(
        filesystem=filesystem_adapter, base_path=Path(BASE_DIR) / "files" / "diagrams"
    )


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

    # File service removed - use filesystem_adapter instead

    # New storage adapters
    filesystem_adapter = providers.Singleton(_create_server_filesystem_adapter)
    blob_adapter = providers.Singleton(_create_server_blob_adapter)
    artifact_adapter = providers.Singleton(
        _create_server_artifact_adapter, blob_store=blob_adapter
    )

    # Override diagram_storage_adapter with server-specific configuration
    diagram_storage_adapter = providers.Singleton(
        _create_server_diagram_storage_adapter, filesystem_adapter=filesystem_adapter
    )
