from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_KEY_STORAGE,
    API_SERVICE,
    ARTIFACT_STORE,
    AST_PARSER,
    BLOB_STORE,
    CLI_SESSION_SERVICE,
    COMPILATION_SERVICE,
    CONVERSATION_MANAGER,
    DB_OPERATIONS_SERVICE,
    DIAGRAM_CONVERTER,
    DIAGRAM_SERVICE,
    DIAGRAM_VALIDATOR,
    DOMAIN_SERVICE_REGISTRY,
    EXECUTION_SERVICE,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    NODE_REGISTRY,
    PERSON_MANAGER,
    PREPARE_DIAGRAM_USE_CASE,
    PROMPT_BUILDER,
    STATE_STORE,
    TEMPLATE_PROCESSOR,
)


class ApplicationContainer:
    """Application services and use cases.

    Contains high-level orchestration, compilation pipeline,
    and execution services. Depends on both Core and Infrastructure.
    """

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._setup_application_services()

    def _setup_application_services(self):
        # Use the wiring system for diagram services
        from dipeo.application.wiring.diagram_wiring import wire_all_diagram_services
        
        # This will wire compiler, serializer, and diagram port based on feature flags
        wire_all_diagram_services(self.registry)
        
        self._setup_app_services()

    def _setup_app_services(self):
        from dipeo.infrastructure.services.database.service import DBOperationsDomainService
        from dipeo.domain.validators import DataValidator
        
        file_system = self.registry.resolve(FILESYSTEM_ADAPTER)
        if not file_system:
            from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter
            file_system = LocalFileSystemAdapter()
        
        self.registry.register(
            DB_OPERATIONS_SERVICE,
            DBOperationsDomainService(
                file_system=file_system,
                validation_service=DataValidator()
            )
        )


        # Setup repositories
        from dipeo.application.repositories import (
            # InMemoryAPIKeyRepository,
            InMemoryConversationRepository,
            # InMemoryDiagramRepository,
            # InMemoryExecutionRepository,
            # InMemoryNodeOutputRepository,
            InMemoryPersonRepository,
        )
        from dipeo.application.services.execution_orchestrator import ExecutionOrchestrator
        
        # Create repository instances
        # api_key_repository = InMemoryAPIKeyRepository()
        conversation_repository = InMemoryConversationRepository()
        # diagram_repository = InMemoryDiagramRepository()
        # execution_repository = InMemoryExecutionRepository()
        # node_output_repository = InMemoryNodeOutputRepository()
        person_repository = InMemoryPersonRepository()
        
        # Register repositories with service registry for access
        from dipeo.application.registry.keys import (
            API_KEY_REPOSITORY,
            CONVERSATION_REPOSITORY,
            DIAGRAM_REPOSITORY,
            EXECUTION_REPOSITORY,
            NODE_OUTPUT_REPOSITORY,
            PERSON_REPOSITORY,
        )
        
        # self.registry.register(API_KEY_REPOSITORY, api_key_repository)
        self.registry.register(CONVERSATION_REPOSITORY, conversation_repository)
        # self.registry.register(DIAGRAM_REPOSITORY, diagram_repository)
        # self.registry.register(EXECUTION_REPOSITORY, execution_repository)
        # self.registry.register(NODE_OUTPUT_REPOSITORY, node_output_repository)
        self.registry.register(PERSON_REPOSITORY, person_repository)
        
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

        # DiagramService is already wired by wire_all_diagram_services
        # Just register it with the old key for backward compatibility
        from dipeo.application.registry.registry_tokens import DIAGRAM_PORT
        diagram_service = self.registry.resolve(DIAGRAM_PORT)
        if diagram_service:
            self.registry.register(DIAGRAM_SERVICE, diagram_service)
        from dipeo.application.execution.use_cases import ExecuteDiagramUseCase, PrepareDiagramForExecutionUseCase
        self.registry.register(
            EXECUTION_SERVICE,
            lambda: ExecuteDiagramUseCase(
                service_registry=self.registry,
                state_store=self.registry.resolve(STATE_STORE),
                message_router=self.registry.resolve(MESSAGE_ROUTER),
                diagram_service=self.registry.resolve(DIAGRAM_SERVICE),
            )
        )
        self.registry.register(
            PREPARE_DIAGRAM_USE_CASE,
            lambda: PrepareDiagramForExecutionUseCase(
                diagram_service=self.registry.resolve(DIAGRAM_SERVICE),
                validator=self.registry.resolve(DIAGRAM_VALIDATOR),
                api_key_service=self.registry.resolve(API_KEY_SERVICE),
                service_registry=self.registry,
            )
        )
