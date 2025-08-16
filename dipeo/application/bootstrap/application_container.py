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
    DIAGRAM_VALIDATOR,
    EXECUTION_SERVICE,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    PERSON_MANAGER,
    PREPARE_DIAGRAM_USE_CASE,
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
        from dipeo.infrastructure.services.diagram import DiagramConverterService, CompilationService
        
        self.registry.register(
            DIAGRAM_CONVERTER,
            DiagramConverterService()
        )
        
        self.registry.register(
            COMPILATION_SERVICE,
            CompilationService()
        )
        
        self._setup_app_services()

    def _setup_app_services(self):
        from dipeo.infrastructure.services.database.service import DBOperationsDomainService
        from dipeo.domain.validators import DataValidator
        
        file_system = self.registry.resolve(FILESYSTEM_ADAPTER)
        if not file_system:
            from dipeo.infrastructure.adapters.storage import FilesystemAdapter
            file_system = FilesystemAdapter()
        
        self.registry.register(
            DB_OPERATIONS_SERVICE,
            DBOperationsDomainService(
                file_system=file_system,
                validation_service=DataValidator()
            )
        )


        # Setup repositories
        from dipeo.application.repositories import (
            InMemoryPersonRepository,
            InMemoryConversationRepository
        )
        from dipeo.application.services.execution_orchestrator import ExecutionOrchestrator
        
        # Create repository instances
        person_repository = InMemoryPersonRepository()
        conversation_repository = InMemoryConversationRepository()
        
        # Create orchestrator that coordinates between repositories
        orchestrator = ExecutionOrchestrator(
            person_repository=person_repository,
            conversation_repository=conversation_repository
        )
        
        # Register the orchestrator as both conversation manager and person manager
        # for backward compatibility during migration
        self.registry.register(CONVERSATION_MANAGER, orchestrator)
        from dipeo.application.registry.keys import CONVERSATION_SERVICE
        self.registry.register(CONVERSATION_SERVICE, orchestrator)
        
        # For now, we'll keep PERSON_MANAGER pointing to the orchestrator
        # This maintains compatibility while we migrate
        self.registry.register(PERSON_MANAGER, orchestrator)
        
        from dipeo.application.services.cli_session_service import CliSessionService
        self.registry.register(CLI_SESSION_SERVICE, CliSessionService())

        from dipeo.infrastructure.services.diagram import DiagramService
        from dipeo.application.registry.keys import DIAGRAM_SERVICE_NEW, DIAGRAM_CONVERTER
        from pathlib import Path
        from dipeo.core.config import Config
        
        filesystem = self.registry.resolve(FILESYSTEM_ADAPTER)
        converter = self.registry.resolve(DIAGRAM_CONVERTER)
        config = Config()
        base_path = Path(config.base_dir) / "files"
        
        # Create and register as a singleton instead of lambda
        diagram_service = DiagramService(
            filesystem=filesystem,
            base_path=base_path,
            converter=converter
        )
        self.registry.register(DIAGRAM_SERVICE_NEW, diagram_service)
        from dipeo.application.execution.use_cases import ExecuteDiagramUseCase, PrepareDiagramForExecutionUseCase
        self.registry.register(
            EXECUTION_SERVICE,
            lambda: ExecuteDiagramUseCase(
                service_registry=self.registry,
                state_store=self.registry.resolve(STATE_STORE),
                message_router=self.registry.resolve(MESSAGE_ROUTER),
                diagram_service=self.registry.resolve(DIAGRAM_SERVICE_NEW),
            )
        )
        self.registry.register(
            PREPARE_DIAGRAM_USE_CASE,
            lambda: PrepareDiagramForExecutionUseCase(
                diagram_service=self.registry.resolve(DIAGRAM_SERVICE_NEW),
                validator=self.registry.resolve(DIAGRAM_VALIDATOR),
                api_key_service=self.registry.resolve(API_KEY_SERVICE),
                service_registry=self.registry,
            )
        )
