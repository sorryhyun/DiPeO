"""Centralized skip decision making for node execution."""

from typing import Dict, Set, Optional


class SkipManager:
    """Centralized skip decision making for nodes in the execution graph.
    
    This class manages which nodes should be skipped during execution and why,
    providing a single source of truth for skip decisions across the system.
    """
    
    def __init__(self):
        self.skip_reasons: Dict[str, str] = {}
        self.skipped_nodes: Set[str] = set()
    
    def should_skip(self, node_id: str, execution_count: int, 
                    max_iterations: Optional[int]) -> bool:
        """Single source of truth for skip decisions.
        
        Args:
            node_id: The unique identifier of the node
            execution_count: How many times this node has been executed
            max_iterations: Maximum allowed iterations for the node
            
        Returns:
            True if the node should be skipped, False otherwise
        """
        if max_iterations and execution_count >= max_iterations:
            self.mark_skipped(node_id, "max_iterations_reached")
            return True
        return False
    
    def mark_skipped(self, node_id: str, reason: str) -> None:
        """Mark a node as skipped with a reason.
        
        Args:
            node_id: The unique identifier of the node
            reason: The reason why this node was skipped
        """
        self.skipped_nodes.add(node_id)
        self.skip_reasons[node_id] = reason
    
    def is_skipped(self, node_id: str) -> bool:
        """Check if a node has been marked as skipped.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            True if the node is marked as skipped
        """
        return node_id in self.skipped_nodes
    
    def get_skip_reason(self, node_id: str) -> Optional[str]:
        """Get the reason why a node was skipped.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            The skip reason if node was skipped, None otherwise
        """
        return self.skip_reasons.get(node_id)
    
    def clear(self) -> None:
        """Clear all skip information."""
        self.skip_reasons.clear()
        self.skipped_nodes.clear()
    
    def get_all_skipped_nodes(self) -> Dict[str, str]:
        """Get all skipped nodes and their reasons.
        
        Returns:
            Dictionary mapping node_id to skip reason
        """
        return dict(self.skip_reasons)