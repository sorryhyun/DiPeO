"""State transition management extracted from ExecutionRuntime."""

import threading
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.core.execution.execution_tracker import CompletionStatus
from dipeo.core.execution.node_output import BaseNodeOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import NodeExecutionStatus, NodeID, NodeState

if TYPE_CHECKING:
    from dipeo.core.execution.execution_tracker import ExecutionTracker
    from dipeo.core.static.executable_diagram import ExecutableDiagram
    from dipeo.core.static.generated_nodes import (
        ConditionNode,
        EndpointNode,
        PersonJobNode,
        StartNode,
    )


class StateTransitionManager:
    """Manages node state transitions with proper thread safety."""
    
    def __init__(
        self, 
        diagram: "ExecutableDiagram",
        tracker: "ExecutionTracker",
        state_lock: threading.Lock
    ):
        self.diagram = diagram
        self.tracker = tracker
        self.state_lock = state_lock
    
    def transition_to_running(
        self, 
        node_id: NodeID, 
        node_states: dict[NodeID, NodeState],
        current_node_id: list[Optional[NodeID]]  # Mutable reference
    ) -> int:
        """Transition a node to running state and return execution number."""
        with self.state_lock:
            # Start execution in tracker (increments count)
            execution_number = self.tracker.start_execution(node_id)
            
            # Update state
            state = node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.PENDING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.RUNNING
            state.started_at = datetime.now()
            node_states[node_id] = state
            
            # Set current node
            current_node_id[0] = node_id
            
            return execution_number
    
    def transition_to_completed(
        self,
        node_id: NodeID,
        node_states: dict[NodeID, NodeState],
        current_node_id: list[Optional[NodeID]],
        output: Any = None,
        token_usage: dict[str, int] = None
    ) -> None:
        """Transition a node to completed state."""
        with self.state_lock:
            # Prepare protocol output
            node_output_protocol = self._prepare_protocol_output(node_id, output)
            
            # Complete in tracker
            self.tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.SUCCESS,
                output=node_output_protocol,
                token_usage=token_usage
            )
            
            # Update state
            state = node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.RUNNING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.COMPLETED
            state.ended_at = datetime.now()
            state.error = None
            node_states[node_id] = state
            
            # Clear current node
            if current_node_id[0] == node_id:
                current_node_id[0] = None
            
            # Handle downstream resets for loops
            self._reset_downstream_nodes_if_needed(node_id, node_states)
    
    def transition_to_failed(
        self,
        node_id: NodeID,
        node_states: dict[NodeID, NodeState],
        current_node_id: list[Optional[NodeID]],
        error: str
    ) -> None:
        """Transition a node to failed state."""
        with self.state_lock:
            # Create error output
            error_output = ErrorOutput(
                value=error,
                node_id=node_id,
                error_type="ExecutionError"
            )
            
            # Complete in tracker with failure
            self.tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.FAILED,
                output=error_output,
                error=error
            )
            
            # Update state
            state = node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.RUNNING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.FAILED
            state.ended_at = datetime.now()
            state.error = error
            node_states[node_id] = state
            
            # Clear current node
            if current_node_id[0] == node_id:
                current_node_id[0] = None
    
    def transition_to_maxiter(
        self,
        node_id: NodeID,
        node_states: dict[NodeID, NodeState],
        output: Optional[NodeOutputProtocol] = None
    ) -> None:
        """Transition a node to max iterations reached state."""
        with self.state_lock:
            # Use provided output or create default max iter output
            if output is None:
                output = BaseNodeOutput(
                    value="Maximum iterations reached",
                    node_id=node_id,
                    metadata={"reason": "max_iterations"}
                )
            
            # Complete in tracker
            self.tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.MAX_ITER,
                output=output
            )
            
            # Update state
            state = node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.PENDING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.MAXITER_REACHED
            state.ended_at = datetime.now()
            node_states[node_id] = state
    
    def transition_to_skipped(
        self,
        node_id: NodeID,
        node_states: dict[NodeID, NodeState]
    ) -> None:
        """Transition a node to skipped state."""
        with self.state_lock:
            # Create skipped output
            skipped_output = BaseNodeOutput(
                value="Node skipped",
                node_id=node_id,
                metadata={"reason": "branch_not_taken"}
            )
            
            # Complete in tracker
            self.tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.SKIPPED,
                output=skipped_output
            )
            
            # Update state
            state = node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.PENDING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.SKIPPED
            state.ended_at = datetime.now()
            node_states[node_id] = state
    
    def reset_node(
        self,
        node_id: NodeID,
        node_states: dict[NodeID, NodeState]
    ) -> None:
        """Reset a node to pending state for iteration."""
        with self.state_lock:
            # Reset in tracker (preserves execution history)
            self.tracker.reset_for_iteration(node_id)
            
            # Update state
            state = node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.COMPLETED,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.PENDING
            state.started_at = None
            state.ended_at = None
            state.error = None
            node_states[node_id] = state
    
    def _prepare_protocol_output(self, node_id: NodeID, output: Any) -> Any:
        """Convert output to protocol format if needed."""
        if output is None:
            return None
        
        # Already protocol-compliant?
        if hasattr(output, 'value') and hasattr(output, 'metadata'):
            return output
        
        # Wrap raw value (shouldn't happen with proper handlers)
        return BaseNodeOutput(
            value=output,
            node_id=node_id,
            metadata={}
        )
    
    def _reset_downstream_nodes_if_needed(
        self,
        node_id: NodeID,
        node_states: dict[NodeID, NodeState]
    ) -> None:
        """Reset downstream nodes if they're part of a loop."""
        from dipeo.core.static.generated_nodes import (
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
            target_state = node_states.get(target_node.id)
            if not target_state or target_state.status != NodeExecutionStatus.COMPLETED:
                continue
            
            # Check if we can reset this node
            can_reset = True
            
            # Don't reset one-time nodes
            if isinstance(target_node, (StartNode, EndpointNode)):
                can_reset = False
            
            # For condition nodes, allow reset if they're part of a loop
            # (they need to re-evaluate when loop conditions change)
            if isinstance(target_node, ConditionNode):
                # Check if this condition node has outgoing edges that loop back
                # If it does, it's part of a loop and should be reset
                cond_outgoing = [e for e in self.diagram.edges if e.source_node_id == target_node.id]
                can_reset = False
            
            # For PersonJobNodes, check max_iteration
            if isinstance(target_node, PersonJobNode):
                exec_count = self.tracker.get_execution_count(target_node.id)
                if exec_count > target_node.max_iteration:
                    can_reset = False
            
            if can_reset:
                nodes_to_reset.append(target_node.id)
        
        # Reset nodes and cascade
        for node_id_to_reset in nodes_to_reset:
            self.reset_node(node_id_to_reset, node_states)
            self._reset_downstream_nodes_if_needed(node_id_to_reset, node_states)