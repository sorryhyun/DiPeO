from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_KEY_STORAGE,
    AST_PARSER,
    BLOB_STORE,
    CLI_SESSION_SERVICE,
    DB_OPERATIONS_SERVICE,
    DIAGRAM_CONVERTER,
    DIAGRAM_PORT,
    DIAGRAM_VALIDATOR,
    DOMAIN_SERVICE_REGISTRY,
    EXECUTION_SERVICE,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    NODE_REGISTRY,
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
        # ExecutionOrchestrator is now registered by wire_execution() in _wire_bounded_contexts()
        
        from dipeo.application.execution.use_cases import CliSessionService
        self.registry.register(CLI_SESSION_SERVICE, CliSessionService())

        # DiagramService is already wired by wire_all_diagram_services
        # Just register it with the old key for backward compatibility
        from dipeo.application.registry.keys import DIAGRAM_PORT
        diagram_service = self.registry.resolve(DIAGRAM_PORT)
        if diagram_service:
            self.registry.register(DIAGRAM_PORT, diagram_service)
        from dipeo.application.execution.use_cases import ExecuteDiagramUseCase
        self.registry.register(
            EXECUTION_SERVICE,
            lambda: ExecuteDiagramUseCase(
                service_registry=self.registry,
                state_store=self.registry.resolve(STATE_STORE),
                message_router=self.registry.resolve(MESSAGE_ROUTER),
                diagram_service=self.registry.resolve(DIAGRAM_PORT),
            )
        )
        # PrepareDiagramForExecutionUseCase is now registered by wire_execution() in _wire_bounded_contexts()
