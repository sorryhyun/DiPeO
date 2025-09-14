"""Adapters that bridge existing infrastructure to new domain ports."""

from typing import Any

from dipeo.diagram_generated import (
    DiagramID,
    ExecutionID,
    ExecutionState,
    LLMUsage,
    Status,
)
from dipeo.domain.execution.state import (
    ExecutionCachePort,
    ExecutionStateRepository,
    ExecutionStateService,
)
from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort


class StateServiceAdapter(ExecutionStateService):
    """Adapter implementing ExecutionStateService using ExecutionStateRepository."""

    def __init__(self, repository: ExecutionStateRepository):
        self._repository = repository

    async def start_execution(
        self,
        execution_id: ExecutionID,
        diagram_id: DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        await self._repository.create_execution(execution_id, diagram_id, variables)
        await self._repository.update_status(str(execution_id), Status.RUNNING)
        updated_state = await self._repository.get_execution(str(execution_id))
        return updated_state

    async def finish_execution(
        self,
        execution_id: str,
        status: Status,
        error: str | None = None,
    ) -> None:
        await self._repository.update_status(execution_id, status, error)

    async def update_node_execution(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        status: Status,
        is_exception: bool = False,
        llm_usage: LLMUsage | None = None,
        error: str | None = None,
    ) -> None:
        await self._repository.update_node_output(
            execution_id, node_id, output, is_exception, llm_usage
        )
        await self._repository.update_node_status(execution_id, node_id, status, error)

    async def append_llm_usage(self, execution_id: str, usage: LLMUsage) -> None:
        if hasattr(self._repository, "add_llm_usage"):
            await self._repository.add_llm_usage(execution_id, usage)
        else:
            state = await self._repository.get_execution(execution_id)
            if state and state.llm_usage:
                state.llm_usage.input += usage.input
                state.llm_usage.output += usage.output
                if usage.cached:
                    state.llm_usage.cached = (state.llm_usage.cached or 0) + usage.cached
                state.llm_usage.total = state.llm_usage.input + state.llm_usage.output
                await self._repository.save_execution(state)

    async def get_execution_state(self, execution_id: str) -> ExecutionState | None:
        return await self._repository.get_execution(execution_id)


class StateCacheAdapter(ExecutionCachePort):
    """Adapter implementing ExecutionCachePort using state store's cache."""

    def __init__(self, state_store: StateStorePort):
        self._store = state_store

    async def get_state_from_cache(self, execution_id: str) -> ExecutionState | None:
        if hasattr(self._store, "_execution_cache"):
            cache = await self._store._execution_cache.get_cache(execution_id)
            return await cache.get_state()
        return None

    async def create_execution_in_cache(
        self,
        execution_id: ExecutionID,
        diagram_id: DiagramID | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionState:
        return await self._store.create_execution(
            execution_id=execution_id,
            diagram_id=diagram_id,
            variables=variables,
        )

    async def persist_final_state(self, state: ExecutionState) -> None:
        await self._store.persist_final_state(state)
