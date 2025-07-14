"""Protocol for managing execution context during diagram runtime."""

from abc import abstractmethod
from typing import Any, Protocol

from dipeo.models import NodeID, NodeState


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
    def set_node_state(self, node_id: NodeID, state: NodeState) -> None:
        """Set the execution state of a node.
        
        Args:
            node_id: The ID of the node
            state: The new state
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
    def get_variable(self, key: str) -> Any:
        """Get a variable from the execution context.
        
        Args:
            key: The variable key
            
        Returns:
            The variable value, or None if not found
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


