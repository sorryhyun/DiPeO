"""Protocol for managing execution context during diagram runtime."""

from typing import Protocol, Dict, Any, Optional, List
from abc import abstractmethod
from dipeo.models import NodeID, NodeState


class ExecutionContext(Protocol):
    """Manages the runtime context during diagram execution.
    
    This protocol defines the interface for tracking execution state,
    managing dependencies, and coordinating between nodes.
    """
    
    @abstractmethod
    def get_execution_id(self) -> str:
        """Get the unique identifier for this execution.
        
        Returns:
            The execution ID
        """
        ...
    
    @abstractmethod
    def get_current_node(self) -> Optional[NodeID]:
        """Get the currently executing node.
        
        Returns:
            The ID of the current node, or None if no node is executing
        """
        ...
    
    @abstractmethod
    def set_current_node(self, node_id: NodeID) -> None:
        """Set the currently executing node.
        
        Args:
            node_id: The ID of the node that is now executing
        """
        ...
    
    @abstractmethod
    def get_node_state(self, node_id: NodeID) -> Optional[NodeState]:
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
    def get_node_result(self, node_id: NodeID) -> Optional[Dict[str, Any]]:
        """Get the execution result of a completed node.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            The node's result, or None if not completed
        """
        ...
    
    @abstractmethod
    def set_node_result(self, node_id: NodeID, result: Dict[str, Any]) -> None:
        """Store the result of a node execution.
        
        Args:
            node_id: The ID of the node
            result: The execution result
        """
        ...
    
    @abstractmethod
    def get_global_context(self) -> Dict[str, Any]:
        """Get the global execution context shared across all nodes.
        
        Returns:
            The global context dictionary
        """
        ...
    
    @abstractmethod
    def update_global_context(self, updates: Dict[str, Any]) -> None:
        """Update the global execution context.
        
        Args:
            updates: Dictionary of values to merge into global context
        """
        ...
    
    @abstractmethod
    def get_completed_nodes(self) -> List[NodeID]:
        """Get list of all completed node IDs.
        
        Returns:
            List of node IDs that have completed execution
        """
        ...
    
    @abstractmethod
    def is_node_complete(self, node_id: NodeID) -> bool:
        """Check if a node has completed execution.
        
        Args:
            node_id: The ID of the node to check
            
        Returns:
            True if the node has completed, False otherwise
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


