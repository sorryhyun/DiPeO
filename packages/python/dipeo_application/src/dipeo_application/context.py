"""Application context interface for use cases.

This provides an abstraction over the actual application context
to allow use cases to be used in different environments (server, CLI).
"""

from typing import Protocol


class ApplicationContext(Protocol):
    """Protocol for application context required by use cases."""

    @property
    def api_key_service(self) -> "SupportsAPIKey | None": ...

    @property
    def llm_service(self) -> "SupportsLLM | None": ...

    @property
    def file_service(self) -> "SupportsFile | None": ...

    @property
    def conversation_service(self) -> "SupportsMemory | None": ...

    @property
    def execution_service(self) -> "SupportsExecution | None": ...

    @property
    def notion_service(self) -> "SupportsNotion | None": ...

    @property
    def diagram_storage_service(self) -> "SupportsDiagram | None": ...

    @property
    def state_store(self):
        """State store for execution state management."""
        ...

    @property
    def message_router(self):
        """Message router for real-time updates."""
        ...
