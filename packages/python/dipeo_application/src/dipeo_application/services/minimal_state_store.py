"""Minimal state store implementation for local/CLI execution."""

from typing import Any


class MinimalStateStore:
    """Minimal state store for local execution.
    
    This implementation provides no-op methods for state management,
    suitable for CLI or local execution where persistence is not required.
    """

    async def create_execution_in_cache(
        self, execution_id: str, diagram_id: str | None, variables: dict[str, Any]
    ) -> None:
        """Create execution record (no-op for local execution)."""
        pass

    async def update_node_state(
        self, execution_id: str, node_id: str, state: str
    ) -> None:
        """Update node state (no-op for local execution)."""
        pass

    async def get_execution_state(self, execution_id: str) -> dict[str, Any] | None:
        """Get execution state (returns None for local execution)."""
        return None

    async def save_execution_result(
        self, execution_id: str, result: dict[str, Any]
    ) -> None:
        """Save execution result (no-op for local execution)."""
        pass