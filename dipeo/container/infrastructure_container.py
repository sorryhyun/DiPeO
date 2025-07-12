"""Infrastructure layer container - External systems and I/O."""

import os
from dependency_injector import containers, providers


def _create_state_store_for_context():
    """Create state store - server must override this.
    
    This returns None as the base container doesn't provide
    a state store implementation. The server container must
    override this provider.
    """
    return None


def _create_message_router_for_context():
    """Create message router - server must override this.
    
    This returns None as the base container doesn't provide
    a message router implementation. The server container must
    override this provider.
    """
    return None


def _create_file_service(base_dir, backup_service=None, domain_validator=None):
    from dipeo.infra.persistence.file import ModularFileService
    from dipeo.domain.file.services import BackupService, FileValidator

    return ModularFileService(
        base_dir=base_dir,
        backup_service=backup_service or BackupService(),
        domain_validator=domain_validator or FileValidator()
    )


def _create_llm_service(api_key_service):
    from dipeo.infra.llm import LLMInfraService

    return LLMInfraService(api_key_service)


def _create_notion_service():
    # TODO: NotionAPIService not yet implemented in new structure
    # Return None for now as it's optional
    return None


def _create_api_service(api_business_logic, file_service):
    """Create infrastructure API service."""
    from dipeo.infra.services.api import APIService
    return APIService(
        business_logic=api_business_logic,
        file_service=file_service
    )




def _create_diagram_loader(file_service):
    """Create diagram loader adapter."""
    from dipeo.infra.persistence.diagram.diagram_loader import DiagramLoaderAdapter
    return DiagramLoaderAdapter(file_service=file_service)


def _create_integrated_diagram_service(diagram_business_logic, base_dir):
    """Create integrated diagram service with conversion capabilities."""
    from dipeo.infra.diagram.integrated_diagram_service import IntegratedDiagramService
    return IntegratedDiagramService(
        domain_service=diagram_business_logic,
        base_dir=base_dir
    )


def _create_api_key_storage(store_file=None):
    """Create API key storage implementation."""
    from dipeo.infra.persistence.keys.file_apikey_storage import FileAPIKeyStorage
    from pathlib import Path
    
    # Use provided file or default location
    if store_file is None:
        store_file = Path.home() / ".dipeo" / "apikeys.json"
    
    return FileAPIKeyStorage(file_path=Path(store_file))


class InfrastructureContainer(containers.DeclarativeContainer):
    """Infrastructure layer container - External systems and I/O."""
    
    config = providers.Configuration()
    base_dir = providers.Configuration()
    
    # Dependencies from other layers
    api_key_service = providers.Dependency()
    api_business_logic = providers.Dependency()
    file_business_logic = providers.Dependency()
    diagram_business_logic = providers.Dependency()
    
    # Core infrastructure
    state_store = providers.Singleton(_create_state_store_for_context)
    message_router = providers.Singleton(_create_message_router_for_context)
    file_service = providers.Singleton(
        _create_file_service,
        base_dir=base_dir,
    )
    notion_service = providers.Singleton(_create_notion_service)
    api_key_storage = providers.Singleton(
        _create_api_key_storage,
        store_file=config.api_key_store_file.optional(None),
    )
    
    # Infrastructure services that depend on domain services
    llm_service = providers.Singleton(
        _create_llm_service,
        api_key_service=api_key_service,
    )
    api_service = providers.Singleton(
        _create_api_service,
        api_business_logic=api_business_logic,
        file_service=file_service,
    )
    diagram_loader = providers.Singleton(
        _create_diagram_loader,
        file_service=file_service,
    )
    integrated_diagram_service = providers.Singleton(
        _create_integrated_diagram_service,
        diagram_business_logic=diagram_business_logic,
        base_dir=base_dir,
    )