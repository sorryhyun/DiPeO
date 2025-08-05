from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_SERVICE,
    ARTIFACT_STORE,
    AST_PARSER,
    BLOB_STORE,
    CLI_SESSION_SERVICE,
    COMPILATION_SERVICE,
    CONVERSATION_MANAGER,
    DB_OPERATIONS_SERVICE,
    DIAGRAM_CONVERTER,
    DIAGRAM_STORAGE,
    DIAGRAM_STORAGE_SERVICE,
    DIAGRAM_VALIDATOR,
    EXECUTION_SERVICE,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    PERSON_MANAGER,
    PROMPT_BUILDER,
    STATE_STORE,
)

TEMPLATE_PROCESSOR = ServiceKey("template_processor")
NODE_REGISTRY = ServiceKey("node_registry")
DOMAIN_SERVICE_REGISTRY = ServiceKey("domain_service_registry")
FILESYSTEM_ADAPTER = ServiceKey("filesystem_adapter")
API_KEY_STORAGE = ServiceKey("api_key_storage")


class ApplicationContainer:
    """Application services and use cases.

    Contains high-level orchestration, compilation pipeline,
    and execution services. Depends on both Core and Infrastructure.
    """

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._setup_application_services()

    def _setup_application_services(self):
        """Register application-level services with dependencies."""
        from dipeo.infrastructure.services.diagram import DiagramConverterService, CompilationService
        
        # Register diagram converter service
        self.registry.register(
            DIAGRAM_CONVERTER,
            DiagramConverterService()
        )
        
        # Register compilation service
        self.registry.register(
            COMPILATION_SERVICE,
            CompilationService()
        )
        
        self._setup_app_services()

    def _setup_app_services(self):
        """Set up application-level services."""
        from dipeo.infrastructure.services.database.service import DBOperationsDomainService
        from dipeo.domain.validators import DataValidator
        
        # Get file system from registry (should be registered by infrastructure container)
        file_system = self.registry.resolve(FILESYSTEM_ADAPTER)
        if not file_system:
            # Fallback to creating a new one if not found
            from dipeo.infrastructure.adapters.storage import FilesystemAdapter
            file_system = FilesystemAdapter()
        
        self.registry.register(
            DB_OPERATIONS_SERVICE,
            DBOperationsDomainService(
                file_system=file_system,
                validation_service=DataValidator()
            )
        )


        from dipeo.application.services.person_manager_impl import PersonManagerImpl
        self.registry.register(
            PERSON_MANAGER,
            PersonManagerImpl()
        )

        from dipeo.application.services.conversation_manager_impl import ConversationManagerImpl
        conversation_manager = ConversationManagerImpl()
        self.registry.register(CONVERSATION_MANAGER, conversation_manager)
        from dipeo.application.registry.keys import CONVERSATION_SERVICE
        self.registry.register(CONVERSATION_SERVICE, conversation_manager)
        
        from dipeo.application.services.cli_session_service import CliSessionService
        self.registry.register(CLI_SESSION_SERVICE, CliSessionService())

        from dipeo.infrastructure.services.diagram import DiagramService
        from dipeo.application.registry.keys import DIAGRAM_SERVICE_NEW
        self.registry.register(
            DIAGRAM_SERVICE_NEW,
            lambda: DiagramService(
                storage=self.registry.resolve(DIAGRAM_STORAGE),
                converter=None  # Will create default converter
            )
        )
        from dipeo.application.execution.use_cases import ExecuteDiagramUseCase
        self.registry.register(
            EXECUTION_SERVICE,
            lambda: ExecuteDiagramUseCase(
                service_registry=self.registry,
                state_store=self.registry.resolve(STATE_STORE),
                message_router=self.registry.resolve(MESSAGE_ROUTER),
                diagram_storage_service=self.registry.resolve(DIAGRAM_STORAGE),
            )
        )
