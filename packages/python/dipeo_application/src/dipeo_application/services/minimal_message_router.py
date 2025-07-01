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
        """Send update (no-op for local execution)."""
        pass

    async def send_node_update(
        self, execution_id: str, node_id: str, update: dict[str, Any]
    ) -> None:
        """Send node-specific update (no-op for local execution)."""
        pass

    async def send_error(
        self, execution_id: str, error: str, details: dict[str, Any] | None = None
    ) -> None:
        """Send error message (no-op for local execution)."""
        pass

    async def broadcast(
        self, message: dict[str, Any]
    ) -> None:
        """Broadcast message to all subscribers (no-op for local execution)."""
        pass