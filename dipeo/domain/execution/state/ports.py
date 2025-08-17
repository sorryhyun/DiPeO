"""Domain ports for execution state management."""

from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dipeo.diagram_generated import (
        DiagramID,
        ExecutionID,
        ExecutionState,
        Status,
        TokenUsage,
    )


@runtime_checkable
class ExecutionStateRepository(Protocol):
    """Repository for execution state persistence."""

    async def create_execution(
        self,
        execution_id: "ExecutionID",
        diagram_id: Optional["DiagramID"] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> "ExecutionState":
        """Create a new execution state."""
        ...

    async def get_execution(self, execution_id: str) -> Optional["ExecutionState"]:
        """Get execution state by ID."""
        ...

    async def save_execution(self, state: "ExecutionState") -> None:
        """Save or update execution state."""
        ...

    async def update_status(
        self, execution_id: str, status: "Status", error: Optional[str] = None
    ) -> None:
        """Update execution status."""
        ...

    async def get_node_output(
        self, execution_id: str, node_id: str
    ) -> Optional[dict[str, Any]]:
        """Get output for a specific node."""
        ...

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        is_exception: bool = False,
        token_usage: Optional["TokenUsage"] = None,
    ) -> None:
        """Update output for a specific node."""
        ...

    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: "Status",
        error: Optional[str] = None,
    ) -> None:
        """Update status for a specific node."""
        ...

    async def list_executions(
        self,
        diagram_id: Optional["DiagramID"] = None,
        status: Optional["Status"] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list["ExecutionState"]:
        """List executions with optional filtering."""
        ...

    async def cleanup_old_executions(self, days: int = 7) -> None:
        """Clean up old execution states."""
        ...


@runtime_checkable
class ExecutionStateService(Protocol):
    """High-level service for execution state management."""

    async def start_execution(
        self,
        execution_id: "ExecutionID",
        diagram_id: Optional["DiagramID"] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> "ExecutionState":
        """Start a new execution."""
        ...

    async def finish_execution(
        self,
        execution_id: str,
        status: "Status",
        error: Optional[str] = None,
    ) -> None:
        """Finish an execution with final status."""
        ...

    async def update_node_execution(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        status: "Status",
        is_exception: bool = False,
        token_usage: Optional["TokenUsage"] = None,
        error: Optional[str] = None,
    ) -> None:
        """Atomically update node execution state."""
        ...

    async def append_token_usage(
        self, execution_id: str, tokens: "TokenUsage"
    ) -> None:
        """Append to cumulative token usage."""
        ...

    async def get_execution_state(self, execution_id: str) -> Optional["ExecutionState"]:
        """Get current execution state."""
        ...


@runtime_checkable
class ExecutionCachePort(Protocol):
    """Optional cache layer for execution state."""

    async def get_state_from_cache(self, execution_id: str) -> Optional["ExecutionState"]:
        """Get state from cache only (no DB lookup)."""
        ...

    async def create_execution_in_cache(
        self,
        execution_id: "ExecutionID",
        diagram_id: Optional["DiagramID"] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> "ExecutionState":
        """Create execution in cache only."""
        ...

    async def persist_final_state(self, state: "ExecutionState") -> None:
        """Persist final state from cache to database."""
        ...