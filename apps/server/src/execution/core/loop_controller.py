"""Loop controller for managing explicit loop execution state."""

from typing import List


class LoopController:
    """Manages loop execution state."""
    
    def __init__(self, max_iterations: int, loop_nodes: List[str]):
        """Initialize loop controller.
        
        Args:
            max_iterations: Maximum number of iterations allowed
            loop_nodes: List of node IDs that are part of the loop
        """
        self.max_iterations = max_iterations
        self.loop_nodes = loop_nodes
        self.current_iteration = 0
    
    def should_continue(self) -> bool:
        """Check if loop should continue executing.
        
        Returns:
            True if more iterations are allowed, False otherwise
        """
        return self.current_iteration < self.max_iterations
    
    def mark_iteration_complete(self) -> None:
        """Mark current iteration as complete and increment counter."""
        self.current_iteration += 1
    
    def get_current_iteration(self) -> int:
        """Get current iteration number (0-based)."""
        return self.current_iteration
    
    def get_remaining_iterations(self) -> int:
        """Get number of remaining iterations."""
        return max(0, self.max_iterations - self.current_iteration)
    
    def is_node_in_loop(self, node_id: str) -> bool:
        """Check if a node is part of this loop.
        
        Args:
            node_id: ID of node to check
            
        Returns:
            True if node is part of the loop, False otherwise
        """
        return node_id in self.loop_nodes
    
    def reset(self) -> None:
        """Reset loop controller to initial state."""
        self.current_iteration = 0