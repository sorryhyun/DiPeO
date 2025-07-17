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
