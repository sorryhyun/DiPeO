"""Minimal message router implementation for local/CLI execution."""

from typing import Any


class MinimalMessageRouter:
    """Minimal message router for local execution.
    
    This implementation provides no-op methods for message routing,
    suitable for CLI or local execution where real-time updates are not required.
    """

    async def send_update(
        self, execution_id: str, update: dict[str, Any]
    ) -> None:
        pass

    async def send_node_update(
        self, execution_id: str, node_id: str, update: dict[str, Any]
    ) -> None:
        pass

    async def send_error(
        self, execution_id: str, error: str, details: dict[str, Any] | None = None
    ) -> None:
        pass

    async def broadcast(
        self, message: dict[str, Any]
    ) -> None:
        pass

    async def broadcast_to_execution(
        self, execution_id: str, update: dict[str, Any]
    ) -> None:
        """Broadcast update to specific execution."""
        pass