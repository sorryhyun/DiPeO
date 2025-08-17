"""Protocol for managing execution context during diagram runtime."""

from abc import abstractmethod
from typing import Any, Optional, Protocol, Sequence

from dipeo.diagram_generated import NodeID, NodeState
from dipeo.domain.execution.envelope import Envelope


class ExecutionContext(Protocol):
    """Manages runtime execution state, dependencies, and node coordination.
    
    This protocol defines the contract for managing execution state during
    diagram runtime, including node states, results, and execution flow.
    """
    
    # Node State Queries
    
    @abstractmethod
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the current state of a node."""
        ...
    
    @abstractmethod
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node."""
        ...
    
    @abstractmethod
    def get_node_output(self, node_id: NodeID) -> Envelope | None:
        """Get the typed output of a completed node."""
        ...
    
    # Execution Status Queries
    
    @abstractmethod
    def get_completed_nodes(self) -> list[NodeID]:
        """Get all nodes that have completed execution."""
        ...
    
    @abstractmethod
    def get_running_nodes(self) -> list[NodeID]:
        """Get nodes currently in execution."""
        ...
    
    @abstractmethod
    def get_failed_nodes(self) -> list[NodeID]:
        """Get nodes that failed during execution."""
        ...
    
    @abstractmethod
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the number of times a node has been executed."""
        ...
    
    # State Transitions
    
    @abstractmethod
    def transition_node_to_running(self, node_id: NodeID) -> int:
        """Transition a node to running state. Returns execution count."""
        ...
    
    @abstractmethod
    def transition_node_to_completed(self, node_id: NodeID, output: Any = None, token_usage: dict[str, int] | None = None) -> None:
        """Transition a node to completed state with output."""
        ...
    
    @abstractmethod
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state with error message."""
        ...
    
    @abstractmethod
    def transition_node_to_maxiter(self, node_id: NodeID, output: Optional[Envelope] = None) -> None:
        """Transition a node to max iterations state."""
        ...
    
    @abstractmethod
    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state."""
        ...
    
    @abstractmethod
    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to initial state."""
        ...
    
    @abstractmethod
    def get_all_node_states(self) -> dict[NodeID, NodeState]:
        """Get all node states in the execution context."""
        ...
    
    # Runtime Context
    
    @abstractmethod
    def get_execution_metadata(self) -> dict[str, Any]:
        """Get global execution metadata."""
        ...
    
    @abstractmethod
    def set_execution_metadata(self, key: str, value: Any) -> None:
        """Set a value in global execution metadata."""
        ...
    
    @abstractmethod
    def get_node_metadata(self, node_id: NodeID) -> dict[str, Any]:
        """Get metadata for a specific node."""
        ...
    
    @abstractmethod
    def set_node_metadata(self, node_id: NodeID, key: str, value: Any) -> None:
        """Set metadata for a specific node."""
        ...
    
    # Dynamic Control Flow
    
    @abstractmethod
    def mark_branch_taken(self, node_id: NodeID, branch: str) -> None:
        """Mark which branch was taken from a conditional node."""
        ...
    
    @abstractmethod
    def get_branch_taken(self, node_id: NodeID) -> str | None:
        """Get which branch was taken from a conditional node."""
        ...
    
    @abstractmethod
    def is_loop_active(self, node_id: NodeID) -> bool:
        """Check if a loop node should continue iterating."""
        ...
    
    @abstractmethod
    def update_loop_state(self, node_id: NodeID, should_continue: bool) -> None:
        """Update the iteration state of a loop node."""
        ...


