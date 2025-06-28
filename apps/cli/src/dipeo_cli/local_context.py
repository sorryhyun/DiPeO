"""Local application context for CLI execution."""

from typing import Optional

from dipeo_core import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)


class MinimalStateStore:
    """Minimal state store for local execution."""

    async def create_execution_in_cache(self, execution_id: str, diagram_id: str | None, variables: dict):
        """Create execution record (no-op for local execution)."""
        pass

    async def update_node_state(self, execution_id: str, node_id: str, state: str):
        """Update node state (no-op for local execution)."""
        pass


class MinimalMessageRouter:
    """Minimal message router for local execution."""

    async def send_update(self, execution_id: str, update: dict):
        """Send update (no-op for local execution)."""
        pass


class LocalAppContext:
    """Minimal application context for CLI local execution."""

    def __init__(self):
        # Required services - will be None for minimal local execution
        self.api_key_service: SupportsAPIKey | None = None
        self.llm_service: SupportsLLM | None = None
        self.file_service: SupportsFile | None = None
        self.conversation_service: SupportsMemory | None = None
        self.execution_service: SupportsExecution | None = None
        self.notion_service: SupportsNotion | None = None
        self.diagram_storage_service: SupportsDiagram | None = None

        # Minimal infrastructure
        self.state_store = MinimalStateStore()
        self.message_router = MinimalMessageRouter()

    async def initialize_for_local(self):
        """Initialize minimal services for local execution."""
        # Import necessary services
        from dipeo_usecases import LocalExecutionService

        # Initialize execution service
        self.execution_service = LocalExecutionService(self)
        await self.execution_service.initialize()

        # TODO: Initialize other services as needed for specific node types
        # For now, we'll start with just the execution service