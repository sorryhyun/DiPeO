"""Minimal state store implementation for local/CLI execution."""

from datetime import datetime
from typing import Any

from dipeo.models import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeOutput,
    TokenUsage,
)


class MinimalStateStore:
    """Minimal state store for local execution.
    
    This implementation provides no-op methods for state management,
    suitable for CLI or local execution where persistence is not required.
    """

    async def create_execution(
        self, execution_id: str, diagram_id: str | None = None, variables: dict[str, Any] | None = None
    ) -> ExecutionState:
        """Create a minimal execution record."""
        now = datetime.now().isoformat()
        return ExecutionState(
            id=ExecutionID(execution_id),
            status=ExecutionStatus.PENDING,
            diagram_id=DiagramID(diagram_id) if diagram_id else None,
            started_at=now,
            ended_at=None,
            node_states={},
            node_outputs={},
            token_usage=TokenUsage(input=0, output=0, cached=None, total=0),
            error=None,
            variables=variables or {},
            is_active=True,
        )

    async def create_execution_in_cache(
        self, execution_id: str, diagram_id: str | None, variables: dict[str, Any]
    ) -> ExecutionState:
        """Create execution in cache (same as create_execution for minimal store)."""
        return await self.create_execution(execution_id, diagram_id, variables)

    async def get_state(self, execution_id: str) -> ExecutionState | None:
        """Get execution state by ID (always returns None for minimal store)."""
        return None

    async def save_state(self, state: ExecutionState) -> None:
        """Save execution state (no-op for minimal store)."""
        pass

    async def update_node_state(
        self, execution_id: str, node_id: str, state: str
    ) -> None:
        pass

    async def update_node_status(
        self, execution_id: str, node_id: str, status: NodeExecutionStatus, error: str | None = None
    ) -> None:
        pass

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        token_usage: TokenUsage | None = None,
    ) -> None:
        pass

    async def update_status(
        self, execution_id: str, status: ExecutionStatus, error: str | None = None
    ) -> None:
        pass

    async def get_execution_state(self, execution_id: str) -> dict[str, Any] | None:
        """Deprecated method - use get_state instead."""
        return None

    async def save_execution_result(
        self, execution_id: str, result: dict[str, Any]
    ) -> None:
        pass

    async def get_node_output(
        self, execution_id: str, node_id: str
    ) -> NodeOutput | None:
        """Get output for a specific node."""
        return None

    async def update_variables(
        self, execution_id: str, variables: dict[str, Any]
    ) -> None:
        """Update execution variables."""
        pass

    async def update_token_usage(self, execution_id: str, tokens: TokenUsage) -> None:
        """Update token usage (replaces existing)."""
        pass

    async def add_token_usage(self, execution_id: str, tokens: TokenUsage) -> None:
        """Add to token usage (increments existing)."""
        pass

    async def list_executions(
        self,
        diagram_id: DiagramID | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        """List executions with optional filtering."""
        return []

    async def cleanup_old_states(self, days: int = 7) -> None:
        """Clean up old execution states."""
        pass

    async def get_state_from_cache(self, execution_id: str) -> ExecutionState | None:
        """Get state from cache only (no DB lookup)."""
        return None

    async def persist_final_state(self, state: ExecutionState) -> None:
        """Persist final state from cache to database."""
        pass

    async def initialize(self) -> None:
        """Initialize the state store."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass