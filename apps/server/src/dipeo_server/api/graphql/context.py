"""GraphQL context for providing access to services."""

from typing import TYPE_CHECKING, Any, Optional

from fastapi import Request
from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from dipeo_server.application.container import ServerContainer
    from dipeo.application.services.minimal_state_store import MinimalStateStore
    from dipeo.application.services.minimal_message_router import MinimalMessageRouter
    from dipeo.infra.persistence.file import ModularFileService
    from dipeo.infra.llm import LLMInfraService
    from dipeo.infra.adapters.notion import NotionAPIService
    from dipeo.infra.services.api import APIService
    from dipeo.infra.services.file import FileOperationsService
    from dipeo.domain.services.apikey import APIKeyDomainService
    from dipeo.domain.services.conversation.simple_service import (
        ConversationMemoryService,
    )
    from dipeo.infra.persistence.diagram import DiagramFileRepository
    from dipeo.domain.services.diagram.domain_service import DiagramStorageDomainService
    from dipeo.domain.services.db import DBOperationsDomainService
    from dipeo.domain.services.execution import FlowControlService
    from dipeo.application.execution.use_cases import (
        ExecuteDiagramUseCase,
    )
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry


class GraphQLContext(BaseContext):
    """Context object that provides direct access to the DI container."""

    request: Request
    user_data: dict[str, Any]
    container: "ServerContainer"

    def __init__(
        self,
        request: Request,
        container: "ServerContainer",
    ):
        super().__init__()
        self.request = request
        self.user_data = {}
        self.container = container

    # Properties for backward compatibility - access services through container
    @property
    def state_store(self) -> "MinimalStateStore":
        return self.container.infra.state_store()

    @property
    def message_router(self) -> "MinimalMessageRouter":
        return self.container.infra.message_router()

    @property
    def file_service(self) -> "ModularFileService":
        return self.container.infra.file_service()

    @property
    def llm_service(self) -> "LLMInfraService":
        return self.container.infra.llm_service()

    @property
    def notion_service(self) -> "NotionAPIService":
        return self.container.infra.notion_service()

    @property
    def api_service(self) -> "APIService":
        return self.container.infra.api_service()

    @property
    def file_operations_service(self) -> "FileOperationsService":
        return self.container.infra.file_operations_service()

    @property
    def api_key_service(self) -> "APIKeyDomainService":
        return self.container.domain.api_key_service()

    @property
    def conversation_service(self) -> "ConversationMemoryService":
        return self.container.domain.conversation_service()

    @property
    def diagram_storage_service(self) -> "DiagramFileRepository":
        return self.container.domain.diagram_storage_service()

    @property
    def diagram_storage_domain_service(self) -> "DiagramStorageDomainService":
        return self.container.domain.diagram_storage_domain_service()

    @property
    def db_operations_service(self) -> "DBOperationsDomainService":
        return self.container.domain.db_operations_service()

    @property
    def flow_control_service(self) -> "FlowControlService":
        return self.container.domain.flow_control_service()

    @property
    def execution_service(self) -> "ExecuteDiagramUseCase":
        return self.container.application.execution_service()

    @property
    def service_registry(self) -> "UnifiedServiceRegistry":
        return self.container.application.service_registry()

    @property
    def can_read_api_keys(self) -> bool:
        """Check if the current user can read API keys."""
        # Allow all requests for local use
        return True


async def get_graphql_context(request: Request) -> GraphQLContext:
    """
    Factory function for creating GraphQL context.
    Used as context_getter in GraphQLRouter.
    """
    # Get the global container instance directly
    from dipeo_server.application.app_context import get_container

    container = get_container()

    # Create context with container
    return GraphQLContext(
        request=request,
        container=container,
    )
