"""Server-specific dependency injection container."""

from pathlib import Path

from dependency_injector import providers, containers
from dipeo.container import Container as BaseContainer
from dipeo.container.infrastructure_container import _create_api_key_storage
from dipeo.core import (
    SupportsAPIKey,
    SupportsExecution,
    SupportsMemory,
)
from dipeo.core.ports import (
    FileServicePort,
    LLMServicePort,
    NotionServicePort,
)
from dipeo.domain.services.apikey import APIKeyDomainService
from dipeo.domain.services.conversation.simple_service import ConversationMemoryService
from dipeo.domain.services.db import DBOperationsDomainService
from dipeo.domain.services.diagram import DiagramDomainService
from dipeo.infra.persistence.diagram import (
    DiagramFileRepository,
    DiagramStorageAdapter,
)
from dipeo.domain.services.execution.preparation_service import (
    PrepareDiagramForExecutionUseCase,
)
from dipeo.application.unified_service_registry import UnifiedServiceRegistry
from dipeo.application.execution.use_cases import ExecuteDiagramUseCase
from dipeo.domain.services.text import TextProcessingDomainService
from dipeo.domain.services.validation import ValidationDomainService
from dipeo.infra import (
    MessageRouter,
    NotionAPIService,
    LLMInfraService,
)
from dipeo.infra.persistence.file import ModularFileService
from dipeo_server.infra.persistence.state_registry import state_store
from dipeo_server.shared.constants import BASE_DIR
from dipeo.infra.persistence.memory import InMemoryConversationStore


# We don't need separate container classes - we'll override directly in ServerContainer


class ServerContainer(BaseContainer):
    """Server-specific dependency injection container."""

    # Override providers in init method to ensure proper initialization
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Override infrastructure providers
        self.infra.override_providers(
            state_store=providers.Singleton(lambda: state_store),
            message_router=providers.Singleton(MessageRouter),
            file_service=providers.Singleton(
                ModularFileService,
                base_dir=providers.Factory(lambda: BASE_DIR),
            ),
            memory_service=providers.Singleton(InMemoryConversationStore),
            notion_service=providers.Singleton(NotionAPIService),
        )

        # Override infra providers to set api key storage path
        self.infra.override_providers(
            api_key_storage=providers.Singleton(
                _create_api_key_storage,
                store_file=providers.Factory(
                    lambda: str(Path(BASE_DIR) / "files" / "apikeys.json")
                ),
            ),
        )

        # Override domain providers
        self.domain.override_providers(
            diagram_domain_service=providers.Singleton(DiagramDomainService),
            diagram_storage_service=providers.Singleton(
                DiagramFileRepository,
                domain_service=self.domain.diagram_domain_service,
                base_dir=providers.Factory(lambda: BASE_DIR),
            ),
            diagram_storage_adapter=providers.Singleton(
                DiagramStorageAdapter,
                file_repository=self.domain.diagram_storage_service,
                domain_service=self.domain.diagram_domain_service,
            ),
            validation_service=providers.Singleton(ValidationDomainService),
            text_processing_service=providers.Singleton(TextProcessingDomainService),
            conversation_service=providers.Singleton(
                ConversationMemoryService,
                memory_service=self.infra.memory_service,
            ),
        )

        # Override application providers
        self.application.override_providers(
            execution_preparation_service=providers.Singleton(
                PrepareDiagramForExecutionUseCase,
                storage_service=self.domain.diagram_storage_service,
                validator=self.domain.validation_service,
                api_key_service=self.domain.api_key_service,
            )
        )


async def init_server_resources(container: ServerContainer) -> None:
    """Initialize all server resources that require async setup."""
    # Initialize infrastructure
    state_store = container.infra.state_store()
    if hasattr(state_store, "initialize"):
        await state_store.initialize()

    message_router = container.infra.message_router()
    if hasattr(message_router, "initialize"):
        await message_router.initialize()

    # Initialize services
    api_key_service = container.domain.api_key_service()
    if hasattr(api_key_service, "initialize"):
        await api_key_service.initialize()

    llm_service = container.infra.llm_service()
    if hasattr(llm_service, "initialize"):
        await llm_service.initialize()

    diagram_storage_service = container.domain.diagram_storage_service()
    if hasattr(diagram_storage_service, "initialize"):
        await diagram_storage_service.initialize()

    notion_service = container.infra.notion_service()
    if notion_service is not None and hasattr(notion_service, "initialize"):
        await notion_service.initialize()

    # Initialize execution service
    execution_service = container.application.execution_service()
    if execution_service is not None and hasattr(execution_service, "initialize"):
        await execution_service.initialize()

    # Validate protocol compliance
    _validate_protocol_compliance(container)


async def shutdown_server_resources(container: ServerContainer) -> None:
    """Cleanup all server resources."""
    message_router = container.infra.message_router()
    if hasattr(message_router, "cleanup"):
        await message_router.cleanup()

    state_store = container.infra.state_store()
    if hasattr(state_store, "cleanup"):
        await state_store.cleanup()


def _validate_protocol_compliance(container: ServerContainer) -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.domain.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.infra.llm_service(), LLMServicePort, "LLMInfrastructureService"),
        (container.infra.file_service(), FileServicePort, "ModularFileService"),
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
        (container.infra.notion_service(), NotionServicePort, "NotionAPIService"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )
