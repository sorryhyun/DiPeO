"""GraphQL context for providing access to services."""

from typing import TYPE_CHECKING, Any

from fastapi import Request
from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from dipeo.application.execution.use_cases import (
        ExecuteDiagramUseCase,
    )
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry

    from dipeo_server.application.container import ServerContainer


class GraphQLContext(BaseContext):
    """Context object that provides direct access to the DI container."""

    request: Request | None
    user_data: dict[str, Any]
    container: "ServerContainer"

    def __init__(
        self,
        request: Request | None,
        container: "ServerContainer",
    ):
        super().__init__()
        self.request = request
        self.user_data = {}
        self.container = container

    def get_service(self, name: str) -> Any:
        """Get a service from the unified service registry."""
        return self.service_registry.get(name)

    @property
    def service_registry(self) -> "UnifiedServiceRegistry":
        return self.container.application.service_registry()

    @property
    def execution_service(self) -> "ExecuteDiagramUseCase":
        """Direct access to execution service to avoid circular dependency."""
        return self.container.application.execution_service()

    @property
    def can_read_api_keys(self) -> bool:
        """Check if the current user can read API keys."""
        # Allow all requests for local use
        return True


async def get_graphql_context(request: Request) -> GraphQLContext:
    """
    Factory function for creating GraphQL context.
    Used as context_getter in GraphQLRouter.
    
    Handles both HTTP requests and WebSocket connections.
    """
    # Get the global container instance directly
    from dipeo_server.application.app_context import get_container

    container = get_container()

    # Create and return the context
    return GraphQLContext(
        request=request,
        container=container,
    )

