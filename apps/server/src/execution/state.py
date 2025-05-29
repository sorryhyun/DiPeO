"""Execution state management for diagram processing."""

from dataclasses import dataclass
from collections import Counter
from typing import Any, Dict


@dataclass
class ExecutionState:
    """Holds mutable state during diagram execution.
    
    Attributes:
        context: Dictionary of execution variables and their values
        condition_values: Cached condition evaluation results 
        counts: Counter tracking execution iterations per node
        total_cost: Accumulated cost of LLM calls in USD
        node_max_iterations: Maximum allowed iterations per node
    """
    context: Dict[str, Any]
    condition_values: Dict[str, bool]
    counts: Counter
    total_cost: float
    node_max_iterations: Dict[str, int]
    
    @classmethod
    def create_initial(cls, initial_context: Dict[str, Any] = None, 
                      node_max_iterations: Dict[str, int] = None) -> 'ExecutionState':
        """Factory method to create initial execution state."""
        return cls(
            context=initial_context or {},
            condition_values={},
            counts=Counter(),
            total_cost=0.0,
            node_max_iterations=node_max_iterations or {}
        )
    
    def update_cost(self, cost: float) -> None:
        """Add to total execution cost."""
        self.total_cost += cost
        
    def get_node_count(self, node_id: str) -> int:
        """Get execution count for a specific node."""
        return self.counts.get(node_id, 0)
        
    def increment_node_count(self, node_id: str) -> int:
        """Increment and return execution count for a node."""
        self.counts[node_id] += 1
        return self.counts[node_id]
        
    def is_max_iterations_exceeded(self, node_id: str) -> bool:
        """Check if node has exceeded max iterations."""
        if node_id not in self.node_max_iterations:
            return False
        return self.get_node_count(node_id) >= self.node_max_iterations[node_id]