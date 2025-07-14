"""Execution observers for server-specific functionality."""

import asyncio
from datetime import datetime

from dipeo.core.ports import ExecutionObserver
from dipeo.models import (
    ExecutionStatus,
    NodeExecutionStatus,
    NodeState,
)


class StateStoreObserver(ExecutionObserver):
    """Observer that persists execution state."""

    def __init__(self, state_store):
        self.state_store = state_store

    async def on_execution_start(self, execution_id: str, diagram_id: str | None):
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if execution already exists
        existing = await self.state_store.get_state(execution_id)
        if not existing:
            await self.state_store.create_execution(execution_id, diagram_id)
        else:
            logger.debug(f"StateStoreObserver: Execution {execution_id} already exists, skipping creation")

    async def on_node_start(self, execution_id: str, node_id: str):
        await self.state_store.update_node_status(
            execution_id, node_id, NodeExecutionStatus.RUNNING
        )

    async def on_node_complete(
        self, execution_id: str, node_id: str, state: NodeState
    ):
        # Update node status
        await self.state_store.update_node_status(
            execution_id, node_id, state.status
        )

        # Store the output separately if available
        if state.output:
            await self.state_store.update_node_output(
                execution_id, node_id, state.output, token_usage=state.token_usage
            )

    async def on_node_error(self, execution_id: str, node_id: str, error: str):
        await self.state_store.update_node_status(
            execution_id, node_id, NodeExecutionStatus.FAILED, error=error
        )

    async def on_execution_complete(self, execution_id: str):
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"StateStoreObserver: Updating execution {execution_id} to COMPLETED")
        
        await self.state_store.update_status(execution_id, ExecutionStatus.COMPLETED)
        # Small delay to ensure state is fully persisted
        import asyncio

        await asyncio.sleep(0.1)
        
        # Verify the state was saved
        state = await self.state_store.get_state(execution_id)
        if not state:
            logger.error(f"StateStoreObserver: Failed to verify execution {execution_id} after completion")

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
                    "output": state.output.model_dump() if state.output else None,
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
