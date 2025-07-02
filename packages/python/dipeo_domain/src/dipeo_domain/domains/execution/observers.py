"""Execution observers for server-specific functionality."""

import asyncio
from datetime import datetime

from dipeo_domain.models import (
    ExecutionStatus,
    NodeExecutionStatus,
    NodeOutput,
    TokenUsage,
)
from dipeo_application.execution_engine import ExecutionObserver


class StateStoreObserver(ExecutionObserver):
    """Observer that persists execution state."""

    def __init__(self, state_store):
        self.state_store = state_store

    async def on_execution_start(self, execution_id: str, diagram_id: str | None):
        await self.state_store.create_execution(execution_id, diagram_id)

    async def on_node_start(self, execution_id: str, node_id: str):
        await self.state_store.update_node_status(
            execution_id, node_id, NodeExecutionStatus.RUNNING
        )

    async def on_node_complete(
        self, execution_id: str, node_id: str, output: NodeOutput
    ):
        # Update node status
        await self.state_store.update_node_status(
            execution_id, node_id, NodeExecutionStatus.COMPLETED
        )

        # Store the output separately
        token_usage = None
        if output.metadata:
            if "token_usage" in output.metadata:
                token_usage = TokenUsage(**output.metadata["token_usage"])

        await self.state_store.update_node_output(
            execution_id, node_id, output, token_usage=token_usage
        )

    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        await self.state_store.update_node_status(
            execution_id, node_id, NodeExecutionStatus.FAILED, error=error
        )

    async def on_execution_complete(self, execution_id: str):
        await self.state_store.update_status(execution_id, ExecutionStatus.COMPLETED)
        # Small delay to ensure state is fully persisted
        import asyncio

        await asyncio.sleep(0.1)

    async def on_execution_error(self, execution_id: str, error: str):
        await self.state_store.update_status(
            execution_id, ExecutionStatus.FAILED, error
        )


class StreamingObserver(ExecutionObserver):
    """Observer that publishes real-time updates."""

    def __init__(self, message_router):
        self.message_router = message_router
        self._queues: dict[str, asyncio.Queue] = {}

    async def subscribe(self, execution_id: str) -> asyncio.Queue:
        """Subscribe to execution updates."""
        if execution_id not in self._queues:
            self._queues[execution_id] = asyncio.Queue()
        return self._queues[execution_id]

    async def on_execution_start(self, execution_id: str, diagram_id: str | None):
        await self._publish(
            execution_id,
            {
                "type": "execution_start",
                "execution_id": execution_id,
                "diagram_id": diagram_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def on_node_start(self, execution_id: str, node_id: str):
        await self._publish(
            execution_id,
            {
                "type": "node_update",
                "execution_id": execution_id,
                "data": {
                    "node_id": node_id,
                    "state": NodeExecutionStatus.RUNNING.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )

    async def on_node_complete(
        self, execution_id: str, node_id: str, output: NodeOutput
    ):
        await self._publish(
            execution_id,
            {
                "type": "node_update",
                "execution_id": execution_id,
                "data": {
                    "node_id": node_id,
                    "state": NodeExecutionStatus.COMPLETED.value,
                    "output": output.model_dump() if output else None,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )

    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        await self._publish(
            execution_id,
            {
                "type": "node_update",
                "execution_id": execution_id,
                "data": {
                    "node_id": node_id,
                    "state": NodeExecutionStatus.FAILED.value,
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )

    async def on_execution_complete(self, execution_id: str):
        await self._publish(
            execution_id,
            {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": "completed",
            },
        )

    async def on_execution_error(self, execution_id: str, error: str):
        await self._publish(
            execution_id,
            {
                "type": "execution_error",
                "execution_id": execution_id,
                "error": error,
            },
        )

    async def _publish(self, execution_id: str, update: dict):
        """Publish update to subscribers."""
        # Publish to message router
        await self.message_router.broadcast_to_execution(execution_id, update)

        # Also publish to direct queue if exists
        if execution_id in self._queues:
            await self._queues[execution_id].put(update)
