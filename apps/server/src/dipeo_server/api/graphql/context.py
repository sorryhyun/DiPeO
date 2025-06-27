"""GraphQL context for providing access to services."""

from typing import TYPE_CHECKING, Any

from fastapi import Request
from strawberry.fastapi import BaseContext

from dipeo_server.application.app_context import AppContext, get_app_context
from dipeo_server.infrastructure.messaging import message_router
from dipeo_server.infrastructure.persistence import state_store

if TYPE_CHECKING:
    from dipeo_core import (
        SupportsAPIKey,
        SupportsExecution,
        SupportsFile,
        SupportsLLM,
        SupportsNotion,
    )

    from dipeo_server.domains.diagram.services import (
        DiagramStorageAdapter,
        DiagramStorageService,
    )


class GraphQLContext(BaseContext):
    """Context object provided to all GraphQL resolvers."""

    api_key_service: "SupportsAPIKey"
    diagram_storage_service: "DiagramStorageService"
    diagram_storage_adapter: "DiagramStorageAdapter"
    execution_service: "SupportsExecution"
    file_service: "SupportsFile"
    llm_service: "SupportsLLM"
    notion_service: "SupportsNotion"
    conversation_service: Any  # ConversationService

    def __init__(self, request: Request, app_context: AppContext):
        super().__init__()
        self.request = request
        self.app_context = app_context

        self.diagram_storage_service = app_context.diagram_storage_service
        self.diagram_storage_adapter = app_context.diagram_storage_adapter

        self.api_key_service = app_context.api_key_service
        self.execution_service = app_context.execution_service
        self.state_store = state_store  # Use global instance
        self.file_service = app_context.file_service
        self.llm_service = app_context.llm_service
        self.conversation_service = (
            app_context.conversation_service
        )  # ConversationService now handles memory functionality
        self.notion_service = app_context.notion_service
        self.message_router = message_router  # Use global instance
        self.event_bus = app_context.event_bus

        # Backward compatibility alias
        self.memory_service = self.conversation_service

        # Additional context data
        self.user_data: dict[str, Any] = {}

    @property
    def can_read_api_keys(self) -> bool:
        """Check if the current user can read API keys."""
        # TODO: Implement proper permission checking
        # For now, allow all authenticated requests
        return True


async def get_graphql_context(request: Request = None) -> GraphQLContext:
    """
    Factory function for creating GraphQL context.
    Used as context_getter in GraphQLRouter.
    """
    app_context = get_app_context()
    return GraphQLContext(request=request, app_context=app_context)
