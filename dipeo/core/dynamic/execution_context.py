"""Protocol for managing execution context during diagram runtime."""

from abc import abstractmethod
from typing import Any, Optional, Protocol

from dipeo.diagram_generated import NodeID, NodeState
from dipeo.core.execution.node_output import NodeOutputProtocol


class ExecutionContext(Protocol):
    """Manages runtime execution state, dependencies, and node coordination."""
    
    
    
    @abstractmethod
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        ...
    
    @abstractmethod
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        ...
    
    
    
    @abstractmethod
    def get_completed_nodes(self) -> list[NodeID]:
        ...
    
    @abstractmethod
    def get_node_execution_count(self, node_id: NodeID) -> int:
        ...
    
    
    @abstractmethod
    def transition_node_to_running(self, node_id: NodeID) -> int:
        ...
    
    @abstractmethod
    def transition_node_to_completed(self, node_id: NodeID, output: Any = None, token_usage: dict[str, int] | None = None) -> None:
        ...
    
    @abstractmethod
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        ...
    
    @abstractmethod
    def transition_node_to_maxiter(self, node_id: NodeID, output: Optional[NodeOutputProtocol] = None) -> None:
        ...
    
    @abstractmethod
    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        ...
    
    @abstractmethod
    def reset_node(self, node_id: NodeID) -> None:
        ...


