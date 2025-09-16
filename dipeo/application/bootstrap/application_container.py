from dipeo.application.registry.enhanced_service_registry import EnhancedServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    DB_OPERATIONS_SERVICE,
    DIAGRAM_PORT,
    DIAGRAM_VALIDATOR,
    EXECUTION_SERVICE,
    FILESYSTEM_ADAPTER,
    MESSAGE_ROUTER,
    NODE_REGISTRY,
    PROMPT_BUILDER,
    STATE_STORE,
    TEMPLATE_PROCESSOR,
)


class ApplicationContainer:
    """Application services and use cases.

    Contains high-level orchestration, compilation pipeline,
    and execution services. Depends on both Core and Infrastructure.
    """

    def __init__(self, registry: EnhancedServiceRegistry):
        self.registry = registry
        # Only setup application-specific services
        # Bounded context wiring is handled by bootstrap_services in server/CLI context
        self._setup_app_services()

    def _setup_app_services(self):
        from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator

        self.registry.register(
            DIAGRAM_VALIDATOR,
            lambda: DiagramValidator(api_key_service=self.registry.resolve(API_KEY_SERVICE)),
        )

        from dipeo.application.utils import PromptBuilder

        self.registry.register(
            PROMPT_BUILDER,
            lambda: PromptBuilder(template_processor=self.registry.resolve(TEMPLATE_PROCESSOR)),
        )

        from dipeo.application import get_global_registry

        self.registry.register(NODE_REGISTRY, get_global_registry())

        from dipeo.domain.integrations.validators import DataValidator
        from dipeo.infrastructure.shared.database.service import DBOperationsDomainService

        def create_db_operations_service():
            if self.registry.has(FILESYSTEM_ADAPTER):
                file_system = self.registry.resolve(FILESYSTEM_ADAPTER)
            else:
                from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter

                file_system = LocalFileSystemAdapter()

            return DBOperationsDomainService(
                file_system=file_system, validation_service=DataValidator()
            )

        self.registry.register(
            DB_OPERATIONS_SERVICE,
            create_db_operations_service,
        )

        # CLI_SESSION_SERVICE is registered by wire_execution in wiring.py

        # DIAGRAM_PORT is registered by wire_diagram_port, no need to re-register it
        # Just verify it exists if we're in a context where it should be wired
        if self.registry.has(DIAGRAM_PORT):
            # Already registered by wiring, nothing to do
            pass
        from dipeo.application.execution.use_cases import ExecuteDiagramUseCase

        self.registry.register(
            EXECUTION_SERVICE,
            lambda: ExecuteDiagramUseCase(
                service_registry=self.registry,
                state_store=self.registry.resolve(STATE_STORE),
                message_router=self.registry.resolve(MESSAGE_ROUTER),
                diagram_service=self.registry.resolve(DIAGRAM_PORT),
            ),
        )
