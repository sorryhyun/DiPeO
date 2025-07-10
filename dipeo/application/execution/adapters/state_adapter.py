"""Application-level execution state adapter.

This module provides an adapter that bridges between the domain ExecutionState
and application-specific state needs, preventing redundant state tracking.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

from dipeo.models import NodeOutput, NodeState, NodeExecutionStatus, ExecutionState
from dipeo.application.execution.state import UnifiedExecutionCoordinator

if TYPE_CHECKING:
    from dipeo.core.ports.state_store import StateStorePort


@dataclass
class ApplicationExecutionState:
    """Application-specific view of execution state.
    
    This adapter provides a unified interface for state management,
    translating between domain state and application needs while
    maintaining a single source of truth.
    """
    
    execution_state: ExecutionState
    coordinator: UnifiedExecutionCoordinator
    state_store: Optional["StateStorePort"] = None
    
    def get_node_exec_count(self, node_id: str) -> int:
        """Get execution count for a node."""
        return self.coordinator.get_node_exec_count(self.execution_state, node_id)
    
    def get_node_max_iterations(self, node_id: str) -> int:
        """Get max iterations for a node."""
        node_state = self.execution_state.node_states.get(node_id)
        if not node_state:
            return 1
        # Extract max iterations from node state metadata
        return node_state.metadata.get("max_iterations", 1) if node_state.metadata else 1
    
    def can_node_execute(self, node_id: str) -> bool:
        """Check if node can execute."""
        return self.coordinator.can_node_execute(self.execution_state, node_id)
    
    def get_node_output(self, node_id: str) -> Optional[NodeOutput]:
        """Get output for a node."""
        return self.execution_state.node_outputs.get(node_id)
    
    def get_all_node_outputs(self) -> Dict[str, NodeOutput]:
        """Get all node outputs."""
        return self.execution_state.node_outputs.copy()
    
    def get_all_node_exec_counts(self) -> Dict[str, int]:
        """Get execution counts for all nodes."""
        counts = {}
        for node_id, node_state in self.execution_state.node_states.items():
            counts[node_id] = self.get_node_exec_count(node_id)
        return counts
    
    async def update_node_state(
        self,
        node_id: str,
        node_type: str,
        output: Optional[NodeOutput] = None,
        max_iterations: int = 1,
        increment_exec_count: bool = False
    ) -> None:
        """Update node state in domain model."""
        # Initialize node state if it doesn't exist
        if node_id not in self.execution_state.node_states:
            self.coordinator.initialize_node_state(
                self.execution_state, node_id, node_type, max_iterations
            )
        
        # Execute node if requested
        if increment_exec_count:
            self.coordinator.execute_node_state(
                self.execution_state, node_id, output
            )
        elif output:
            # Just update output without executing
            self.execution_state.node_outputs[node_id] = output
            node_state = self.execution_state.node_states.get(node_id)
            if node_state:
                node_state.output = output
        
        # Persist if state store is available
        if self.state_store:
            await self.state_store.save_execution_state(self.execution_state)
    
    def get_executed_nodes(self) -> set[str]:
        """Get set of executed node IDs."""
        return self.coordinator.get_executed_nodes(self.execution_state)
    
    def is_endpoint_executed(self) -> bool:
        """Check if any endpoint node has been executed."""
        return self.coordinator.is_endpoint_executed(self.execution_state)