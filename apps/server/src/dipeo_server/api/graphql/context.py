"""GraphQL context for providing access to services."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from fastapi import Request, WebSocket
from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from dipeo.application.execution.use_cases import (
        ExecuteDiagramUseCase,
    )
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry

    from dipeo_server.application.container import ServerContainer


@dataclass
class GraphQLContext(BaseContext):
    """Context object that provides direct access to the DI container."""

    request: Optional[Request] = None       # present on HTTP
    websocket: Optional[WebSocket] = None   # present on WS
    container: Optional["ServerContainer"] = None
    user_data: dict[str, Any] = field(default_factory=dict)

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


def get_graphql_context(request_or_ws=None):
    """
    Factory function for creating GraphQL context.
    Used as context_getter in GraphQLRouter.
    
    Handles both HTTP requests and WebSocket connections.
    Strawberry calls this with a single positional argument:
    - HTTP: The FastAPI Request object
    - WebSocket: The WebSocket connection object
    """
    # Get the global container instance directly
    from dipeo_server.application.app_context import get_container

    container = get_container()
    
    # Determine what type of connection we have
    request = None
    websocket = None
    
    if request_or_ws:
        # Check if it's a Request object (has url attribute)
        if hasattr(request_or_ws, 'url') and hasattr(request_or_ws, 'method'):
            request = request_or_ws
        # Otherwise assume it's a WebSocket
        else:
            websocket = request_or_ws

    # Create and return the context
    return GraphQLContext(
        request=request,
        websocket=websocket,
        container=container,
    )

