"""Manages execution lifecycle and state for diagram execution."""

from typing import Any, Dict, Optional, Set
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionStateManager:
    """Manages execution lifecycle and tracks node execution state.
    
    This class maintains the state of diagram execution, tracking which nodes
    have been completed, their results, and the current execution position.
    It provides a centralized way to query and update execution progress.
    """
    
    def __init__(self):
        self.current_node: Optional[str] = None
        self.completed_nodes: Set[str] = set()
        self.node_results: Dict[str, Any] = {}
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.execution_errors: Dict[str, Exception] = {}
    
    def mark_node_complete(self, node_id: str, result: Any) -> None:
        """Mark a node as completed and store its result.
        
        Args:
            node_id: The ID of the completed node
            result: The execution result from the node
        """
        self.completed_nodes.add(node_id)
        self.node_results[node_id] = result
        
        # Clear current node if it matches
        if self.current_node == node_id:
            self.current_node = None
            
        logger.info(f"Node {node_id} marked as complete with result: {result}")
    
    def set_current_node(self, node_id: str) -> None:
        """Set the currently executing node.
        
        Args:
            node_id: The ID of the node currently being executed
        """
        self.current_node = node_id
        logger.debug(f"Current node set to: {node_id}")
    
    def is_node_complete(self, node_id: str) -> bool:
        """Check if a node has been completed.
        
        Args:
            node_id: The ID of the node to check
            
        Returns:
            True if the node has been completed, False otherwise
        """
        return node_id in self.completed_nodes
    
    def get_node_result(self, node_id: str) -> Optional[Any]:
        """Get the result of a completed node.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            The node's result if completed, None otherwise
        """
        return self.node_results.get(node_id)
    
    def mark_node_error(self, node_id: str, error: Exception) -> None:
        """Mark a node as having encountered an error.
        
        Args:
            node_id: The ID of the node that errored
            error: The exception that occurred
        """
        self.execution_errors[node_id] = error
        logger.error(f"Node {node_id} encountered error: {error}")
    
    def has_errors(self) -> bool:
        """Check if any nodes encountered errors during execution.
        
        Returns:
            True if there were errors, False otherwise
        """
        return len(self.execution_errors) > 0
    
    def get_progress(self) -> Dict[str, Any]:
        """Get the current execution progress.
        
        Returns:
            Dictionary containing progress information
        """
        total_completed = len(self.completed_nodes)
        
        return {
            "current_node": self.current_node,
            "completed_count": total_completed,
            "completed_nodes": list(self.completed_nodes),
            "has_errors": self.has_errors(),
            "error_count": len(self.execution_errors),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self._calculate_duration()
        }
    
    def finalize_execution(self) -> None:
        """Mark the execution as complete and record end time."""
        self.end_time = datetime.now()
        self.current_node = None
        logger.info(f"Execution finalized. Total nodes completed: {len(self.completed_nodes)}")
    
    def reset(self) -> None:
        """Reset the execution state for a new run."""
        self.current_node = None
        self.completed_nodes.clear()
        self.node_results.clear()
        self.execution_errors.clear()
        self.start_time = datetime.now()
        self.end_time = None
        logger.debug("Execution state reset")
    
    def _calculate_duration(self) -> Optional[float]:
        """Calculate the execution duration in seconds.
        
        Returns:
            Duration in seconds, or None if execution hasn't started
        """
        if not self.start_time:
            return None
            
        end = self.end_time or datetime.now()
        duration = (end - self.start_time).total_seconds()
        return duration
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a complete snapshot of the current execution state.
        
        Returns:
            Dictionary containing all state information
        """
        return {
            "current_node": self.current_node,
            "completed_nodes": list(self.completed_nodes),
            "node_results": self.node_results.copy(),
            "execution_errors": {
                node_id: str(error) 
                for node_id, error in self.execution_errors.items()
            },
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self._calculate_duration()
        }
    
    def __repr__(self) -> str:
        """String representation of the ExecutionStateManager."""
        return (f"ExecutionStateManager(current={self.current_node}, "
                f"completed={len(self.completed_nodes)}, "
                f"errors={len(self.execution_errors)})")