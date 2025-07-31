"""Request context for providing access to services across different protocols."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from fastapi import Request, WebSocket
from strawberry.fastapi import BaseContext

from dipeo.application.registry.keys import EXECUTION_SERVICE

if TYPE_CHECKING:
    from dipeo.application.execution.use_cases import (
        ExecuteDiagramUseCase,
    )
    from dipeo.application.registry import ServiceRegistry, ServiceKey
    from dipeo.application.bootstrap import Container


@dataclass
class RequestContext(BaseContext):
    """Context object that provides access to services and request information.

    This context can be used across different protocols (GraphQL, REST, WebSocket).
    For GraphQL specifically, it extends BaseContext for Strawberry compatibility.
    """

    request: Optional[Request] = None
    websocket: Optional[WebSocket] = None
    container: Optional["Container"] = None
    user_data: dict[str, Any] = field(default_factory=dict)

    def get_service(self, key: "ServiceKey") -> Any:
        """Get a service from the container using a ServiceKey.

        This is the preferred method for service access in the new container system.
        """
        return self.container.get_service(key)

    @property
    def service_registry(self) -> "ServiceRegistry":
        """Direct access to the service registry for advanced use cases."""
        return self.container.registry

    @property
    def execution_service(self) -> "ExecuteDiagramUseCase":
        """Direct access to execution service."""
        return self.container.get_service(EXECUTION_SERVICE)

    @property
    def can_read_api_keys(self) -> bool:
        """Check if the current user can read API keys."""
        # Allow all requests for local use
        return True


# Alias for backward compatibility during migration
GraphQLContext = RequestContext


def get_request_context(request_or_ws=None):
    """
    Factory function for creating request context.

    Handles both HTTP requests and WebSocket connections.
    For GraphQL, Strawberry calls this with a single positional argument:
    - HTTP: The FastAPI Request object
    - WebSocket: The WebSocket connection object
    """
    from dipeo_server.app_context import get_container

    container = get_container()

    request = None
    websocket = None

    if request_or_ws:
        if hasattr(request_or_ws, "url") and hasattr(request_or_ws, "method"):
            request = request_or_ws
        else:
            websocket = request_or_ws
    return RequestContext(
        request=request,
        websocket=websocket,
        container=container,
    )


# Alias for backward compatibility
get_graphql_context = get_request_context
