"""Adapters that bridge existing infrastructure to new domain ports."""

from typing import Any, Optional

from dipeo.core.ports import StateStorePort
from dipeo.diagram_generated import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    Status,
    TokenUsage,
)
from dipeo.domain.execution.state import (
    ExecutionCachePort,
    ExecutionStateRepository,
    ExecutionStateService,
)
from dipeo.infrastructure.state import EventBasedStateStore


class StateRepositoryAdapter(ExecutionStateRepository):
    """Adapter wrapping EventBasedStateStore to implement ExecutionStateRepository."""

    def __init__(self, state_store: StateStorePort | None = None):
        self._store = state_store or EventBasedStateStore()

    async def initialize(self):
        """Initialize the underlying store."""
        await self._store.initialize()

    async def cleanup(self):
        """Cleanup resources."""
        await self._store.cleanup()

    async def create_execution(
        self,
        execution_id: ExecutionID,
        diagram_id: Optional[DiagramID] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> ExecutionState:
        # Use the existing create_execution which returns ExecutionState
        return await self._store.create_execution(
            execution_id=execution_id,
            diagram_id=diagram_id,
            variables=variables,
        )

    async def get_execution(self, execution_id: str) -> Optional[ExecutionState]:
        return await self._store.get_state(execution_id)

    async def save_execution(self, state: ExecutionState) -> None:
        await self._store.save_state(state)

    async def update_status(
        self, execution_id: str, status: Status, error: Optional[str] = None
    ) -> None:
        # Status is already the correct type, just pass through
        await self._store.update_status(execution_id, status, error)

    async def get_node_output(
        self, execution_id: str, node_id: str
    ) -> Optional[dict[str, Any]]:
        return await self._store.get_node_output(execution_id, node_id)

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        token_usage: Optional[TokenUsage] = None,
    ) -> None:
        await self._store.update_node_output(
            execution_id, node_id, output, is_exception, token_usage
        )

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: Status,
        error: Optional[str] = None,
    ) -> None:
        # Status is already the correct type, just pass through
        await self._store.update_node_status(
            execution_id, node_id, status, error
        )

    async def list_executions(
        self,
        diagram_id: Optional[DiagramID] = None,
        status: Optional[Status] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionState]:
        # Status is already the correct type, just pass through
        return await self._store.list_executions(diagram_id, status, limit, offset)

    async def cleanup_old_executions(self, days: int = 7) -> None:
        await self._store.cleanup_old_states(days)


class StateServiceAdapter(ExecutionStateService):
    """Adapter implementing ExecutionStateService using StateRepositoryAdapter."""

    def __init__(self, repository: ExecutionStateRepository | None = None):
        self._repository = repository or StateRepositoryAdapter()

    async def start_execution(
        self,
        execution_id: ExecutionID,
        diagram_id: Optional[DiagramID] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> ExecutionState:
        state = await self._repository.create_execution(execution_id, diagram_id, variables)
        await self._repository.update_status(str(execution_id), Status.RUNNING)
        # Re-fetch to get updated status
        updated_state = await self._repository.get_execution(str(execution_id))
        return updated_state

    async def finish_execution(
        self,
        execution_id: str,
        status: Status,
        error: Optional[str] = None,
    ) -> None:
        await self._repository.update_status(execution_id, status, error)

    async def update_node_execution(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        status: Status,
        is_exception: bool = False,
        token_usage: Optional[TokenUsage] = None,
        error: Optional[str] = None,
    ) -> None:
        await self._repository.update_node_output(
            execution_id, node_id, output, is_exception, token_usage
        )
        await self._repository.update_node_status(execution_id, node_id, status, error)

    async def append_token_usage(
        self, execution_id: str, tokens: TokenUsage
    ) -> None:
        # Use the store's add_token_usage directly
        if hasattr(self._repository, '_store'):
            await self._repository._store.add_token_usage(execution_id, tokens)
        else:
            # Fallback: fetch state, update, save
            state = await self._repository.get_execution(execution_id)
            if state and state.token_usage:
                state.token_usage.input += tokens.input
                state.token_usage.output += tokens.output
                if tokens.cached:
                    state.token_usage.cached = (state.token_usage.cached or 0) + tokens.cached
                state.token_usage.total = state.token_usage.input + state.token_usage.output
                await self._repository.save_execution(state)

    async def get_execution_state(self, execution_id: str) -> Optional[ExecutionState]:
        return await self._repository.get_execution(execution_id)


class StateCacheAdapter(ExecutionCachePort):
    """Adapter implementing ExecutionCachePort using EventBasedStateStore's cache."""

    def __init__(self, state_store: StateStorePort | None = None):
        self._store = state_store or EventBasedStateStore()

    async def get_state_from_cache(self, execution_id: str) -> Optional[ExecutionState]:
        # Use the execution cache directly
        if hasattr(self._store, '_execution_cache'):
            cache = await self._store._execution_cache.get_cache(execution_id)
            return await cache.get_state()
        return None

    async def create_execution_in_cache(
        self,
        execution_id: ExecutionID,
        diagram_id: Optional[DiagramID] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> ExecutionState:
        # Create in store which automatically caches
        return await self._store.create_execution(
            execution_id=execution_id,
            diagram_id=diagram_id,
            variables=variables,
        )

    async def persist_final_state(self, state: ExecutionState) -> None:
        # Use the store's persist_final_state which handles cache removal
        await self._store.persist_final_state(state)