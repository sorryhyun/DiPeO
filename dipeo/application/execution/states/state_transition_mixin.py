"""State transition mixin for execution contexts."""

import threading
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from dipeo.core.execution.execution_tracker import CompletionStatus
from dipeo.core.execution.node_output import BaseNodeOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated import NodeExecutionStatus, NodeID, NodeState

if TYPE_CHECKING:
    from dipeo.core.execution.execution_tracker import ExecutionTracker
    from dipeo.core.execution.executable_diagram import ExecutableDiagram


class TransitionType(Enum):
    """Types of node transitions."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MAXITER = "maxiter"
    SKIPPED = "skipped"
    RESET = "reset"


class StateTransitionMixin:
    """Mixin providing state transition functionality for execution contexts."""
    
    # These attributes must be provided by the class using this mixin
    diagram: "ExecutableDiagram"
    _tracker: "ExecutionTracker"
    _state_lock: threading.Lock
    _node_states: dict[NodeID, NodeState]
    _current_node_id: list[Optional[NodeID]]
    
    def transition_node_to_running(self, node_id: NodeID) -> int:
        """Transition a node to running state."""
        with self._state_lock:
            # Start execution in tracker (increments count)
            execution_number = self._tracker.start_execution(node_id)
            
            # Update state
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.PENDING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.RUNNING
            state.started_at = datetime.now()
            self._node_states[node_id] = state
            
            # Set current node
            self._current_node_id[0] = node_id
            
            return execution_number
    
    def transition_node_to_completed(
        self, 
        node_id: NodeID, 
        output: Any = None,
        token_usage: Optional[dict[str, int]] = None
    ) -> None:
        """Transition a node to completed state."""
        self._transition_to_final_state(
            node_id=node_id,
            status=NodeExecutionStatus.COMPLETED,
            completion_status=CompletionStatus.SUCCESS,
            output=output,
            token_usage=token_usage,
            error=None,
            reset_downstream=True
        )
    
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state."""
        # Create error output
        error_output = ErrorOutput(
            value=error,
            node_id=node_id,
            error_type="ExecutionError"
        )
        
        self._transition_to_final_state(
            node_id=node_id,
            status=NodeExecutionStatus.FAILED,
            completion_status=CompletionStatus.FAILED,
            output=error_output,
            error=error,
            reset_downstream=False
        )
    
    def transition_node_to_maxiter(
        self, 
        node_id: NodeID, 
        output: Optional[NodeOutputProtocol] = None
    ) -> None:
        """Transition a node to max iterations reached state."""
        # Use provided output or create default
        if output is None:
            output = BaseNodeOutput(
                value="Maximum iterations reached",
                node_id=node_id,
                metadata={"reason": "max_iterations"}
            )
        
        self._transition_to_final_state(
            node_id=node_id,
            status=NodeExecutionStatus.MAXITER_REACHED,
            completion_status=CompletionStatus.MAX_ITER,
            output=output,
            reset_downstream=False
        )
    
    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state."""
        # Create skipped output
        skipped_output = BaseNodeOutput(
            value="Node skipped",
            node_id=node_id,
            metadata={"reason": "branch_not_taken"}
        )
        
        self._transition_to_final_state(
            node_id=node_id,
            status=NodeExecutionStatus.SKIPPED,
            completion_status=CompletionStatus.SKIPPED,
            output=skipped_output,
            reset_downstream=False
        )
    
    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to pending state for iteration."""
        with self._state_lock:
            # Reset in tracker (preserves execution history)
            self._tracker.reset_for_iteration(node_id)
            
            # Update state
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.COMPLETED,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.PENDING
            state.started_at = None
            state.ended_at = None
            state.error = None
            self._node_states[node_id] = state
    
    def _transition_to_final_state(
        self,
        node_id: NodeID,
        status: NodeExecutionStatus,
        completion_status: CompletionStatus,
        output: Any = None,
        token_usage: Optional[dict[str, int]] = None,
        error: Optional[str] = None,
        reset_downstream: bool = False
    ) -> None:
        """Consolidated method for transitioning to any final state."""
        with self._state_lock:
            # Prepare protocol output
            node_output_protocol = self._prepare_protocol_output(node_id, output)
            
            # Complete in tracker
            self._tracker.complete_execution(
                node_id=node_id,
                status=completion_status,
                output=node_output_protocol,
                token_usage=token_usage,
                error=error
            )
            
            # Update state
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.RUNNING,
                node_id=node_id
            )
            state.status = status
            state.ended_at = datetime.now()
            state.error = error
            self._node_states[node_id] = state
            
            # Clear current node if it matches
            if self._current_node_id[0] == node_id:
                self._current_node_id[0] = None
            
            # Handle downstream resets for loops (only for successful completion)
            if reset_downstream:
                self._reset_downstream_nodes_if_needed(node_id)
    
    def _prepare_protocol_output(self, node_id: NodeID, output: Any) -> Any:
        """Convert output to protocol format if needed."""
        if output is None:
            return None
        
        # Already protocol-compliant?
        if hasattr(output, 'value') and hasattr(output, 'metadata'):
            return output
        
        # Wrap raw value
        return BaseNodeOutput(
            value=output,
            node_id=node_id,
            metadata={}
        )
    
    def _reset_downstream_nodes_if_needed(self, node_id: NodeID) -> None:
        """Reset downstream nodes if they're part of a loop."""
        from dipeo.diagram_generated.generated_nodes import (
            ConditionNode,
            EndpointNode,
            PersonJobNode,
            StartNode,
        )
        
        outgoing_edges = [e for e in self.diagram.edges if e.source_node_id == node_id]
        nodes_to_reset = []
        
        for edge in outgoing_edges:
            target_node = self.diagram.get_node(edge.target_node_id)
            if not target_node:
                continue
            
            # Check if target was already executed
            target_state = self._node_states.get(target_node.id)
            if not target_state or target_state.status != NodeExecutionStatus.COMPLETED:
                continue
            
            # Check if we can reset this node
            can_reset = True
            
            # Don't reset one-time nodes
            if isinstance(target_node, (StartNode, EndpointNode)):
                can_reset = False
            
            # For condition nodes, allow reset if they're part of a loop
            if isinstance(target_node, ConditionNode):
                cond_outgoing = [e for e in self.diagram.edges if e.source_node_id == target_node.id]
                can_reset = False
            
            # For PersonJobNodes, check max_iteration
            if isinstance(target_node, PersonJobNode):
                exec_count = self._tracker.get_execution_count(target_node.id)
                if exec_count > target_node.max_iteration:
                    can_reset = False
            
            if can_reset:
                nodes_to_reset.append(target_node.id)
        
        # Reset nodes and cascade
        for node_id_to_reset in nodes_to_reset:
            self.reset_node(node_id_to_reset)
            self._reset_downstream_nodes_if_needed(node_id_to_reset)