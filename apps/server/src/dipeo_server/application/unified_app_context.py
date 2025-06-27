"""Unified application context with the new architecture."""

from dipeo_server.application.app_context import AppContext
from dipeo_server.domains.api import APIIntegrationDomainService
from dipeo_server.domains.execution.services import UnifiedExecutionService
from dipeo_server.domains.file import FileOperationsDomainService
from dipeo_server.domains.text import TextProcessingDomainService


class UnifiedAppContext(AppContext):
    """Extended app context that supports the new unified architecture."""

    def __init__(self):
        super().__init__()

        # New domain services
        self.api_integration_service: APIIntegrationDomainService | None = None
        self.text_processing_service: TextProcessingDomainService | None = None
        self.file_operations_service: FileOperationsDomainService | None = None

        # Infrastructure services that GraphQL layer expects
        from dipeo_server.infrastructure.messaging import message_router
        from dipeo_server.infrastructure.persistence import state_store

        self.state_store = state_store
        self.message_router = message_router

    async def startup(self):
        """Initialize services with unified execution."""
        # Initialize base services first
        await super().startup()

        # Initialize new domain services
        self.api_integration_service = APIIntegrationDomainService(self.file_service)
        self.text_processing_service = TextProcessingDomainService()
        self.file_operations_service = FileOperationsDomainService(self.file_service)

        # Replace execution service with unified version
        unified_execution_service = UnifiedExecutionService(self)
        await unified_execution_service.initialize()

        # Replace the execution service
        self.execution_service = unified_execution_service

        # Re-validate protocol compliance
        self._validate_protocol_compliance()


# Create unified app context instance
unified_app_context = UnifiedAppContext()


def get_unified_app_context() -> UnifiedAppContext:
    """Get the unified application context."""
    return unified_app_context
