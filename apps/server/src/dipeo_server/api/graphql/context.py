"""GraphQL context for providing access to services."""

from typing import TYPE_CHECKING, Any

from fastapi import Request
from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from dipeo_server.application.unified_app_context import UnifiedAppContext


class GraphQLContext(BaseContext):
    """Thin context object that delegates to AppContext."""

    request: Request
    app_context: "UnifiedAppContext"
    user_data: dict[str, Any]

    def __init__(self, request: Request, app_context: "UnifiedAppContext"):
        super().__init__()
        self.request = request
        self.app_context = app_context
        self.user_data = {}

    def __getattr__(self, name: str) -> Any:
        """Delegate all service access to app_context."""
        # First check if it's in our instance dict
        if name in self.__dict__:
            return self.__dict__[name]

        # Otherwise delegate to app_context
        return getattr(self.app_context, name)

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
    from dipeo_server.application.unified_app_context import get_unified_app_context

    app_context = get_unified_app_context()
    return GraphQLContext(request=request, app_context=app_context)
