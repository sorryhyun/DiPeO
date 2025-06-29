"""Dependency Injection Container for DiPeO applications."""

import os
from pathlib import Path

from dependency_injector import containers, providers
from dipeo_core import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)

from .app_context_adapter import AppContextAdapter


def _get_project_base_dir():
    """Get the project base directory."""
    # Try to import from config if available
    try:
        from config import BASE_DIR
        return BASE_DIR
    except ImportError:
        # Fall back to finding the project root
        # This file is in packages/python/dipeo_container/src/dipeo_container/
        # Project root is 5 levels up
        return Path(__file__).resolve().parents[5]


def _import_state_store():
    """Lazy import to avoid circular dependencies."""
    from dipeo_server.infrastructure.persistence import state_store
    return state_store


def _import_message_router():
    """Lazy import to avoid circular dependencies."""
    from dipeo_server.infrastructure.messaging import message_router
    return message_router


def _create_api_key_service():
    """Factory for APIKeyDomainService."""
    from dipeo_server.domains.apikey import APIKeyDomainService
    return APIKeyDomainService()


def _create_file_service(base_dir):
    """Factory for FileService."""
    from dipeo_server.infrastructure.persistence import FileService
    return FileService(base_dir=base_dir)


def _create_conversation_service():
    """Factory for ConversationService."""
    from dipeo_server.domains.conversation import ConversationService
    return ConversationService()


def _create_llm_service(api_key_service):
    """Factory for LLMService."""
    from dipeo_server.infrastructure.external.llm import LLMServiceClass
    return LLMServiceClass(api_key_service)


def _create_notion_service():
    """Factory for NotionService."""
    from dipeo_server.infrastructure.external.integrations import NotionService
    return NotionService()


def _create_diagram_storage_service(base_dir):
    """Factory for DiagramStorageService."""
    from dipeo_server.domains.diagram.services import DiagramStorageService
    return DiagramStorageService(base_dir=base_dir)


def _create_diagram_storage_adapter(storage_service):
    """Factory for DiagramStorageAdapter."""
    from dipeo_server.domains.diagram.services import DiagramStorageAdapter
    return DiagramStorageAdapter(storage_service=storage_service)


def _create_diagram_validator(api_key_service):
    """Factory for DiagramValidator."""
    from dipeo_server.domains.execution.validators import DiagramValidator
    return DiagramValidator(api_key_service)


def _create_execution_preparation_service(storage_service, validator, api_key_service):
    """Factory for ExecutionPreparationService."""
    from dipeo_server.domains.execution import ExecutionPreparationService
    return ExecutionPreparationService(
        storage_service=storage_service,
        validator=validator,
        api_key_service=api_key_service,
    )


def _create_api_integration_service(file_service):
    """Factory for APIIntegrationDomainService."""
    from dipeo_services import APIIntegrationDomainService
    return APIIntegrationDomainService(file_service)


def _create_text_processing_service():
    """Factory for TextProcessingDomainService."""
    from dipeo_server.domains.text import TextProcessingDomainService
    return TextProcessingDomainService()


def _create_file_operations_service(file_service):
    """Factory for FileOperationsDomainService."""
    from dipeo_server.domains.file import FileOperationsDomainService
    return FileOperationsDomainService(file_service)


def _create_notion_integration_service(notion_service, file_service):
    """Factory for NotionIntegrationDomainService."""
    from dipeo_services import NotionIntegrationDomainService
    return NotionIntegrationDomainService(notion_service, file_service)


def _create_conversation_domain_service(llm_service, api_key_service, conversation_service):
    """Factory for ConversationDomainService."""
    from dipeo_server.domains.conversation.domain_service import ConversationDomainService
    return ConversationDomainService(
        llm_service=llm_service,
        api_key_service=api_key_service,
        conversation_service=conversation_service,
    )


def _create_diagram_storage_domain_service(storage_service):
    """Factory for DiagramStorageDomainService."""
    from dipeo_server.domains.diagram.services.domain_service import DiagramStorageDomainService
    return DiagramStorageDomainService(storage_service=storage_service)


def _create_service_registry(
    llm_service, api_key_service, file_service, conversation_memory_service,
    conversation_domain_service, notion_integration_service, diagram_storage_domain_service,
    api_integration_service, text_processing_service, file_operations_service
):
    """Factory for ServiceRegistry with explicit dependencies."""
    from dipeo_server.domains.execution.services.service_registry import ServiceRegistry
    return ServiceRegistry(
        llm_service=llm_service,
        api_key_service=api_key_service,
        file_service=file_service,
        conversation_memory_service=conversation_memory_service,
        conversation_service=conversation_domain_service,
        notion_integration_service=notion_integration_service,
        diagram_storage_service=diagram_storage_domain_service,
        api_integration_service=api_integration_service,
        text_processing_service=text_processing_service,
        file_operations_service=file_operations_service,
    )


def _create_server_execution_service(service_registry, state_store, message_router, diagram_storage_service):
    """Factory for ServerExecutionService with explicit dependencies."""
    from dipeo_server.domains.execution.services import ServerExecutionService
    return ServerExecutionService(
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )


async def init_resources(container: "Container") -> None:
    """Initialize all resources that require async setup."""
    # Initialize infrastructure
    await container.state_store().initialize()
    await container.message_router().initialize()

    # Initialize services
    await container.llm_service().initialize()
    await container.diagram_storage_service().initialize()
    await container.notion_service().initialize()

    # Initialize execution service
    execution_service = container.execution_service()
    await execution_service.initialize()

    # Validate protocol compliance
    _validate_protocol_compliance(container)


async def shutdown_resources(container: "Container") -> None:
    """Cleanup all resources."""
    await container.message_router().cleanup()
    await container.state_store().cleanup()


def _validate_protocol_compliance(container: "Container") -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.llm_service(), SupportsLLM, "LLMService"),
        (container.file_service(), SupportsFile, "FileService"),
        (container.conversation_service(), SupportsMemory, "ConversationService"),
        (container.execution_service(), SupportsExecution, "ServerExecutionService"),
        (container.notion_service(), SupportsNotion, "NotionService"),
        (container.diagram_storage_service(), SupportsDiagram, "DiagramStorageService"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )


class Container(containers.DeclarativeContainer):
    """Main dependency injection container for DiPeO."""

    # Self reference for container injection
    __self__ = providers.Self()

    # Configuration
    config = providers.Configuration()

    # Base directory configuration
    base_dir = providers.Factory(
        lambda: Path(os.environ.get("DIPEO_BASE_DIR", _get_project_base_dir()))
    )

    # Infrastructure Services (Singletons)
    state_store = providers.Singleton(_import_state_store)
    message_router = providers.Singleton(_import_message_router)

    # Core Domain Services
    api_key_service = providers.Singleton(_create_api_key_service)

    file_service = providers.Singleton(
        _create_file_service,
        base_dir=base_dir,
    )

    conversation_service = providers.Singleton(_create_conversation_service)

    llm_service = providers.Singleton(
        _create_llm_service,
        api_key_service=api_key_service,
    )

    notion_service = providers.Singleton(_create_notion_service)

    # Diagram Services
    diagram_storage_service = providers.Singleton(
        _create_diagram_storage_service,
        base_dir=base_dir,
    )

    diagram_storage_adapter = providers.Singleton(
        _create_diagram_storage_adapter,
        storage_service=diagram_storage_service,
    )

    # Execution Services
    diagram_validator = providers.Factory(
        _create_diagram_validator,
        api_key_service=api_key_service,
    )

    execution_preparation_service = providers.Singleton(
        _create_execution_preparation_service,
        storage_service=diagram_storage_service,
        validator=diagram_validator,
        api_key_service=api_key_service,
    )

    # Domain Services
    api_integration_service = providers.Singleton(
        _create_api_integration_service,
        file_service=file_service,
    )

    text_processing_service = providers.Singleton(_create_text_processing_service)

    file_operations_service = providers.Singleton(
        _create_file_operations_service,
        file_service=file_service,
    )

    notion_integration_service = providers.Singleton(
        _create_notion_integration_service,
        notion_service=notion_service,
        file_service=file_service,
    )

    # Additional Domain Services
    conversation_domain_service = providers.Singleton(
        _create_conversation_domain_service,
        llm_service=llm_service,
        api_key_service=api_key_service,
        conversation_service=conversation_service,
    )

    diagram_storage_domain_service = providers.Singleton(
        _create_diagram_storage_domain_service,
        storage_service=diagram_storage_service,
    )

    # Service Registry with explicit dependencies
    service_registry = providers.Singleton(
        _create_service_registry,
        llm_service=llm_service,
        api_key_service=api_key_service,
        file_service=file_service,
        conversation_memory_service=conversation_service,
        conversation_domain_service=conversation_domain_service,
        notion_integration_service=notion_integration_service,
        diagram_storage_domain_service=diagram_storage_domain_service,
        api_integration_service=api_integration_service,
        text_processing_service=text_processing_service,
        file_operations_service=file_operations_service,
    )

    # Application Context for backward compatibility
    app_context = providers.Singleton(
        AppContextAdapter,
        container=__self__,
    )

    # Server Execution Service with explicit dependencies
    execution_service = providers.Singleton(
        _create_server_execution_service,
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )

