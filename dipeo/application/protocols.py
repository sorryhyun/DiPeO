# Application-level service protocols.

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)

from dipeo.models import NodeState


class ExecutionObserver(Protocol):
    """Observers for execution events."""

    async def on_execution_start(
        self, execution_id: str, diagram_id: Optional[str]
    ) -> None: ...
    
    async def on_node_start(self, execution_id: str, node_id: str) -> None: ...
    
    async def on_node_complete(
        self, execution_id: str, node_id: str, state: NodeState
    ) -> None: ...
    
    async def on_node_error(
        self, execution_id: str, node_id: str, error: str
    ) -> None: ...
    
    async def on_execution_complete(self, execution_id: str) -> None: ...
    
    async def on_execution_error(self, execution_id: str, error: str) -> None: ...


@runtime_checkable
class SupportsAPIKey(Protocol):
    # Protocol for API key management operations.

    def get_api_key(self, key_id: str) -> dict: ...
    def list_api_keys(self) -> List[dict]: ...
    def create_api_key(self, label: str, service: str, key: str) -> dict: ...
    def delete_api_key(self, key_id: str) -> None: ...
    def update_api_key(
        self,
        key_id: str,
        label: Optional[str] = None,
        service: Optional[str] = None,
        key: Optional[str] = None,
    ) -> dict: ...


@runtime_checkable
class SupportsExecution(Protocol):
    """Protocol for diagram execution operations."""

    async def execute_diagram(
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable] = None,
    ) -> AsyncIterator[Dict[str, Any]]: ...


