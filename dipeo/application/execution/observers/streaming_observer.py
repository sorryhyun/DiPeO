import asyncio
from datetime import datetime

from dipeo.core.ports import ExecutionObserver
from dipeo.models import (
    ExecutionStatus,
    NodeExecutionStatus,
    NodeState,
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
        self, execution_id: str, node_id: str, state: NodeState
    ):
        await self._publish(
            execution_id,
            {
                "type": "node_update",
                "execution_id": execution_id,
                "data": {
                    "node_id": node_id,
                    "state": state.status.value,
                    "output": state.output if state.output else None,
                    "started_at": state.started_at,
                    "ended_at": state.ended_at,
                    "token_usage": state.token_usage.model_dump() if state.token_usage else None,
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
