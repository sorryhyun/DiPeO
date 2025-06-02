from typing import Dict, Set, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class IterationStats:
    """Statistics about loop iterations"""
    total_iterations: Dict[str, int] = field(default_factory=dict)
    max_iterations_map: Dict[str, int] = field(default_factory=dict)
    nodes_at_max: Set[str] = field(default_factory=set)
    all_nodes_at_max: bool = False


class LoopController:
    """
    Manages loop execution state, tracking iterations for nodes and
    determining when loops should terminate.
    """
    
    def __init__(self, max_iterations: int = 100):
        """
        Initialize loop controller.
        
        Args:
            max_iterations: Global maximum iteration limit for safety
        """
        self.iteration_counts: Dict[str, int] = {}
        self.max_iterations = max_iterations
        self.loop_nodes: Set[str] = set()
        self.node_max_iterations: Dict[str, int] = {}
        self.logger = logger
    
    def register_loop_node(self, node_id: str, max_iterations: Optional[int] = None) -> None:
        """
        Register a node as part of a loop with optional max iterations.
        
        Args:
            node_id: The node ID to register
            max_iterations: Node-specific max iterations (overrides global)
        """
        self.loop_nodes.add(node_id)
        if max_iterations is not None:
            self.node_max_iterations[node_id] = max_iterations
        
        # Initialize iteration count if not exists
        if node_id not in self.iteration_counts:
            self.iteration_counts[node_id] = 0
    
    def should_continue_loop(self, node_id: str) -> bool:
        """
        Check if a node should continue iterating.
        
        Args:
            node_id: The node to check
            
        Returns:
            True if the node should continue, False if it should stop
        """
        if node_id not in self.loop_nodes:
            # Not a loop node, always continue
            return True
        
        current_count = self.iteration_counts.get(node_id, 0)
        
        # Check node-specific limit first
        if node_id in self.node_max_iterations:
            max_iter = self.node_max_iterations[node_id]
            if current_count >= max_iter:
                self.logger.info(f"Node {node_id} reached max iterations: {max_iter}")
                return False
        
        # Check global limit
        if current_count >= self.max_iterations:
            self.logger.warning(f"Node {node_id} reached global max iterations: {self.max_iterations}")
            return False
        
        return True
    
    def increment_iteration(self, node_id: str) -> int:
        """
        Increment iteration count for a node.
        
        Args:
            node_id: The node to increment
            
        Returns:
            The new iteration count
        """
        if node_id not in self.iteration_counts:
            self.iteration_counts[node_id] = 0
        
        self.iteration_counts[node_id] += 1
        return self.iteration_counts[node_id]
    
    def reset_iterations(self, node_id: str) -> None:
        """
        Reset iteration count for a node.
        
        Args:
            node_id: The node to reset
        """
        self.iteration_counts[node_id] = 0
        self.logger.debug(f"Reset iterations for node {node_id}")
    
    def get_iteration_count(self, node_id: str) -> int:
        """
        Get current iteration count for a node (0-based).
        
        Args:
            node_id: The node to check
            
        Returns:
            Current iteration count (0 if never executed)
        """
        return self.iteration_counts.get(node_id, 0)
    
    def get_remaining_iterations(self, node_id: str) -> Optional[int]:
        """
        Calculate remaining iterations for a node.
        
        Args:
            node_id: The node to check
            
        Returns:
            Number of remaining iterations, or None if unlimited
        """
        current = self.get_iteration_count(node_id)
        
        # Check node-specific limit
        if node_id in self.node_max_iterations:
            max_iter = self.node_max_iterations[node_id]
            return max(0, max_iter - current)
        
        # Check if approaching global limit
        if current < self.max_iterations:
            return self.max_iterations - current
        
        return 0
    
    def has_any_node_reached_max_iterations(self) -> bool:
        """
        Check if ANY node has reached its max iteration limit.
        
        Returns:
            True if any node has reached its limit
        """
        for node_id in self.loop_nodes:
            current = self.iteration_counts.get(node_id, 0)
            
            # Check node-specific limit
            if node_id in self.node_max_iterations:
                if current >= self.node_max_iterations[node_id]:
                    return True
            
            # Check global limit
            if current >= self.max_iterations:
                return True
        
        return False
    
    def have_all_nodes_reached_max_iterations(self) -> bool:
        """
        Check if ALL loop nodes have reached their max iteration limits.
        This is used by condition nodes to determine loop exit.
        
        Returns:
            True if all loop nodes have reached their limits
        """
        if not self.loop_nodes:
            return False
        
        for node_id in self.loop_nodes:
            current = self.iteration_counts.get(node_id, 0)
            
            # Check node-specific limit
            if node_id in self.node_max_iterations:
                if current < self.node_max_iterations[node_id]:
                    return False
            else:
                # If no specific limit, use global limit
                if current < self.max_iterations:
                    return False
        
        return True
    
    def get_iteration_stats(self) -> IterationStats:
        """
        Get comprehensive iteration statistics.
        
        Returns:
            IterationStats object with detailed information
        """
        stats = IterationStats()
        
        # Collect iteration counts and limits
        for node_id in self.loop_nodes:
            current = self.iteration_counts.get(node_id, 0)
            stats.total_iterations[node_id] = current
            
            # Determine effective max for this node
            if node_id in self.node_max_iterations:
                max_iter = self.node_max_iterations[node_id]
            else:
                max_iter = self.max_iterations
            
            stats.max_iterations_map[node_id] = max_iter
            
            # Check if at max
            if current >= max_iter:
                stats.nodes_at_max.add(node_id)
        
        # Check if all nodes at max
        stats.all_nodes_at_max = (
            len(stats.nodes_at_max) == len(self.loop_nodes) 
            and len(self.loop_nodes) > 0
        )
        
        return stats
    
    def mark_iteration_complete(self, node_id: str) -> Tuple[bool, int]:
        """
        Mark an iteration as complete for a node.
        Combines increment and continuation check.
        
        Args:
            node_id: The node that completed an iteration
            
        Returns:
            Tuple of (should_continue, new_iteration_count)
        """
        new_count = self.increment_iteration(node_id)
        should_continue = self.should_continue_loop(node_id)
        
        return should_continue, new_count
    
    def create_sub_controller(self, node_ids: List[str]) -> 'LoopController':
        """
        Create a new loop controller for a subset of nodes.
        Useful for nested loops or sub-workflows.
        
        Args:
            node_ids: List of node IDs for the sub-controller
            
        Returns:
            New LoopController instance
        """
        sub_controller = LoopController(max_iterations=self.max_iterations)
        
        # Copy relevant node configurations
        for node_id in node_ids:
            if node_id in self.loop_nodes:
                max_iter = self.node_max_iterations.get(node_id)
                sub_controller.register_loop_node(node_id, max_iter)
        
        return sub_controller
    
    def update_from_node_properties(self, node: Dict) -> None:
        """
        Update loop configuration from node properties.
        Specifically handles PersonJob nodes with max_iterations.
        
        Args:
            node: Node dictionary with properties
        """
        node_id = node.get("id")
        node_type = node.get("type")
        properties = node.get("properties", {})
        
        # Check for max_iterations in node properties
        if "max_iterations" in properties:
            max_iter = properties["max_iterations"]
            if isinstance(max_iter, int) and max_iter > 0:
                self.register_loop_node(node_id, max_iter)
                self.logger.debug(f"Registered loop node {node_id} with max_iterations={max_iter}")
        
        # PersonJob and PersonBatchJob nodes can be loop nodes
        elif node_type in ["personjob", "personbatchjob"]:
            # Check if they have loop-related properties
            if properties.get("firstOnlyPrompt") or properties.get("iterationPrompt"):
                self.register_loop_node(node_id)
                self.logger.debug(f"Registered {node_type} node {node_id} as loop node")