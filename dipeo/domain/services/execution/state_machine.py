"""Domain state machine for execution state transitions.

This module provides a domain service that encapsulates all state transitions
and modifications, ensuring proper validation and consistency.
"""

from datetime import datetime
from typing import Optional

from dipeo.models import (
    ExecutionState,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeOutput,
    NodeState,
)


class ExecutionStateMachine:
    """Domain service for managing execution state transitions."""
    
    @staticmethod
    def transition_to_running(state: ExecutionState) -> None:
        """Transition execution to running status."""
        if state.status != ExecutionStatus.PENDING:
            raise ValueError(f"Cannot transition to RUNNING from {state.status}")
        state.status = ExecutionStatus.RUNNING
        state.started_at = datetime.utcnow().isoformat()
        state.is_active = True
    
    @staticmethod
    def transition_to_completed(state: ExecutionState) -> None:
        """Transition execution to completed status."""
        if state.status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot transition to COMPLETED from {state.status}")
        state.status = ExecutionStatus.COMPLETED
        state.ended_at = datetime.utcnow().isoformat()
        state.is_active = False
    
    @staticmethod
    def transition_to_failed(state: ExecutionState, error: str) -> None:
        """Transition execution to failed status."""
        if state.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            raise ValueError(f"Cannot transition to FAILED from {state.status}")
        state.status = ExecutionStatus.FAILED
        state.ended_at = datetime.utcnow().isoformat()
        state.is_active = False
        state.error = error
    
    @staticmethod
    def initialize_node_state(
        execution_state: ExecutionState,
        node_id: str,
        node_type: str,
        max_iterations: int = 1
    ) -> NodeState:
        """Initialize a new node state."""
        node_state = NodeState(
            status=NodeExecutionStatus.PENDING,
            started_at=datetime.utcnow().isoformat(),
            metadata={
                "exec_count": 0,
                "max_iterations": max_iterations,
                "node_type": node_type
            }
        )
        execution_state.node_states[node_id] = node_state
        return node_state
    
    @staticmethod
    def execute_node(
        execution_state: ExecutionState,
        node_id: str,
        output: Optional[NodeOutput] = None
    ) -> None:
        """Mark a node as executed and update its state."""
        node_state = execution_state.node_states.get(node_id)
        if not node_state:
            raise ValueError(f"Node {node_id} not found in execution state")
        
        if not node_state.metadata:
            raise ValueError(f"Node {node_id} has no metadata")
        
        # Increment execution count
        exec_count = node_state.metadata.get("exec_count", 0)
        node_state.metadata["exec_count"] = exec_count + 1
        
        # Update status based on iterations
        max_iterations = node_state.metadata.get("max_iterations", 1)
        if node_state.metadata["exec_count"] >= max_iterations:
            node_state.status = NodeExecutionStatus.COMPLETED
            node_state.ended_at = datetime.utcnow().isoformat()
        else:
            node_state.status = NodeExecutionStatus.RUNNING
        
        # Update output
        if output:
            execution_state.node_outputs[node_id] = output
            node_state.output = output
    
    @staticmethod
    def can_node_execute(execution_state: ExecutionState, node_id: str) -> bool:
        """Check if a node can execute."""
        node_state = execution_state.node_states.get(node_id)
        if not node_state:
            return True  # New nodes can execute
        
        # Check if completed or failed
        if node_state.status in [NodeExecutionStatus.COMPLETED, NodeExecutionStatus.FAILED]:
            return False
        
        # Check iteration count
        if node_state.metadata:
            exec_count = node_state.metadata.get("exec_count", 0)
            max_iterations = node_state.metadata.get("max_iterations", 1)
            return exec_count < max_iterations
        
        return True
    
    @staticmethod
    def get_node_exec_count(execution_state: ExecutionState, node_id: str) -> int:
        """Get execution count for a node."""
        node_state = execution_state.node_states.get(node_id)
        if not node_state or not node_state.metadata:
            return 0
        return node_state.metadata.get("exec_count", 0)
    
    @staticmethod
    def get_executed_nodes(execution_state: ExecutionState) -> set[str]:
        """Get set of executed node IDs."""
        executed = set()
        for node_id, node_state in execution_state.node_states.items():
            if node_state.metadata and node_state.metadata.get("exec_count", 0) > 0:
                executed.add(node_id)
        return executed
    
    @staticmethod
    def is_endpoint_executed(execution_state: ExecutionState) -> bool:
        """Check if any endpoint node has been executed."""
        for node_id, node_state in execution_state.node_states.items():
            if node_state.metadata and node_state.metadata.get("node_type") == "endpoint":
                if node_state.metadata.get("exec_count", 0) > 0:
                    return True
        return False