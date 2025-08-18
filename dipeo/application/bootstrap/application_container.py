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
        # Use per-context wiring modules
        self._wire_bounded_contexts()
        
        # Wire remaining services that haven't been migrated yet
        self._setup_app_services()
    
    def _wire_bounded_contexts(self):
        """Wire all bounded contexts using their respective wiring modules."""
        # Wire execution context
        from dipeo.application.execution.wiring import wire_execution
        wire_execution(self.registry)
        
        # Wire conversation context
        from dipeo.application.conversation.wiring import wire_conversation
        wire_conversation(self.registry)
        
        # Wire diagram context
        from dipeo.application.diagram.wiring import wire_diagram
        wire_diagram(self.registry)
        
        # Wire integrations context
        from dipeo.application.integrations.wiring import wire_integrations
        wire_integrations(self.registry)

    def _setup_app_services(self):
        # Register domain services
        from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator
        self.registry.register(
            DIAGRAM_VALIDATOR,
            lambda: DiagramValidator(
                api_key_service=self.registry.resolve(API_KEY_SERVICE)
            )
        )
        
        from dipeo.application.utils import PromptBuilder
        self.registry.register(
            PROMPT_BUILDER,
            lambda: PromptBuilder(
                template_processor=self.registry.resolve(TEMPLATE_PROCESSOR)
            )
        )
        
        from dipeo.application import get_global_registry
        self.registry.register(
            NODE_REGISTRY,
            get_global_registry()
        )
        
        from dipeo.infrastructure.shared.database.service import DBOperationsDomainService
        from dipeo.domain.integrations.validators import DataValidator
        
        file_system = self.registry.resolve(FILESYSTEM_ADAPTER)
        if not file_system:
            from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter
            file_system = LocalFileSystemAdapter()
        
        self.registry.register(
            DB_OPERATIONS_SERVICE,
            DBOperationsDomainService(
                file_system=file_system,
                validation_service=DataValidator()
            )
        )


        # Setup repositories - now handled by InfrastructureContainer
        from dipeo.application.execution.orchestrators import ExecutionOrchestrator
        from dipeo.application.registry.keys import (
            CONVERSATION_REPOSITORY,
            PERSON_REPOSITORY,
        )
        
        # Get repositories from registry (registered by InfrastructureContainer)
        conversation_repository = self.registry.resolve(CONVERSATION_REPOSITORY)
        person_repository = self.registry.resolve(PERSON_REPOSITORY)
        
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
        
        from dipeo.application.execution.use_cases import CliSessionService
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
