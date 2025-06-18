"""GraphQL context for providing access to services."""
from typing import Dict, Any, TYPE_CHECKING
from fastapi import Request
from strawberry.fastapi import BaseContext

from src.shared.utils.app_context import AppContext
from src.domains.execution.services.event_store import event_store
from src.domains.execution.services.message_router import message_router

if TYPE_CHECKING:
    from src.shared.service_types import (
        SupportsAPIKey,
        SupportsDiagram,
        SupportsExecution,
        SupportsFile,
        SupportsLLM,
        SupportsMemory,
        SupportsNotion
    )


class GraphQLContext(BaseContext):
    """Context object provided to all GraphQL resolvers."""
    
    api_key_service: 'SupportsAPIKey'
    diagram_service: 'SupportsDiagram'
    execution_service: 'SupportsExecution'
    file_service: 'SupportsFile'
    llm_service: 'SupportsLLM'
    memory_service: 'SupportsMemory'
    notion_service: 'SupportsNotion'
    
    def __init__(
        self,
        request: Request,
        app_context: AppContext
    ):
        super().__init__()
        self.request = request
        self.app_context = app_context
        
        # Expose services directly for easy access
        self.api_key_service = app_context.api_key_service
        self.diagram_service = app_context.diagram_service
        self.execution_service = app_context.execution_service
        self.event_store = event_store  # Use global instance
        self.file_service = app_context.file_service
        self.llm_service = app_context.llm_service
        self.memory_service = app_context.memory_service
        self.notion_service = app_context.notion_service
        self.message_router = message_router  # Use global instance
        
        # Additional context data
        self.user_data: Dict[str, Any] = {}
        
    @property
    def can_read_api_keys(self) -> bool:
        """Check if the current user can read API keys."""
        # TODO: Implement proper permission checking
        # For now, allow all authenticated requests
        return True


async def get_graphql_context(
    request: Request = None
) -> GraphQLContext:
    """
    Factory function for creating GraphQL context.
    Used as context_getter in GraphQLRouter.
    """
    from src.shared.utils.app_context import get_app_context
    
    app_context = get_app_context()
    return GraphQLContext(
        request=request,
        app_context=app_context
    )