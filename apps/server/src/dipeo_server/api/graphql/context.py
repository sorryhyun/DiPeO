"""GraphQL context for providing access to services."""

from typing import TYPE_CHECKING, Any

from fastapi import Request
from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from dipeo.application.services.minimal_state_store import MinimalStateStore
    from dipeo.application.services.minimal_message_router import MinimalMessageRouter
    from dipeo.infra import ConsolidatedFileService
    from dipeo.infra.llm.service import LLMInfrastructureService
    from dipeo.infra.services.notion import NotionAPIService
    from dipeo.infra.services.api import APIService
    from dipeo.infra.services.file import FileOperationsService
    from dipeo.domain.services.apikey import APIKeyDomainService
    from dipeo.domain.services.conversation.simple_service import (
        ConversationMemoryService,
    )
    from dipeo.domain.services.diagram.storage import DiagramFileRepository
    from dipeo.domain.services.diagram.domain_service import DiagramStorageDomainService
    from dipeo.domain.services.db import DBOperationsDomainService
    from dipeo.domain.services.execution import ExecutionFlowService
    from dipeo.application.execution.server_execution_service import (
        ExecuteDiagramUseCase,
    )
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry


class GraphQLContext(BaseContext):
    """Context object that provides direct access to injected services."""

    request: Request
    user_data: dict[str, Any]

    # Infrastructure services
    state_store: "MinimalStateStore"
    message_router: "MinimalMessageRouter"
    file_service: "ConsolidatedFileService"
    llm_service: "LLMInfrastructureService"
    notion_service: "NotionAPIService"
    api_service: "APIService"
    file_operations_service: "FileOperationsService"

    # Domain services
    api_key_service: "APIKeyDomainService"
    conversation_service: "ConversationMemoryService"
    diagram_storage_service: "DiagramFileRepository"
    diagram_storage_domain_service: "DiagramStorageDomainService"
    db_operations_service: "DBOperationsDomainService"
    execution_flow_service: "ExecutionFlowService"

    # Application services
    execution_service: "ExecuteDiagramUseCase"
    service_registry: "UnifiedServiceRegistry"

    def __init__(
        self,
        request: Request,
        state_store: "MinimalStateStore",
        message_router: "MinimalMessageRouter",
        file_service: "ConsolidatedFileService",
        llm_service: "LLMInfrastructureService",
        notion_service: "NotionAPIService",
        api_service: "APIService",
        file_operations_service: "FileOperationsService",
        api_key_service: "APIKeyDomainService",
        conversation_service: "ConversationMemoryService",
        diagram_storage_service: "DiagramFileRepository",
        diagram_storage_domain_service: "DiagramStorageDomainService",
        db_operations_service: "DBOperationsDomainService",
        execution_flow_service: "ExecutionFlowService",
        execution_service: "ExecuteDiagramUseCase",
        service_registry: "UnifiedServiceRegistry",
    ):
        super().__init__()
        self.request = request
        self.user_data = {}

        # Infrastructure services
        self.state_store = state_store
        self.message_router = message_router
        self.file_service = file_service
        self.llm_service = llm_service
        self.notion_service = notion_service
        self.api_service = api_service
        self.file_operations_service = file_operations_service

        # Domain services
        self.api_key_service = api_key_service
        self.conversation_service = conversation_service
        self.diagram_storage_service = diagram_storage_service
        self.diagram_storage_domain_service = diagram_storage_domain_service
        self.db_operations_service = db_operations_service
        self.execution_flow_service = execution_flow_service

        # Application services
        self.execution_service = execution_service
        self.service_registry = service_registry

    @property
    def can_read_api_keys(self) -> bool:
        """Check if the current user can read API keys."""
        # Allow all requests for local use
        return True


async def get_graphql_context(request: Request = None) -> GraphQLContext:
    """
    Factory function for creating GraphQL context.
    Used as context_getter in GraphQLRouter.
    """
    # Get the global container instance
    # This assumes the container is initialized and stored globally during app startup
    from dipeo_server.application.app_context import get_app_context

    app_context = get_app_context()
    container = app_context.container

    # Create context with all required services
    return GraphQLContext(
        request=request,
        # Infrastructure services
        state_store=container.infra.state_store(),
        message_router=container.infra.message_router(),
        file_service=container.infra.file_service(),
        llm_service=container.infra.llm_service(),
        notion_service=container.infra.notion_service(),
        api_service=container.infra.api_service(),
        file_operations_service=container.infra.file_operations_service(),
        # Domain services
        api_key_service=container.domain.api_key_service(),
        conversation_service=container.domain.conversation_service(),
        diagram_storage_service=container.domain.diagram_storage_service(),
        diagram_storage_domain_service=container.domain.diagram_storage_domain_service(),
        db_operations_service=container.domain.db_operations_service(),
        execution_flow_service=container.domain.execution_flow_service(),
        # Application services
        execution_service=container.application.execution_service(),
        service_registry=container.application.service_registry(),
    )
