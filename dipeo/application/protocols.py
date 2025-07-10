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


@runtime_checkable
class SupportsMemory(Protocol):
    """Protocol for memory management operations.
    
    Note: This protocol is evolving. The forget_* methods contain business logic
    that should ideally be in the domain layer. Future versions may replace these
    with more infrastructure-focused operations, with business logic handled by
    domain services like MemoryTransformer.
    """

    def get_or_create_person_memory(self, person_id: str) -> Any: ...
    def add_message_to_conversation(
        self,
        person_id: str,
        execution_id: str,
        role: str,
        content: str,
        current_person_id: str,
        node_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> None: ...
    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None: 
        """Clear all messages for a person (infrastructure operation)."""
        ...
    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None: 
        """[DEPRECATED] Clear only messages sent by the person.
        
        This method contains business logic that should be in the domain layer.
        Modern implementations should use MemoryTransformer for forgetting strategies.
        """
        ...
    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]: ...
    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str: ...
    def clear_all_conversations(self) -> None: ...