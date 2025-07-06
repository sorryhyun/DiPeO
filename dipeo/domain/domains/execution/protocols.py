"""Execution observer protocol for monitoring execution events."""

from typing import Protocol, Optional

from ...models import NodeState


class ExecutionObserver(Protocol):
    """Observers for execution events."""

    async def on_execution_start(
        self, execution_id: str, diagram_id: Optional[str]
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