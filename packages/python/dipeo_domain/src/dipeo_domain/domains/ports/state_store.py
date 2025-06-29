"""State storage port for domain layer."""

from typing import Any, Protocol, runtime_checkable

from dipeo_domain import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeOutput,
    TokenUsage,
)


@runtime_checkable
class StateStorePort(Protocol):
    """Port for execution state persistence."""

    async def initialize(self) -> None:
        """Initialize the state store."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def create_execution(
        self,
        execution_id: ExecutionID,
        diagram_id: DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        """Create a new execution state."""
        ...

    async def save_state(self, state: ExecutionState) -> None:
        """Save or update the complete execution state."""
        ...

    async def get_state(self, execution_id: str) -> ExecutionState | None:
        """Get execution state by ID."""
        ...

    async def update_status(
        self, execution_id: str, status: ExecutionStatus, error: str | None = None
    ) -> None:
        """Update execution status."""
        ...

    async def get_node_output(
        self, execution_id: str, node_id: str
    ) -> NodeOutput | None:
        """Get output for a specific node."""
        ...

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        token_usage: TokenUsage | None = None,
    ) -> None:
        """Update output for a specific node."""
        ...

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: NodeExecutionStatus,
        error: str | None = None,
    ) -> None:
        """Update status for a specific node."""
        ...

    async def update_variables(
        self, execution_id: str, variables: dict[str, Any]
    ) -> None:
        """Update execution variables."""
        ...

    async def update_token_usage(self, execution_id: str, tokens: TokenUsage) -> None:
        """Update token usage (replaces existing)."""
        ...

    async def add_token_usage(self, execution_id: str, tokens: TokenUsage) -> None:
        """Add to token usage (increments existing)."""
        ...

    async def list_executions(
        self,
        diagram_id: DiagramID | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        """List executions with optional filtering."""
        ...

    async def cleanup_old_states(self, days: int = 7) -> None:
        """Clean up old execution states."""
        ...

    async def get_state_from_cache(self, execution_id: str) -> ExecutionState | None:
        """Get state from cache only (no DB lookup)."""
        ...

    async def create_execution_in_cache(
        self,
        execution_id: ExecutionID,
        diagram_id: DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        """Create execution in cache only."""
        ...

    async def persist_final_state(self, state: ExecutionState) -> None:
        """Persist final state from cache to database."""
        ...
