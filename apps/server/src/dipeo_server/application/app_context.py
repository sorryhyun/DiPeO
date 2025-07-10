"""Application context and dependency injection configuration."""

from dependency_injector import providers
from .container import ServerContainer


# Global container instance
_container: ServerContainer | None = None


def get_container() -> ServerContainer:
    """Get the global DI container instance."""
    if _container is None:
        raise RuntimeError(
            "Container not initialized. Call initialize_container() first."
        )
    return _container


def initialize_container() -> ServerContainer:
    """Initialize the global DI container."""
    global _container
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Initializing ServerContainer...")

    if _container is None:
        _container = ServerContainer()
        logger.info(f"Created ServerContainer: {_container}")
        
        # Override infrastructure providers after creation
        from dipeo_server.infra.persistence.state_registry import state_store
        logger.info(f"Overriding state_store with: {state_store}")
        
        def get_state_store():
            logger.info(f"State store factory called, returning: {state_store}")
            return state_store
        
        # Import necessary modules
        from dipeo.infra import MessageRouter, NotionAPIService
        from dipeo.infra.persistence.file import ModularFileService
        from dipeo.infra.persistence.memory import InMemoryConversationStore
        from dipeo_server.shared.constants import BASE_DIR
        from dipeo.container.infrastructure_container import _create_api_key_storage
        from pathlib import Path
        from dipeo.utils.diagram import DiagramBusinessLogic as DiagramDomainService
        from dipeo.infra.persistence.diagram import DiagramFileRepository, DiagramStorageAdapter
        from dipeo.utils.validation import ValidationDomainService
        from dipeo.utils.text import TextProcessingDomainService
        from dipeo.application.services.conversation import ConversationMemoryService
        from dipeo.application.execution.preparation import PrepareDiagramForExecutionUseCase
        
        _container.infra.override_providers(
            state_store=providers.Singleton(get_state_store),
            message_router=providers.Singleton(MessageRouter),
            file_service=providers.Singleton(
                ModularFileService,
                base_dir=providers.Factory(lambda: BASE_DIR),
            ),
            memory_service=providers.Singleton(InMemoryConversationStore),
            notion_service=providers.Singleton(NotionAPIService),
            api_key_storage=providers.Singleton(
                _create_api_key_storage,
                store_file=providers.Factory(
                    lambda: str(Path(BASE_DIR) / "files" / "apikeys.json")
                ),
            ),
        )
        
        # Override domain providers
        _container.domain.override_providers(
            diagram_storage_service=providers.Singleton(DiagramDomainService),
            diagram_storage_adapter=providers.Singleton(
                DiagramStorageAdapter,
                file_repository=_container.domain.diagram_storage_service,
                domain_service=_container.domain.diagram_storage_service,
            ),
            validation_service=providers.Singleton(ValidationDomainService),
            text_processing_service=providers.Singleton(TextProcessingDomainService),
            conversation_service=providers.Singleton(
                ConversationMemoryService,
                memory_service=_container.infra.memory_service,
            ),
        )
        
        # Override application providers
        _container.application.override_providers(
            execution_preparation_service=providers.Singleton(
                PrepareDiagramForExecutionUseCase,
                storage_service=_container.domain.diagram_storage_service,
                validator=_container.domain.validation_service,
                api_key_service=_container.domain.api_key_service,
            )
        )
        
        # Configure from environment - no need to call from_env() for now
        # as we're using factory functions that handle env vars directly

        # Wire the container to necessary modules
        _container.wire(
            modules=[
                "dipeo_server.api.graphql.queries",
                "dipeo_server.api.graphql.mutations",
                "dipeo_server.api.graphql.subscriptions",
                "dipeo_server.api.graphql.resolvers",
            ]
        )

    return _container
