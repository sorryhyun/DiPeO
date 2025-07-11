"""Application-level service protocols.

These protocols define the interfaces for application services that orchestrate
domain logic and infrastructure. They are distinct from infrastructure ports.
"""

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


@runtime_checkable
class SupportsAPIKey(Protocol):
    """Protocol for API key management operations."""

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


