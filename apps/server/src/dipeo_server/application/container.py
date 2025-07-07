"""Server-specific dependency injection container."""

from pathlib import Path

from dependency_injector import providers
from dipeo.container import Container as BaseContainer
from dipeo.core import (
    SupportsAPIKey,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)
from dipeo.domain.services.apikey import APIKeyDomainService
from dipeo.domain.services.conversation.simple_service import ConversationMemoryService
from dipeo.domain.services.db import DBOperationsDomainService
from dipeo.domain.services.diagram import (
    DiagramFileRepository,
    DiagramStorageAdapter,
)
from dipeo.domain.services.execution.preparation_service import PrepareDiagramForExecutionUseCase
from dipeo.application.unified_service_registry import UnifiedServiceRegistry
from dipeo.application.execution.server_execution_service import ExecuteDiagramUseCase
from dipeo.domain.services.file import FileOperationsDomainService
from dipeo.domain.services.text import TextProcessingDomainService
from dipeo.domain.services.validation import ValidationDomainService
from dipeo.infra import (
    MessageRouter,
    NotionAPIService,
    LLMInfraService,
    ConsolidatedFileService,
)
from dipeo.domain.services.api import APIIntegrationDomainService
from dipeo_server.infra.persistence.state_registry import state_store
from dipeo_server.shared.constants import BASE_DIR
from dipeo.infra.persistence.memory import MemoryService


class ServerContainer(BaseContainer):
    """Server-specific dependency injection container."""

    # Infrastructure providers
    state_store = providers.Singleton(lambda: state_store)

    message_router = providers.Singleton(MessageRouter)

    # Domain service providers
    api_key_service = providers.Singleton(
        APIKeyDomainService,
        store_file=providers.Factory(
            lambda: str(Path(BASE_DIR) / "files" / "apikeys.json")
        ),
    )

    llm_service = providers.Singleton(
        LLMInfraService,
        api_key_service=api_key_service,
    )

    file_service = providers.Singleton(
        ConsolidatedFileService,
        base_dir=providers.Factory(lambda: BASE_DIR),
    )

    memory_service = providers.Singleton(
        MemoryService,
    )
    
    conversation_memory_service = providers.Singleton(
        ConversationMemoryService,
        memory_service=memory_service,
    )

    diagram_file_repository = providers.Singleton(
        DiagramFileRepository,
        base_dir=providers.Factory(lambda: BASE_DIR),
    )

    diagram_storage_adapter = providers.Singleton(
        DiagramStorageAdapter,
        storage_service=diagram_file_repository,
    )

    diagram_storage_service = diagram_file_repository

    validation_service = providers.Singleton(ValidationDomainService)

    prepare_diagram_use_case = providers.Singleton(
        PrepareDiagramForExecutionUseCase,
        storage_service=diagram_file_repository,
        validator=validation_service,
        api_key_service=api_key_service,
    )

    text_processing_service = providers.Singleton(TextProcessingDomainService)

    file_operations_service = providers.Singleton(
        FileOperationsDomainService,
        file_service=file_service,
    )

    db_operations_service = providers.Singleton(
        DBOperationsDomainService,
        file_service=file_service,
        validation_service=validation_service,
    )

    api_integration_service = providers.Factory(
        APIIntegrationDomainService,
        file_service=file_service,
    )

    notion_api_service = providers.Singleton(NotionAPIService)

    # Don't override service_registry - let it inherit from base container
    # The base container already includes all services including person_job services

    # Don't override execution_service - let it use the one from base container
    # which already has the correct service_registry with person_job services


async def init_server_resources(container: ServerContainer) -> None:
    """Initialize all server resources that require async setup."""
    # Initialize infrastructure
    await container.state_store().initialize()
    await container.message_router().initialize()

    # Initialize services
    await container.api_key_service().initialize()
    await container.llm_service().initialize()
    await container.diagram_storage_service().initialize()
    await container.notion_api_service().initialize()

    # Initialize execution service
    execution_service = container.execution_service()
    await execution_service.initialize()

    # Validate protocol compliance
    _validate_protocol_compliance(container)


async def shutdown_server_resources(container: ServerContainer) -> None:
    """Cleanup all server resources."""
    await container.message_router().cleanup()
    await container.state_store().cleanup()


def _validate_protocol_compliance(container: ServerContainer) -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.llm_service(), SupportsLLM, "LLMInfrastructureService"),
        (container.file_service(), SupportsFile, "ConsolidatedFileService"),
        (
            container.conversation_memory_service(),
            SupportsMemory,
            "ConversationMemoryService",
        ),
        (container.execution_service(), SupportsExecution, "ExecuteDiagramUseCase"),
        (container.notion_api_service(), SupportsNotion, "NotionAPIService"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )
