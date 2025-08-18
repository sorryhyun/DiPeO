"""Execution observer protocol for monitoring diagram execution events."""

from typing import Protocol

from dipeo.diagram_generated import NodeState


class ExecutionObserver(Protocol):
    """Protocol for observing execution events."""

    async def on_execution_start(
        self, execution_id: str, diagram_id: str | None
    ) -> None: ...
    
    async def on_node_start(self, execution_id: str, node_id: str) -> None: ...
    
    async def on_node_complete(
        self, execution_id: str, node_id: str, state: NodeState
    ) -> None: ...
    
    async def on_node_error(
        self, execution_id: str, node_id: str, error: str
    ) -> None: ...
    
    async def on_execution_complete(self, execution_id: str) -> None: ...
    
    async def on_execution_error(self, execution_id: str, error: str) -> None: ...