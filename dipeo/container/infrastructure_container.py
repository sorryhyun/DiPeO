"""Infrastructure layer container - External systems and I/O."""

import os
from dependency_injector import containers, providers
from dipeo.core.ports import (
    DiagramLoaderPort,
    FileServicePort,
    LLMServicePort,
    NotionServicePort,
)


def _create_state_store_for_context():
    """Create appropriate state store based on execution context.
    
    This factory method determines whether we're running in a server
    or CLI context and returns the appropriate state store implementation.
    """
    # Check if we're in a server context by looking for server-specific env vars
    # or by attempting to import server modules
    is_server_context = os.environ.get("DIPEO_CONTEXT") == "server"
    
    if is_server_context:
        try:
            from dipeo_server.infra.persistence import state_store
            return state_store
        except ImportError:
            # Fallback if server modules aren't available
            pass
    
    # Return minimal implementation for CLI/local usage
    from dipeo.application.services.minimal_state_store import MinimalStateStore
    return MinimalStateStore()


def _create_message_router_for_context():
    """Create appropriate message router based on execution context.
    
    This factory method determines whether we're running in a server
    or CLI context and returns the appropriate message router implementation.
    """
    # Check if we're in a server context
    is_server_context = os.environ.get("DIPEO_CONTEXT") == "server"
    
    if is_server_context:
        try:
            from dipeo_server.infra.messaging import message_router
            return message_router
        except ImportError:
            # Fallback if server modules aren't available
            pass
    
    # Return minimal implementation for CLI/local usage
    from dipeo.application.services.minimal_message_router import MinimalMessageRouter
    return MinimalMessageRouter()


def _create_file_service(base_dir):
    from dipeo.infra.persistence.file import ModularFileService

    return ModularFileService(base_dir=base_dir)


def _create_memory_service():
    from dipeo.infra.persistence.memory import InMemoryConversationStore
    
    return InMemoryConversationStore()


def _create_llm_service(api_key_service):
    from dipeo.infra.adapters.llm import LLMInfraService

    return LLMInfraService(api_key_service)


def _create_notion_service():
    # TODO: NotionAPIService not yet implemented in new structure
    # Return None for now as it's optional
    return None


def _create_api_service(api_domain_service, file_service):
    """Create infrastructure API service."""
    from dipeo.infra.services.api import APIService
    return APIService(
        domain_service=api_domain_service,
        file_service=file_service
    )


def _create_file_operations_infra_service(file_domain_service):
    """Create infrastructure file operations service."""
    from dipeo.infra.services.file import FileOperationsService
    return FileOperationsService(domain_service=file_domain_service)


def _create_diagram_loader(file_service):
    """Create diagram loader adapter."""
    from dipeo.infra.persistence.diagram.diagram_loader import DiagramLoaderAdapter
    return DiagramLoaderAdapter(file_service=file_service)


class InfrastructureContainer(containers.DeclarativeContainer):
    """Infrastructure layer container - External systems and I/O."""
    
    config = providers.Configuration()
    base_dir = providers.Configuration()
    
    # Dependencies from other layers
    api_key_service = providers.Dependency()
    api_domain_service = providers.Dependency()
    file_domain_service = providers.Dependency()
    
    # Core infrastructure
    state_store = providers.Singleton(_create_state_store_for_context)
    message_router = providers.Singleton(_create_message_router_for_context)
    file_service = providers.Singleton(
        _create_file_service,
        base_dir=base_dir,
    )
    memory_service = providers.Singleton(_create_memory_service)
    notion_service = providers.Singleton(_create_notion_service)
    
    # Infrastructure services that depend on domain services
    llm_service = providers.Singleton(
        _create_llm_service,
        api_key_service=api_key_service,
    )
    api_service = providers.Singleton(
        _create_api_service,
        api_domain_service=api_domain_service,
        file_service=file_service,
    )
    file_operations_service = providers.Singleton(
        _create_file_operations_infra_service,
        file_domain_service=file_domain_service,
    )
    diagram_loader = providers.Singleton(
        _create_diagram_loader,
        file_service=file_service,
    )