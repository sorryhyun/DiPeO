"""Protocol for managing execution context during diagram runtime."""

from abc import abstractmethod
from typing import Any, Optional, Protocol

from dipeo.models import NodeID, NodeState
from dipeo.core.execution.node_output import NodeOutputProtocol


class ExecutionContext(Protocol):
    """Manages the runtime context during diagram execution.
    
    This protocol defines the interface for tracking execution state,
    managing dependencies, and coordinating between nodes.
    """
    
    
    
    @abstractmethod
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the execution state of a specific node.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            The node's state, or None if not yet executed
        """
        ...
    
    @abstractmethod
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            The node's result, or None if not completed
        """
        ...
    
    
    
    @abstractmethod
    def get_completed_nodes(self) -> list[NodeID]:
        """Get list of all completed node IDs.
        
        Returns:
            List of node IDs that have completed execution
        """
        ...
    
    @abstractmethod
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the execution count for a specific node.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            The number of times this node has been executed
        """
        ...
    
    # ========== State Transitions ==========
    # These methods provide standardized state management
    
    @abstractmethod
    def transition_node_to_running(self, node_id: NodeID) -> int:
        """Transition a node to running state.
        
        This should increment execution count and update state atomically.
        
        Args:
            node_id: The ID of the node to transition
            
        Returns:
            The execution number for this run
        """
        ...
    
    @abstractmethod
    def transition_node_to_completed(self, node_id: NodeID, output: Any = None) -> None:
        """Transition a node to completed state with optional output.
        
        Args:
            node_id: The ID of the node to transition
            output: Optional output from the node execution
        """
        ...
    
    @abstractmethod
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state.
        
        Args:
            node_id: The ID of the node to transition
            error: Error message describing the failure
        """
        ...
    
    @abstractmethod
    def transition_node_to_maxiter(self, node_id: NodeID, output: Optional[NodeOutputProtocol] = None) -> None:
        """Transition a node to max iterations reached state.
        
        Args:
            node_id: The ID of the node to transition
            output: Optional output from the node execution
        """
        ...
    
    @abstractmethod
    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state.
        
        Args:
            node_id: The ID of the node to transition
        """
        ...
    
    @abstractmethod
    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to pending state (for loops).
        
        This should clear the node's output and reset its state.
        
        Args:
            node_id: The ID of the node to reset
        """
        ...


