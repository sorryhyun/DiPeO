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
from dipeo.domain.services.execution.preparation_service import (
    PrepareDiagramForExecutionUseCase,
)
from dipeo.application.unified_service_registry import UnifiedServiceRegistry
from dipeo.application.execution.server_execution_service import ExecuteDiagramUseCase
from dipeo.domain.services.text import TextProcessingDomainService
from dipeo.domain.services.validation import ValidationDomainService
from dipeo.infra import (
    MessageRouter,
    NotionAPIService,
    LLMInfraService,
    ConsolidatedFileService,
)
from dipeo_server.infra.persistence.state_registry import state_store
from dipeo_server.shared.constants import BASE_DIR
from dipeo.infra.persistence.memory import InMemoryConversationStore


class ServerInfrastructureContainer(BaseContainer.infra.__class__):
    """Server-specific infrastructure overrides."""

    # Override specific providers
    state_store = providers.Singleton(lambda: state_store)
    message_router = providers.Singleton(MessageRouter)
    file_service = providers.Singleton(
        ConsolidatedFileService,
        base_dir=providers.Factory(lambda: BASE_DIR),
    )
    memory_service = providers.Singleton(InMemoryConversationStore)
    notion_service = providers.Singleton(NotionAPIService)


class ServerDomainContainer(BaseContainer.domain.__class__):
    """Server-specific domain overrides."""

    # Override specific providers
    api_key_service = providers.Singleton(
        APIKeyDomainService,
        store_file=providers.Factory(
            lambda: str(Path(BASE_DIR) / "files" / "apikeys.json")
        ),
    )
    diagram_storage_service = providers.Singleton(
        DiagramFileRepository,
        base_dir=providers.Factory(lambda: BASE_DIR),
    )
    validation_service = providers.Singleton(ValidationDomainService)
    text_processing_service = providers.Singleton(TextProcessingDomainService)


class ServerApplicationContainer(BaseContainer.application.__class__):
    """Server-specific application overrides."""

    # Override specific providers
    execution_preparation_service = providers.Singleton(
        PrepareDiagramForExecutionUseCase,
        storage_service=providers.DependenciesContainer.diagram_storage_service,
        validator=providers.DependenciesContainer.validation_service,
        api_key_service=providers.DependenciesContainer.api_key_service,
    )


class ServerContainer(BaseContainer):
    """Server-specific dependency injection container."""

    # Override layer containers with server-specific implementations
    domain = providers.Container(
        ServerDomainContainer,
        config=BaseContainer.config,
        base_dir=BaseContainer.base_dir,
    )

    infra = providers.Container(
        ServerInfrastructureContainer,
        config=BaseContainer.config,
        base_dir=BaseContainer.base_dir,
        api_key_service=domain.api_key_service,
        api_domain_service=domain.api_domain_service,
        file_domain_service=domain.file_domain_service,
    )

    # Wire domain's infrastructure dependencies
    domain.override_providers(infra=infra)

    application = providers.Container(
        ServerApplicationContainer,
        config=BaseContainer.config,
        infra=infra,
        domain=domain,
    )


async def init_server_resources(container: ServerContainer) -> None:
    """Initialize all server resources that require async setup."""
    # Initialize infrastructure
    await container.infra.state_store().initialize()
    await container.infra.message_router().initialize()

    # Initialize services
    await container.domain.api_key_service().initialize()
    await container.infra.llm_service().initialize()
    await container.domain.diagram_storage_service().initialize()
    await container.infra.notion_service().initialize()

    # Initialize execution service
    execution_service = container.application.execution_service()
    await execution_service.initialize()

    # Validate protocol compliance
    _validate_protocol_compliance(container)


async def shutdown_server_resources(container: ServerContainer) -> None:
    """Cleanup all server resources."""
    await container.infra.message_router().cleanup()
    await container.infra.state_store().cleanup()


def _validate_protocol_compliance(container: ServerContainer) -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.domain.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.infra.llm_service(), SupportsLLM, "LLMInfrastructureService"),
        (container.infra.file_service(), SupportsFile, "ConsolidatedFileService"),
        (
            container.domain.conversation_service(),
            SupportsMemory,
            "ConversationMemoryService",
        ),
        (
            container.application.execution_service(),
            SupportsExecution,
            "ExecuteDiagramUseCase",
        ),
        (container.infra.notion_service(), SupportsNotion, "NotionAPIService"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )
