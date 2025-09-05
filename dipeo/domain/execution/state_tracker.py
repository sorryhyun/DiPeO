"""State tracking for execution context.

This module manages node states and execution history, primarily for
UI visualization and reporting. Actual execution is driven by tokens.
"""

import logging
import threading
from collections import defaultdict
from typing import Any

from dipeo.diagram_generated import NodeID, NodeState, Status
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.execution.execution_tracker import CompletionStatus, ExecutionTracker

logger = logging.getLogger(__name__)


class StateTracker:
    """Tracks node execution states and history.

    Responsibilities:
    - Node state transitions (for UI visualization)
    - Execution counting and history
    - Result storage and retrieval
    - Thread-safe state management

    Note: States are for UI only. Token flow drives actual execution.
    """

    def __init__(self):
        """Initialize state tracker."""
        # Node states (for UI)
        self._node_states: dict[NodeID, NodeState] = {}

        # Execution tracking
        self._tracker = ExecutionTracker()

        # Node iteration tracking per epoch
        self._node_iterations_per_epoch: dict[tuple[NodeID, int], int] = defaultdict(int)
        self._max_iterations_per_epoch: int = 100  # Default safety limit

        # Thread safety
        self._lock = threading.Lock()

        # Node metadata storage
        self._node_metadata: dict[NodeID, dict[str, Any]] = {}

    # ========== State Queries ==========

    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the current state of a node (for UI display)."""
        with self._lock:
            return self._node_states.get(node_id)

    def get_all_node_states(self) -> dict[NodeID, NodeState]:
        """Get all node states."""
        with self._lock:
            return dict(self._node_states)

    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node."""
        envelope = self._tracker.get_last_output(node_id)
        if envelope:
            result = {"value": envelope.body}
            if envelope.meta:
                result["metadata"] = envelope.meta
            return result
        return None

    def get_node_output(self, node_id: NodeID) -> Envelope | None:
        """Get the typed output of a completed node."""
        return self._tracker.get_last_output(node_id)

    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the number of times a node has been executed."""
        return self._tracker.get_execution_count(node_id)

    # ========== Node Lists by Status ==========

    def get_completed_nodes(self) -> list[NodeID]:
        """Get all nodes that have completed execution."""
        with self._lock:
            return [
                node_id
                for node_id, state in self._node_states.items()
                if state.status == Status.COMPLETED
            ]

    def get_running_nodes(self) -> list[NodeID]:
        """Get nodes currently in execution."""
        with self._lock:
            return [
                node_id
                for node_id, state in self._node_states.items()
                if state.status == Status.RUNNING
            ]

    def get_failed_nodes(self) -> list[NodeID]:
        """Get nodes that failed during execution."""
        with self._lock:
            return [
                node_id
                for node_id, state in self._node_states.items()
                if state.status == Status.FAILED
            ]

    def has_running_nodes(self) -> bool:
        """Check if any nodes are currently running."""
        with self._lock:
            return any(state.status == Status.RUNNING for state in self._node_states.values())

    # ========== State Transitions ==========

    def initialize_node(self, node_id: NodeID) -> None:
        """Initialize a node in PENDING state."""
        with self._lock:
            if node_id not in self._node_states:
                self._node_states[node_id] = NodeState(status=Status.PENDING)

    def transition_to_running(self, node_id: NodeID, epoch: int) -> int:
        """Transition a node to running state.

        Args:
            node_id: The node to transition
            epoch: The current epoch

        Returns:
            The execution count for this node
        """
        with self._lock:
            self._node_states[node_id] = NodeState(status=Status.RUNNING)
            self._tracker.start_execution(node_id)

            # Track iterations per epoch
            key = (node_id, epoch)
            self._node_iterations_per_epoch[key] += 1

            return self._tracker.get_execution_count(node_id)

    def transition_to_completed(
        self,
        node_id: NodeID,
        output: Envelope | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> None:
        """Transition a node to completed state with output."""
        with self._lock:
            self._node_states[node_id] = NodeState(status=Status.COMPLETED)
            self._tracker.complete_execution(
                node_id, CompletionStatus.SUCCESS, output=output, token_usage=token_usage
            )

    def transition_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state with error message."""
        with self._lock:
            self._node_states[node_id] = NodeState(status=Status.FAILED, error=error)
            self._tracker.complete_execution(node_id, CompletionStatus.FAILED, error=error)

    def transition_to_maxiter(self, node_id: NodeID, output: Envelope | None = None) -> None:
        """Transition a node to max iterations state."""
        logger.debug(f"[MAXITER] Transitioning {node_id} to MAXITER_REACHED")
        with self._lock:
            self._node_states[node_id] = NodeState(status=Status.MAXITER_REACHED)
            self._tracker.complete_execution(node_id, CompletionStatus.MAX_ITER, output=output)

    def transition_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state."""
        with self._lock:
            self._node_states[node_id] = NodeState(status=Status.SKIPPED)
            self._tracker.complete_execution(node_id, CompletionStatus.SKIPPED)

    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to initial state.

        Note: Execution count is NOT reset - it tracks cumulative executions.
        """
        with self._lock:
            self._node_states[node_id] = NodeState(status=Status.PENDING)
            logger.debug(
                f"Reset node {node_id} to PENDING, "
                f"execution_count remains {self._tracker.get_execution_count(node_id)}"
            )

    # ========== Iteration Control ==========

    def can_execute_in_loop(
        self, node_id: NodeID, epoch: int, max_iteration: int | None = None
    ) -> bool:
        """Check if a node can execute within iteration limits.

        Args:
            node_id: The node to check
            epoch: The current epoch
            max_iteration: Node-specific max iterations (e.g., PersonJobNode)

        Returns:
            True if the node hasn't exceeded max iterations for this epoch
        """
        key = (node_id, epoch)
        current_count = self._node_iterations_per_epoch[key]

        # Use node-specific max if provided
        if max_iteration is not None:
            return current_count < max_iteration

        # Otherwise use global max
        return current_count < self._max_iterations_per_epoch

    def get_iterations_in_epoch(self, node_id: NodeID, epoch: int) -> int:
        """Get the number of iterations for a node in a specific epoch."""
        return self._node_iterations_per_epoch.get((node_id, epoch), 0)

    # ========== Node Metadata ==========

    def get_node_metadata(self, node_id: NodeID) -> dict[str, Any]:
        """Get metadata for a specific node."""
        return self._node_metadata.get(node_id, {}).copy()

    def set_node_metadata(self, node_id: NodeID, key: str, value: Any) -> None:
        """Set metadata for a specific node."""
        if node_id not in self._node_metadata:
            self._node_metadata[node_id] = {}
        self._node_metadata[node_id][key] = value

    # ========== Persistence Support ==========

    def get_tracker(self) -> ExecutionTracker:
        """Get the execution tracker (for persistence)."""
        return self._tracker

    def load_states(self, node_states: dict[NodeID, NodeState], tracker: ExecutionTracker) -> None:
        """Load persisted states.

        Args:
            node_states: Persisted node states
            tracker: Persisted execution tracker
        """
        with self._lock:
            self._node_states = node_states.copy()
            self._tracker = tracker
