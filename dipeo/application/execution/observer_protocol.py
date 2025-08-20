"""Minimal observer protocol for sub-diagram support.

Note: This is kept only for backward compatibility with scoped_observer,
which is still needed for sub-diagram execution filtering.
The main execution flow uses the event-driven architecture instead.
"""

from typing import Protocol

from dipeo.diagram_generated import NodeState


class ExecutionObserver(Protocol):
    """Protocol for execution observers (minimal version for sub-diagrams)."""
    
    async def on_execution_start(self, execution_id: str, diagram_id: str | None) -> None:
        """Called when execution starts."""
        ...
    
    async def on_node_start(self, execution_id: str, node_id: str) -> None:
        """Called when a node starts executing."""
        ...
    
    async def on_node_complete(self, execution_id: str, node_id: str, state: NodeState) -> None:
        """Called when a node completes execution."""
        ...
    
    async def on_node_error(self, execution_id: str, node_id: str, error: str) -> None:
        """Called when a node encounters an error."""
        ...
    
    async def on_log_message(self, execution_id: str, node_id: str | None, message: str, level: str = "info") -> None:
        """Called when a log message is generated."""
        ...
    
    async def on_execution_complete(self, execution_id: str, status: str, error: str | None = None) -> None:
        """Called when execution completes."""
        ...