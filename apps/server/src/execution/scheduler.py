"""Execution scheduling and dependency management."""

import structlog
from typing import Dict, List, Tuple, Optional, Set

from .state import ExecutionState
from ..utils.dynamic_executor import DynamicExecutor

logger = structlog.get_logger(__name__)


class ExecutionScheduler:
    """Manages the execution queue and scheduling logic.
    
    Handles node dependency checking, requeuing logic for unmet dependencies,
    and determines execution order based on the diagram structure.
    """
    
    MAX_REQUEUE_ATTEMPTS = 100
    
    def __init__(self, dynamic_executor: DynamicExecutor, state: ExecutionState):
        self.dynamic_executor = dynamic_executor
        self.state = state
        self.requeue_count: Dict[str, int] = {}
        
    def should_skip_node(self, node_id: str) -> Tuple[bool, Optional[str]]:
        """Check if node should be skipped due to max iterations.
        
        Args:
            node_id: ID of node to check
            
        Returns:
            Tuple of (should_skip, skip_reason)
        """
        if node_id not in self.state.node_max_iterations:
            return False, None
            
        max_iter = self.state.node_max_iterations[node_id]
        if self.state.counts[node_id] >= max_iter:
            logger.debug(
                "node_max_iterations_exceeded",
                node_id=node_id,
                max_iterations=max_iter,
                current_count=self.state.counts[node_id]
            )
            return True, "max_iterations_exceeded"
            
        return False, None
    
    def check_dependencies(self, node_id: str) -> Tuple[bool, List[dict]]:
        """Check if node dependencies are met.
        
        Args:
            node_id: ID of node to check
            
        Returns:
            Tuple of (dependencies_met, valid_incoming_arrows)
        """
        available_vars = set(self.state.context.keys())
        deps_met, valid_incoming = self.dynamic_executor.check_dependencies_met(
            node_id,
            available_vars,
            self.state.condition_values,
            self.state.context
        )
        return deps_met, valid_incoming
    
    def handle_requeue(self, node_id: str) -> bool:
        """Handle requeuing of nodes with unmet dependencies.
        
        Args:
            node_id: ID of node to requeue
            
        Returns:
            True if requeue is allowed, False if max attempts exceeded
        """
        self.requeue_count[node_id] = self.requeue_count.get(node_id, 0) + 1
        
        logger.debug(
            "node_requeued",
            node_id=node_id,
            attempt=self.requeue_count[node_id]
        )
        
        if self.requeue_count[node_id] > self.MAX_REQUEUE_ATTEMPTS:
            logger.error(
                "max_requeue_attempts_exceeded",
                node_id=node_id,
                attempts=self.requeue_count[node_id]
            )
            return False
            
        return True
    
    def get_next_nodes(self, node_id: str) -> List[str]:
        """Get the next nodes to execute after current node.
        
        Args:
            node_id: ID of completed node
            
        Returns:
            List of node IDs that should execute next
        """
        return self.dynamic_executor.get_next_nodes(
            node_id, 
            self.state.condition_values
        )
        
    def reset_requeue_count(self, node_id: str) -> None:
        """Reset requeue count for a node after successful execution."""
        if node_id in self.requeue_count:
            del self.requeue_count[node_id]
            
    def get_requeue_stats(self) -> Dict[str, int]:
        """Get current requeue statistics for monitoring."""
        return self.requeue_count.copy()