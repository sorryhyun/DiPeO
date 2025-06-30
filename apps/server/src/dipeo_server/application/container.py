"""Server-specific dependency injection container."""

from pathlib import Path

from dependency_injector import providers
from dipeo_container import Container as BaseContainer
from dipeo_core import (
    SupportsAPIKey,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)
from dipeo_domain.domains.apikey import APIKeyDomainService
from dipeo_domain.domains.conversation import ConversationMemoryDomainService
from dipeo_domain.domains.conversation.domain_service import ConversationDomainService
from dipeo_domain.domains.db import DBOperationsDomainService
from dipeo_domain.domains.diagram.services import (
    DiagramFileRepository,
    DiagramStorageAdapter,
)
from dipeo_domain.domains.execution import PrepareDiagramForExecutionUseCase
from dipeo_domain.domains.execution.services import (
    ExecuteDiagramUseCase,
    ServiceRegistry,
)
from dipeo_domain.domains.file import FileOperationsDomainService
from dipeo_domain.domains.text import TextProcessingDomainService
from dipeo_domain.domains.validation import ValidationDomainService
from dipeo_infra import (
    MessageRouter,
    NotionIntegrationDomainService,
)
from dipeo_domain.domains.api import APIIntegrationDomainService
from dipeo_server.infra.external.integrations.notion import NotionAPIService
from dipeo_server.infra.external.llm import LLMInfraService
from dipeo_server.infra.persistence import FileSystemRepository
from dipeo_server.infra.persistence.state_registry import state_store
from dipeo_server.shared.constants import BASE_DIR


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
        FileSystemRepository,
        base_dir=providers.Factory(lambda: BASE_DIR),
    )

    conversation_memory_service = providers.Singleton(
        ConversationMemoryDomainService,
    )

    conversation_service = providers.Singleton(
        ConversationDomainService,
        llm_service=llm_service,
        api_key_service=api_key_service,
        conversation_service=conversation_memory_service,
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

    notion_integration_service = providers.Factory(
        NotionIntegrationDomainService,
        notion_service=notion_api_service,
        file_service=file_service,
    )

    # Service registry for node handlers
    service_registry = providers.Singleton(
        ServiceRegistry,
        api_key_service=api_key_service,
        llm_service=llm_service,
        file_service=file_service,
        conversation_memory_service=conversation_memory_service,
        conversation_service=conversation_service,
        diagram_storage_service=diagram_storage_service,
        text_processing_service=text_processing_service,
        file_operations_service=file_operations_service,
        validation_service=validation_service,
        db_operations_service=db_operations_service,
        api_integration_service=api_integration_service,
        notion_integration_service=notion_integration_service,
    )

    # Execution service
    execution_service = providers.Singleton(
        ExecuteDiagramUseCase,
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )


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
        (container.file_service(), SupportsFile, "FileSystemRepository"),
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
