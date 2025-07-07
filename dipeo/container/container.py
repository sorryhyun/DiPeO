"""Dependency Injection Container for DiPeO applications."""

import os
from pathlib import Path

from dependency_injector import containers, providers
from dipeo.core import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)

from .adapters.app_context_adapter import AppContextAdapter


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
    # TODO: This is server-specific. For now, return None for non-server contexts
    try:
        from dipeo_server.infra.persistence import state_store
        return state_store
    except ImportError:
        # Return a minimal implementation for CLI usage
        from dipeo.application.services.minimal_state_store import MinimalStateStore
        return MinimalStateStore()


def _import_message_router():
    # TODO: This is server-specific. For now, return None for non-server contexts
    try:
        from dipeo_server.infra.messaging import message_router
        return message_router
    except ImportError:
        # Return a minimal implementation for CLI usage
        from dipeo.application.services.minimal_message_router import MinimalMessageRouter
        return MinimalMessageRouter()


def _create_api_key_service():
    from dipeo.domain.domains.apikey import APIKeyDomainService

    return APIKeyDomainService()


def _create_file_service(base_dir):
    from dipeo.infra import ConsolidatedFileService

    return ConsolidatedFileService(base_dir=base_dir)


def _create_memory_service():
    from dipeo.infra.persistence.memory import MemoryService
    
    return MemoryService()


def _create_conversation_service(memory_service):
    from dipeo.domain.domains.conversation.simple_service import (
        ConversationMemoryService,
    )

    return ConversationMemoryService(memory_service)


def _create_llm_service(api_key_service):
    from dipeo.infra.adapters.llm import LLMInfraService

    return LLMInfraService(api_key_service)


def _create_notion_service():
    # TODO: NotionAPIService not yet implemented in new structure
    # Return None for now as it's optional
    return None


def _create_diagram_storage_service(base_dir):
    from dipeo.domain.domains.diagram import DiagramFileRepository

    return DiagramFileRepository(base_dir=base_dir)


def _create_diagram_storage_adapter(storage_service):
    from dipeo.domain.domains.diagram import DiagramStorageAdapter

    return DiagramStorageAdapter(storage_service=storage_service)


def _create_diagram_validator(api_key_service):
    from dipeo.domain.domains.execution.validators import DiagramValidator

    return DiagramValidator(api_key_service)


def _create_execution_preparation_service(storage_service, validator, api_key_service):
    from dipeo.domain.domains.execution import PrepareDiagramForExecutionUseCase

    return PrepareDiagramForExecutionUseCase(
        storage_service=storage_service,
        validator=validator,
        api_key_service=api_key_service,
    )


def _create_api_integration_service(file_service):
    from dipeo.domain.domains.api import APIIntegrationDomainService

    return APIIntegrationDomainService(file_service)


def _create_text_processing_service():
    from dipeo.domain.domains.text import TextProcessingDomainService

    return TextProcessingDomainService()


def _create_file_operations_service(file_service):
    from dipeo.domain.domains.file import FileOperationsDomainService

    return FileOperationsDomainService(file_service)



def _create_diagram_storage_domain_service(storage_service):
    from dipeo.domain.domains.diagram.domain_service import (
        DiagramStorageDomainService,
    )

    return DiagramStorageDomainService(storage_service=storage_service)


def _create_validation_service():
    from dipeo.domain.domains.validation import ValidationDomainService

    return ValidationDomainService()


def _create_db_operations_service(file_service, validation_service):
    from dipeo.domain.domains.db import DBOperationsDomainService

    return DBOperationsDomainService(file_service, validation_service)


def _create_service_registry(
    llm_service,
    api_key_service,
    file_service,
    conversation_memory_service,
    notion_service,
    diagram_storage_domain_service,
    api_integration_service,
    text_processing_service,
    file_operations_service,
    validation_service,
    db_operations_service,
):
    """Factory for UnifiedServiceRegistry with explicit dependencies."""
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry

    # Create registry and register all services dynamically
    registry = UnifiedServiceRegistry()
    
    # Core services
    registry.register("llm", llm_service)
    registry.register("llm_service", llm_service)
    registry.register("api_key", api_key_service)
    registry.register("api_key_service", api_key_service)
    registry.register("file", file_service)
    registry.register("file_service", file_service)
    registry.register("conversation_memory", conversation_memory_service)
    registry.register("conversation_memory_service", conversation_memory_service)
    registry.register("memory", conversation_memory_service)
    registry.register("memory_service", conversation_memory_service)
    registry.register("conversation", conversation_memory_service)
    
    # Domain services
    registry.register("notion", notion_service)
    registry.register("notion_service", notion_service)
    registry.register("diagram_storage", diagram_storage_domain_service)
    registry.register("diagram_storage_service", diagram_storage_domain_service)
    registry.register("storage", diagram_storage_domain_service)
    registry.register("api_integration", api_integration_service)
    registry.register("api_integration_service", api_integration_service)
    registry.register("api", api_integration_service)
    registry.register("text_processing", text_processing_service)
    registry.register("text_processing_service", text_processing_service)
    registry.register("text", text_processing_service)
    registry.register("file_operations", file_operations_service)
    registry.register("file_operations_service", file_operations_service)
    registry.register("validation", validation_service)
    registry.register("validation_service", validation_service)
    registry.register("db_operations", db_operations_service)
    registry.register("db_operations_service", db_operations_service)
    
    return registry


def _create_execute_diagram_use_case(
    service_registry, state_store, message_router, diagram_storage_service
):
    """Factory for ExecuteDiagramUseCase with explicit dependencies."""
    from dipeo.application.execution.server_execution_service import ExecuteDiagramUseCase

    return ExecuteDiagramUseCase(
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )


async def init_resources(container: "Container") -> None:
    """Initialize all resources that require async setup."""
    # Initialize infrastructure
    state_store = container.state_store()
    if hasattr(state_store, 'initialize'):
        await state_store.initialize()
    
    message_router = container.message_router()
    if hasattr(message_router, 'initialize'):
        await message_router.initialize()

    # Initialize services
    await container.llm_service().initialize()
    await container.diagram_storage_service().initialize()
    
    notion_service = container.notion_service()
    if notion_service is not None and hasattr(notion_service, 'initialize'):
        await notion_service.initialize()

    # Initialize execution service
    execution_service = container.execution_service()
    if execution_service is not None:
        await execution_service.initialize()

    # Validate protocol compliance
    _validate_protocol_compliance(container)


async def shutdown_resources(container: "Container") -> None:
    """Cleanup all resources."""
    message_router = container.message_router()
    if hasattr(message_router, 'cleanup'):
        await message_router.cleanup()
    
    state_store = container.state_store()
    if hasattr(state_store, 'cleanup'):
        await state_store.cleanup()


def _validate_protocol_compliance(container: "Container") -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.llm_service(), SupportsLLM, "LLMInfrastructureService"),
        (container.file_service(), SupportsFile, "FileSystemRepository"),
        (container.conversation_service(), SupportsMemory, "ConversationMemoryService"),
        (container.execution_service(), SupportsExecution, "ExecuteDiagramUseCase"),
        (container.notion_service(), SupportsNotion, "NotionAPIService"),
        (container.diagram_storage_service(), SupportsDiagram, "DiagramFileRepository"),
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

    memory_service = providers.Singleton(_create_memory_service)

    conversation_service = providers.Singleton(
        _create_conversation_service,
        memory_service=memory_service,
    )

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


    # Additional Domain Services

    diagram_storage_domain_service = providers.Singleton(
        _create_diagram_storage_domain_service,
        storage_service=diagram_storage_service,
    )

    # Validation Services
    validation_service = providers.Singleton(_create_validation_service)
    db_operations_service = providers.Singleton(
        _create_db_operations_service,
        file_service=file_service,
        validation_service=validation_service,
    )

    # Service Registry with explicit dependencies
    service_registry = providers.Singleton(
        _create_service_registry,
        llm_service=llm_service,
        api_key_service=api_key_service,
        file_service=file_service,
        conversation_memory_service=conversation_service,
        notion_service=notion_service,
        diagram_storage_domain_service=diagram_storage_domain_service,
        api_integration_service=api_integration_service,
        text_processing_service=text_processing_service,
        file_operations_service=file_operations_service,
        validation_service=validation_service,
        db_operations_service=db_operations_service,
    )

    # Application Context for backward compatibility
    app_context = providers.Singleton(
        AppContextAdapter,
        container=__self__,
    )

    # Execute Diagram Use Case with explicit dependencies
    execution_service = providers.Singleton(
        _create_execute_diagram_use_case,
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )
