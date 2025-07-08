"""Execution state machine logic."""

from typing import List, Dict, Any, Optional, Set
from enum import Enum
import logging

from dipeo.models import DomainDiagram, NodeType, DomainNode

log = logging.getLogger(__name__)


class ExecutionState(Enum):
    """States for execution flow."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStateMachine:
    """Manages execution state transitions and flow control."""
    
    def __init__(self):
        self.state = ExecutionState.IDLE
        self.executed_nodes: Set[str] = set()
        self.node_outputs: Dict[str, Any] = {}
        self.node_exec_counts: Dict[str, int] = {}
        self.error: Optional[str] = None
    
    def start_execution(self) -> bool:
        """Transition to running state."""
        if self.state not in [ExecutionState.IDLE, ExecutionState.PAUSED]:
            return False
        
        self.state = ExecutionState.RUNNING
        self.error = None
        return True
    
    def pause_execution(self) -> bool:
        """Transition to paused state."""
        if self.state != ExecutionState.RUNNING:
            return False
        
        self.state = ExecutionState.PAUSED
        return True
    
    def complete_execution(self) -> bool:
        """Transition to completed state."""
        if self.state not in [ExecutionState.RUNNING, ExecutionState.PAUSED]:
            return False
        
        self.state = ExecutionState.COMPLETED
        return True
    
    def fail_execution(self, error: str) -> bool:
        """Transition to failed state."""
        if self.state not in [ExecutionState.RUNNING, ExecutionState.PAUSED]:
            return False
        
        self.state = ExecutionState.FAILED
        self.error = error
        return True
    
    def cancel_execution(self) -> bool:
        """Transition to cancelled state."""
        if self.state not in [ExecutionState.RUNNING, ExecutionState.PAUSED]:
            return False
        
        self.state = ExecutionState.CANCELLED
        return True
    
    def record_node_execution(self, node_id: str, output: Any) -> None:
        """Record that a node has been executed."""
        self.executed_nodes.add(node_id)
        self.node_outputs[node_id] = output
        self.node_exec_counts[node_id] = self.node_exec_counts.get(node_id, 0) + 1
    
    def get_node_execution_count(self, node_id: str) -> int:
        """Get the number of times a node has been executed."""
        return self.node_exec_counts.get(node_id, 0)
    
    def is_node_executed(self, node_id: str) -> bool:
        """Check if a node has been executed at least once."""
        return node_id in self.executed_nodes
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution state."""
        return {
            "state": self.state.value,
            "executed_nodes": list(self.executed_nodes),
            "total_executions": sum(self.node_exec_counts.values()),
            "node_exec_counts": self.node_exec_counts.copy(),
            "error": self.error
        }
    
    def reset(self) -> None:
        """Reset the state machine to initial state."""
        self.state = ExecutionState.IDLE
        self.executed_nodes.clear()
        self.node_outputs.clear()
        self.node_exec_counts.clear()
        self.error = None
    
    def can_execute_node(self, node: DomainNode) -> bool:
        """Check if a node can be executed based on state and limits."""
        if self.state != ExecutionState.RUNNING:
            return False
        
        exec_count = self.get_node_execution_count(node.id)
        
        # Check max iterations for person_job nodes
        if node.type == NodeType.person_job and node.data:
            max_iter = node.data.get("max_iteration", 1)
            if exec_count >= max_iter:
                return False
        
        # Check max iterations for person_batch_job nodes
        if node.type == NodeType.person_batch_job and node.data:
            max_iter = node.data.get("max_iteration", 1)
            if exec_count >= max_iter:
                return False
        
        return True
    
    def should_continue_execution(self, diagram: DomainDiagram) -> bool:
        """Determine if execution should continue."""
        if self.state != ExecutionState.RUNNING:
            return False
        
        # Check if all endpoints have been executed
        endpoint_nodes = [
            node for node in diagram.nodes 
            if node.type == NodeType.endpoint
        ]
        
        if endpoint_nodes:
            all_endpoints_executed = all(
                self.is_node_executed(endpoint.id)
                for endpoint in endpoint_nodes
            )
            if all_endpoints_executed:
                return False
        
        # Check if any nodes can still execute
        can_execute_any = any(
            self.can_execute_node(node)
            for node in diagram.nodes
            if not self.is_node_executed(node.id) or self.can_execute_node(node)
        )
        
        return can_execute_any