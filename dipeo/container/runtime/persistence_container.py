"""Mutable services for persistence and storage."""

from dependency_injector import providers

from ..base import MutableBaseContainer


# File service removed - use filesystem_adapter instead


def _create_api_key_storage(store_file=None):
    """Create API key storage implementation."""
    from pathlib import Path

    from dipeo.infra.persistence.keys.file_apikey_storage import FileAPIKeyStorage
    
    # Use provided file or default location
    if store_file is None:
        store_file = Path.home() / ".dipeo" / "apikeys.json"
    
    return FileAPIKeyStorage(file_path=Path(store_file))


def _create_api_key_service(storage):
    """Create API key service."""
    from dipeo.application.services.apikey_service import APIKeyService
    return APIKeyService(storage=storage)


def _create_diagram_storage_service(base_dir, diagram_domain_service):
    """Create diagram service - legacy compatibility wrapper."""
    # This is kept for backward compatibility but returns None
    # The actual diagram service is now created separately
    return None


def _create_diagram_storage_adapter(filesystem_adapter, base_dir):
    """Create diagram storage adapter with format awareness."""
    from pathlib import Path
    from dipeo.infrastructure.adapters.storage import DiagramStorageAdapter
    
    # Ensure base_dir is a Path object
    base_path = Path(base_dir)
    
    return DiagramStorageAdapter(
        filesystem=filesystem_adapter,
        base_path=base_path / "files"
    )



def _create_diagram_loader():
    """Create diagram converter service."""
    from dipeo.infrastructure.services.diagram import DiagramConverterService
    return DiagramConverterService()


def _create_db_operations_service(filesystem_adapter, db_validator):
    """Create database operations service."""
    from dipeo.infra.database import DBOperationsDomainService
    
    return DBOperationsDomainService(filesystem_adapter, db_validator)


def _create_state_store():
    """Create state store - server must override this.
    
    This returns None as the base container doesn't provide
    a state store implementation. The server container must
    override this provider.
    """
    return None


def _create_message_router():
    """Create message router - server must override this.
    
    This returns None as the base container doesn't provide
    a message router implementation. The server container must
    override this provider.
    """
    return None


def _create_conversation_persistence():
    """Create conversation persistence service."""
    # TODO: Implement when conversation persistence is added
    return None


def _create_person_persistence():
    """Create person persistence service."""
    # TODO: Implement when person persistence is added  
    return None


def _create_filesystem_adapter(base_dir):
    """Create filesystem adapter for basic file operations."""
    from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter
    
    # Use base_dir as the root for filesystem operations
    adapter = LocalFileSystemAdapter(base_path=base_dir)
    return adapter


def _create_blob_adapter():
    """Create blob storage adapter - must be overridden by implementation."""
    return None


def _create_artifact_adapter():
    """Create artifact storage adapter - must be overridden by implementation."""
    return None


def _create_diagram_service(diagram_storage_adapter, diagram_converter):
    """Create high-level diagram service."""
    from dipeo.infrastructure.services.diagram import DiagramService
    
    return DiagramService(
        storage=diagram_storage_adapter,
        converter=diagram_converter
    )


class PersistenceServicesContainer(MutableBaseContainer):
    """Mutable services for storage, repositories, and persistence.
    
    These services handle I/O operations and maintain state across
    executions. They should be carefully managed to ensure data
    consistency and proper resource cleanup.
    """
    
    config = providers.Configuration()
    base_dir = providers.Configuration()
    
    # Dependencies from other containers
    business = providers.DependenciesContainer()
    
    # File service removed - use filesystem_adapter instead
    
    # API key management
    api_key_storage = providers.Singleton(
        _create_api_key_storage,
        store_file=config.api_key_store_file.optional(None),
    )
    
    api_key_service = providers.Singleton(
        _create_api_key_service,
        storage=api_key_storage,
    )
    
    # Storage adapters
    filesystem_adapter = providers.Singleton(
        _create_filesystem_adapter,
        base_dir=base_dir
    )
    
    # Diagram storage adapter
    diagram_storage_adapter = providers.Singleton(
        _create_diagram_storage_adapter,
        filesystem_adapter=filesystem_adapter,
        base_dir=base_dir,
    )
    
    # Diagram storage service - alias for backward compatibility
    # Points to diagram_storage_adapter for code expecting the old service name
    # We'll use a factory that just returns the diagram_storage_adapter
    diagram_storage_service = providers.Factory(
        lambda adapter: adapter,
        adapter=diagram_storage_adapter
    )

    diagram_loader = providers.Singleton(
        _create_diagram_loader,
    )
    
    # Database operations
    db_operations_service = providers.Singleton(
        _create_db_operations_service,
        filesystem_adapter=filesystem_adapter,
        db_validator=business.db_validator,
    )
    
    # State management (must be overridden by server)
    state_store = providers.Singleton(_create_state_store)
    message_router = providers.Singleton(_create_message_router)
    
    # Conversation and person persistence (future)
    conversation_persistence = providers.Singleton(_create_conversation_persistence)
    person_persistence = providers.Singleton(_create_person_persistence)
    
    # New storage adapters (must be overridden by implementation)
    blob_adapter = providers.Singleton(_create_blob_adapter)
    artifact_adapter = providers.Singleton(_create_artifact_adapter)
    
    # Diagram services
    diagram_converter = providers.Singleton(
        _create_diagram_loader,  # Using the converter function
    )
    
    diagram_service = providers.Singleton(
        _create_diagram_service,
        diagram_storage_adapter=diagram_storage_adapter,
        diagram_converter=diagram_converter,
    )