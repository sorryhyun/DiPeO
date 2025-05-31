"""Simplified execution state management."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time


@dataclass
class ExecutionContext:
    """Simplified execution state container.
    
    This class holds all the state needed during a single diagram execution,
    including node outputs, execution counts, and cost tracking.
    """
    
    execution_id: str
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    node_execution_counts: Dict[str, int] = field(default_factory=dict)
    total_cost: float = 0.0
    start_time: float = field(default_factory=time.time)
    errors: Dict[str, str] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    
    def increment_execution_count(self, node_id: str) -> int:
        """Increment and return the execution count for a node.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            The new execution count for the node
        """
        self.node_execution_counts[node_id] = self.node_execution_counts.get(node_id, 0) + 1
        return self.node_execution_counts[node_id]
    
    def set_node_output(self, node_id: str, output: Any, cost: float = 0.0) -> None:
        """Set the output for a node and update total cost.
        
        Args:
            node_id: The unique identifier of the node
            output: The output value from the node execution
            cost: The cost associated with this execution (default: 0.0)
        """
        self.node_outputs[node_id] = output
        self.total_cost += cost
        self.execution_order.append(node_id)
    
    def get_node_output(self, node_id: str) -> Optional[Any]:
        """Get the output of a specific node.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            The output value if node has been executed, None otherwise
        """
        return self.node_outputs.get(node_id)
    
    def get_execution_count(self, node_id: str) -> int:
        """Get the execution count for a node.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            The number of times the node has been executed
        """
        return self.node_execution_counts.get(node_id, 0)
    
    def set_error(self, node_id: str, error: str) -> None:
        """Record an error for a node.
        
        Args:
            node_id: The unique identifier of the node
            error: The error message
        """
        self.errors[node_id] = error
    
    def has_error(self, node_id: str) -> bool:
        """Check if a node has an error.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            True if the node has an error recorded
        """
        return node_id in self.errors
    
    def get_error(self, node_id: str) -> Optional[str]:
        """Get the error message for a node.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            The error message if exists, None otherwise
        """
        return self.errors.get(node_id)
    
    def get_execution_time(self) -> float:
        """Get the total execution time in seconds.
        
        Returns:
            Time elapsed since context creation in seconds
        """
        return time.time() - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution.
        
        Returns:
            Dictionary containing execution summary information
        """
        return {
            "execution_id": self.execution_id,
            "total_nodes_executed": len(self.node_outputs),
            "total_cost": self.total_cost,
            "execution_time": self.get_execution_time(),
            "error_count": len(self.errors),
            "execution_order": self.execution_order
        }