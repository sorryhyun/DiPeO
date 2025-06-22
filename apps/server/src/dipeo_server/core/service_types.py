"""Service type protocols for duck typing and type checking.

This module defines Protocol classes that describe the interfaces for various services
in the application. These are used with TYPE_CHECKING to avoid circular imports
while maintaining type safety.
"""

from pathlib import Path
from typing import (
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
class SupportsDiagram(Protocol):
    """Protocol for diagram operations."""

    def convert_from_yaml(self, yaml_text: str) -> dict: ...
    def convert_to_llm_yaml(self, diagram: dict) -> str: ...
    def list_diagram_files(
        self, directory: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...
    def load_diagram(self, path: str) -> Dict[str, Any]: ...
    def save_diagram(self, path: str, diagram: Dict[str, Any]) -> None: ...
    def create_diagram(
        self, name: str, diagram: Dict[str, Any], format: str = "json"
    ) -> str: ...
    def update_diagram(self, path: str, diagram: Dict[str, Any]) -> None: ...
    def delete_diagram(self, path: str) -> None: ...
    async def save_diagram_with_id(
        self, diagram_dict: Dict[str, Any], filename: str
    ) -> str: ...
    async def get_diagram(self, diagram_id: str) -> Optional[Dict[str, Any]]: ...


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
class SupportsFile(Protocol):
    """Protocol for file operations."""

    def read(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]: ...
    async def write(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]: ...
    async def save_file(
        self, content: bytes, filename: str, target_path: Optional[str] = None
    ) -> Dict[str, Any]: ...


@runtime_checkable
class SupportsLLM(Protocol):
    """Protocol for LLM operations."""

    def get_token_counts(
        self, client_name: str, usage: Any
    ) -> Any: ...  # Returns TokenUsage
    async def call_llm(
        self,
        service: Optional[str],
        api_key_id: str,
        model: str,
        messages: Any,
        system_prompt: str = "",
    ) -> Dict[str, Any]: ...
    def pre_initialize_model(
        self, service: str, model: str, api_key_id: str
    ) -> bool: ...
    async def get_available_models(
        self, service: str, api_key_id: str
    ) -> List[str]: ...


@runtime_checkable
class SupportsMemory(Protocol):
    """Protocol for memory management operations."""

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
    ) -> None: ...
    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None: ...
    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]: ...
    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str: ...


@runtime_checkable
class SupportsNotion(Protocol):
    """Protocol for Notion API operations."""

    async def retrieve_page(self, page_id: str, api_key: str) -> Dict[str, Any]: ...
    async def list_blocks(self, page_id: str, api_key: str) -> List[Dict[str, Any]]: ...
    async def append_blocks(
        self, page_id: str, blocks: List[Dict[str, Any]], api_key: str
    ) -> Dict[str, Any]: ...
    async def update_block(
        self, block_id: str, block_data: Dict[str, Any], api_key: str
    ) -> Dict[str, Any]: ...
    async def query_database(
        self,
        database_id: str,
        filter: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        api_key: str = None,
    ) -> Dict[str, Any]: ...
    async def create_page(
        self,
        parent: Dict[str, Any],
        properties: Dict[str, Any],
        children: Optional[List[Dict]] = None,
        api_key: str = None,
    ) -> Dict[str, Any]: ...
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str: ...
    def create_text_block(
        self, text: str, block_type: str = "paragraph"
    ) -> Dict[str, Any]: ...
