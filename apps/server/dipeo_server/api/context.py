"""Request context for providing access to services across different protocols."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from fastapi import Request, WebSocket
from strawberry.fastapi import BaseContext

from dipeo.application.registry.keys import EXECUTION_SERVICE

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.execution.use_cases import (
        ExecuteDiagramUseCase,
    )
    from dipeo.application.registry import ServiceKey, ServiceRegistry


@dataclass
class RequestContext(BaseContext):
    """Context providing service access across protocols (GraphQL, REST, WebSocket)."""

    request: Request | None = None
    websocket: WebSocket | None = None
    container: Optional["Container"] = None
    user_data: dict[str, Any] = field(default_factory=dict)

    def get_service(self, key: "ServiceKey") -> Any:
        """Get a service from the container using a ServiceKey.

        This is the preferred method for service access in the new container system.
        """
        return self.container.get_service(key)

    @property
    def service_registry(self) -> "ServiceRegistry":
        return self.container.registry

    @property
    def execution_service(self) -> "ExecuteDiagramUseCase":
        return self.container.get_service(EXECUTION_SERVICE)

    @property
    def can_read_api_keys(self) -> bool:
        return True


def get_request_context(request_or_ws=None):
    """Create request context for HTTP or WebSocket connections."""
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
