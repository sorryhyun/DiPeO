"""Mutable services for persistence and storage."""

from dependency_injector import containers, providers
from ..base import MutableBaseContainer


def _create_file_service(base_dir, backup_service=None, domain_validator=None):
    """Create modular file service."""
    from dipeo.infra.persistence.file import ModularFileService
    from dipeo.domain.file.services import BackupService, FileValidator
    
    return ModularFileService(
        base_dir=base_dir,
        backup_service=backup_service or BackupService(),
        validator=domain_validator or FileValidator()
    )


def _create_api_key_storage(store_file=None):
    """Create API key storage implementation."""
    from dipeo.infra.persistence.keys.file_apikey_storage import FileAPIKeyStorage
    from pathlib import Path
    
    # Use provided file or default location
    if store_file is None:
        store_file = Path.home() / ".dipeo" / "apikeys.json"
    
    return FileAPIKeyStorage(file_path=Path(store_file))


def _create_api_key_service(storage):
    """Create API key service."""
    from dipeo.application.services.apikey_service import APIKeyService
    return APIKeyService(storage=storage)


def _create_diagram_storage_service(base_dir, diagram_domain_service):
    """Create diagram file repository."""
    from dipeo.infra.persistence.diagram import DiagramFileRepository
    return DiagramFileRepository(
        domain_service=diagram_domain_service,
        base_dir=base_dir
    )


def _create_diagram_storage_adapter(storage_service, diagram_domain_service):
    """Create diagram storage adapter."""
    from dipeo.infra.persistence.diagram import DiagramStorageAdapter
    
    return DiagramStorageAdapter(
        file_repository=storage_service,
        domain_service=diagram_domain_service
    )



def _create_diagram_loader(file_service):
    """Create diagram loader adapter."""
    from dipeo.infra.persistence.diagram.diagram_loader import DiagramLoaderAdapter
    return DiagramLoaderAdapter(file_service=file_service)


def _create_db_operations_service(file_service, db_validator):
    """Create database operations service."""
    from dipeo.infra.database import DBOperationsDomainService
    
    return DBOperationsDomainService(file_service, db_validator)


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
    
    # File system services
    file_service = providers.Singleton(
        _create_file_service,
        base_dir=base_dir,
        backup_service=business.backup_service,
        domain_validator=business.file_validator,
    )
    
    # API key management
    api_key_storage = providers.Singleton(
        _create_api_key_storage,
        store_file=config.api_key_store_file.optional(None),
    )
    
    api_key_service = providers.Singleton(
        _create_api_key_service,
        storage=api_key_storage,
    )
    
    # Diagram storage
    diagram_storage_service = providers.Singleton(
        _create_diagram_storage_service,
        base_dir=base_dir,
        diagram_domain_service=business.diagram_business_logic,
    )
    
    diagram_storage_adapter = providers.Singleton(
        _create_diagram_storage_adapter,
        storage_service=diagram_storage_service,
        diagram_domain_service=business.diagram_business_logic,
    )

    diagram_loader = providers.Singleton(
        _create_diagram_loader,
        file_service=file_service,
    )
    
    # Database operations
    db_operations_service = providers.Singleton(
        _create_db_operations_service,
        file_service=file_service,
        db_validator=business.db_validator,
    )
    
    # State management (must be overridden by server)
    state_store = providers.Singleton(_create_state_store)
    message_router = providers.Singleton(_create_message_router)
    
    # Conversation and person persistence (future)
    conversation_persistence = providers.Singleton(_create_conversation_persistence)
    person_persistence = providers.Singleton(_create_person_persistence)