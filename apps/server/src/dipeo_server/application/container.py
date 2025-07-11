"""Server-specific dependency injection container."""

from pathlib import Path

from dependency_injector import providers, containers
from dipeo.container import Container as BaseContainer
from dipeo.container.infrastructure_container import _create_api_key_storage
from dipeo.application.protocols import (
    SupportsAPIKey,
    SupportsExecution,
    SupportsMemory,
)
from dipeo.core.ports import (
    FileServicePort,
    LLMServicePort,
    NotionServicePort,
)
from dipeo.application.services.apikey import APIKeyService
from dipeo.infra.database import DBOperationsDomainService
from dipeo.utils.diagram import DiagramBusinessLogic as DiagramDomainService
from dipeo.infra.persistence.diagram import (
    DiagramFileRepository,
    DiagramStorageAdapter,
)
from dipeo.application.execution.preparation import PrepareDiagramForExecutionUseCase
from dipeo.application.unified_service_registry import UnifiedServiceRegistry
from dipeo.application.execution.use_cases import ExecuteDiagramUseCase
from dipeo.utils.text import TextProcessingDomainService
from dipeo.utils.validation import ValidationDomainService
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
    
    # We'll override providers in the app_context after instantiation
    pass


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
            "ConversationMemoryServiceV2",
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
