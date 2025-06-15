"""GraphQL context for providing access to services."""
from typing import Dict, Any
from fastapi import Request
from strawberry.fastapi import BaseContext

from ..utils.app_context import AppContext
from ..services.api_key_service import APIKeyService
from ..services.diagram_service import DiagramService
from ..services.execution_service import ExecutionService
from ..services.event_store import event_store
from ..services.file_service import FileService
from ..services.llm_service import LLMService
from ..services.memory_service import MemoryService
from ..services.notion_service import NotionService
from ..services.message_router import message_router


class GraphQLContext(BaseContext):
    """Context object provided to all GraphQL resolvers."""
    
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
    from ..utils.dependencies import get_app_context
    
    app_context = get_app_context()
    return GraphQLContext(
        request=request,
        app_context=app_context
    )