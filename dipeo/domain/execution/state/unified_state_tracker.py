"""Unified state tracking system combining UI state, execution history, and iteration limits.

This module consolidates the responsibilities of ExecutionTracker and StateTracker
into a single source of truth, eliminating redundancy and preventing state divergence.

Key Features:
- Single source of truth for all execution state
- Thread-safe operations
- Clear internal separation of concerns
- Comprehensive execution history
- Iteration limit enforcement
- Node metadata management
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import CompletionStatus, Status

if TYPE_CHECKING:
    from dipeo.diagram_generated import NodeID
    from dipeo.domain.execution.messaging.envelope import Envelope

logger = get_module_logger(__name__)


@dataclass
class NodeExecutionRecord:
    """Immutable record of a single node execution."""

    node_id: NodeID
    execution_number: int
    started_at: datetime
    ended_at: datetime | None
    status: CompletionStatus
    output: Envelope | None
    error: str | None
    token_usage: dict[str, int] | None = None
    duration: float = 0.0

    def is_complete(self) -> bool:
        return self.ended_at is not None

    def was_successful(self) -> bool:
        return self.status == CompletionStatus.SUCCESS


@dataclass
class NodeState:
    """Current state of a node for UI visualization."""

    status: Status
    error: str | None = None


@dataclass
class NodeRuntimeState:
    """Backward compatibility: Runtime state (deprecated, not used by execution engine).

    This class exists only for backward compatibility. The execution engine
    uses token-based flow control, not runtime state. This data structure
    is maintained but not actively used in execution logic.
    """

    node_id: NodeID
    flow_status: str = "waiting"  # For compatibility
    is_active: bool = True
    dependencies_met: bool = False
    last_check: datetime = field(default_factory=datetime.now)

    def can_execute(self) -> bool:
        """Check if node can execute (always returns True for compatibility)."""
        return True


class UnifiedStateTracker:
    """Unified state tracking with single source of truth.

    Consolidates:
    - UI state tracking (PENDING, RUNNING, COMPLETED, etc.)
    - Execution history (immutable records)
    - Iteration limits (per-epoch tracking)
    - Node metadata
    - Thread safety

    This class replaces the previous ExecutionTracker and StateTracker
    to eliminate redundancy and prevent state divergence.
    """

    def __init__(self):
        # UI State (for visualization)
        self._node_states: dict[NodeID, NodeState] = {}

        # Execution History (immutable records)
        self._execution_records: dict[NodeID, list[NodeExecutionRecord]] = {}
        self._execution_counts: dict[NodeID, int] = {}
        self._last_outputs: dict[NodeID, Envelope] = {}
        self._execution_order: list[NodeID] = []

        # Iteration Limits (per-epoch tracking)
        self._node_iterations_per_epoch: dict[tuple[NodeID, int], int] = defaultdict(int)
        self._max_iterations_per_epoch: int = 100

        # Metadata (arbitrary key-value storage per node)
        self._node_metadata: dict[NodeID, dict[str, Any]] = {}

        # Thread Safety
        self._lock = threading.Lock()

    # ========================================================================
    # State Transition Methods
    # ========================================================================

    def initialize_node(self, node_id: NodeID) -> None:
        """Initialize a node to PENDING state.

        Args:
            node_id: The node to initialize
        """
        with self._lock:
            if node_id not in self._node_states:
                self._node_states[node_id] = NodeState(status=Status.PENDING)

    def transition_to_running(self, node_id: NodeID, epoch: int) -> int:
        """Transition a node to RUNNING state and start execution tracking.

        Args:
            node_id: The node to transition
            epoch: The current epoch

        Returns:
            The execution count for this node (1-indexed)
        """
        with self._lock:
            # Update UI state
            self._node_states[node_id] = NodeState(status=Status.RUNNING)

            # Start execution tracking
            current_count = self._execution_counts.get(node_id, 0)
            new_count = current_count + 1
            self._execution_counts[node_id] = new_count

            # Create execution record
            record = NodeExecutionRecord(
                node_id=node_id,
                execution_number=new_count,
                started_at=datetime.now(),
                ended_at=None,
                status=CompletionStatus.SUCCESS,
                output=None,
                error=None,
            )

            if node_id not in self._execution_records:
                self._execution_records[node_id] = []
            self._execution_records[node_id].append(record)

            # Track execution order
            self._execution_order.append(node_id)

            # Track iteration per epoch
            key = (node_id, epoch)
            self._node_iterations_per_epoch[key] += 1

            logger.debug(
                f"Node {node_id} transitioned to RUNNING "
                f"(execution #{new_count}, epoch {epoch})"
            )

            return new_count

    def transition_to_completed(
        self,
        node_id: NodeID,
        output: Envelope | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> None:
        """Transition a node to COMPLETED state.

        Args:
            node_id: The node to transition
            output: The node's output envelope
            token_usage: Token usage statistics
        """
        with self._lock:
            # Update UI state
            self._node_states[node_id] = NodeState(status=Status.COMPLETED)

            # Complete execution record
            self._complete_execution_record(
                node_id, CompletionStatus.SUCCESS, output=output, token_usage=token_usage
            )

            logger.debug(f"Node {node_id} transitioned to COMPLETED")

    def transition_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to FAILED state.

        Args:
            node_id: The node to transition
            error: Error message describing the failure
        """
        with self._lock:
            # Update UI state
            self._node_states[node_id] = NodeState(status=Status.FAILED, error=error)

            # Complete execution record
            self._complete_execution_record(node_id, CompletionStatus.FAILED, error=error)

            logger.debug(f"Node {node_id} transitioned to FAILED: {error}")

    def transition_to_maxiter(self, node_id: NodeID, output: Envelope | None = None) -> None:
        """Transition a node to MAXITER_REACHED state.

        Args:
            node_id: The node to transition
            output: The node's last output envelope
        """
        with self._lock:
            # Update UI state
            self._node_states[node_id] = NodeState(status=Status.MAXITER_REACHED)

            # Complete execution record
            self._complete_execution_record(node_id, CompletionStatus.MAX_ITER, output=output)

            logger.debug(f"Node {node_id} transitioned to MAXITER_REACHED")

    def transition_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to SKIPPED state (conditional branch not taken).

        Args:
            node_id: The node to transition
        """
        with self._lock:
            # Update UI state
            self._node_states[node_id] = NodeState(status=Status.SKIPPED)

            # Complete execution record
            self._complete_execution_record(node_id, CompletionStatus.SKIPPED)

            logger.debug(f"Node {node_id} transitioned to SKIPPED")

    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to PENDING state (for next iteration).

        Note: Execution count is NOT reset - it tracks cumulative executions.

        Args:
            node_id: The node to reset
        """
        with self._lock:
            self._node_states[node_id] = NodeState(status=Status.PENDING)
            logger.debug(
                f"Reset node {node_id} to PENDING, "
                f"execution_count remains {self._execution_counts.get(node_id, 0)}"
            )

    # ========================================================================
    # State Query Methods
    # ========================================================================

    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the current state of a node.

        Args:
            node_id: The node to query

        Returns:
            NodeState or None if node not initialized
        """
        with self._lock:
            return self._node_states.get(node_id)

    def get_all_node_states(self) -> dict[NodeID, NodeState]:
        """Get all node states.

        Returns:
            Dictionary mapping node IDs to their states
        """
        with self._lock:
            return dict(self._node_states)

    def get_completed_nodes(self) -> list[NodeID]:
        """Get all nodes in COMPLETED state.

        Returns:
            List of node IDs
        """
        with self._lock:
            return [
                node_id
                for node_id, state in self._node_states.items()
                if state.status == Status.COMPLETED
            ]

    def get_running_nodes(self) -> list[NodeID]:
        """Get all nodes in RUNNING state.

        Returns:
            List of node IDs
        """
        with self._lock:
            return [
                node_id
                for node_id, state in self._node_states.items()
                if state.status == Status.RUNNING
            ]

    def get_failed_nodes(self) -> list[NodeID]:
        """Get all nodes in FAILED state.

        Returns:
            List of node IDs
        """
        with self._lock:
            return [
                node_id
                for node_id, state in self._node_states.items()
                if state.status == Status.FAILED
            ]

    def has_running_nodes(self) -> bool:
        """Check if any nodes are currently running.

        Returns:
            True if at least one node is in RUNNING state
        """
        with self._lock:
            return any(state.status == Status.RUNNING for state in self._node_states.values())

    # ========================================================================
    # Execution History Methods
    # ========================================================================

    def get_execution_count(self, node_id: NodeID) -> int:
        """Get the number of times a node has executed.

        Args:
            node_id: The node to query

        Returns:
            Cumulative execution count (across all epochs)
        """
        with self._lock:
            return self._execution_counts.get(node_id, 0)

    def has_executed(self, node_id: NodeID) -> bool:
        """Check if a node has ever executed.

        Args:
            node_id: The node to query

        Returns:
            True if the node has executed at least once
        """
        with self._lock:
            records = self._execution_records.get(node_id, [])
            return len(records) > 0

    def get_last_output(self, node_id: NodeID) -> Envelope | None:
        """Get the last output envelope from a node.

        Args:
            node_id: The node to query

        Returns:
            The last output envelope or None
        """
        with self._lock:
            return self._last_outputs.get(node_id)

    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the last result from a node (envelope body + metadata).

        Args:
            node_id: The node to query

        Returns:
            Dictionary with 'value' and optional 'metadata' keys, or None
        """
        with self._lock:
            envelope = self._last_outputs.get(node_id)
            if envelope:
                result = {"value": envelope.body}
                if envelope.meta:
                    result["metadata"] = envelope.meta
                return result
            return None

    def get_node_execution_history(self, node_id: NodeID) -> list[NodeExecutionRecord]:
        """Get all execution records for a node.

        Args:
            node_id: The node to query

        Returns:
            List of execution records (ordered by execution number)
        """
        with self._lock:
            return self._execution_records.get(node_id, []).copy()

    def get_execution_summary(self) -> dict[str, Any]:
        """Get a summary of all executions.

        Returns:
            Dictionary with execution statistics:
            - total_executions: Total number of node executions
            - successful_executions: Number of successful executions
            - failed_executions: Number of failed executions
            - success_rate: Ratio of successful to total executions
            - total_duration: Total execution time in seconds
            - total_tokens: Total token usage (input, output, cached)
            - nodes_executed: Number of unique nodes executed
            - execution_order: List of node IDs in execution order
        """
        with self._lock:
            total_executions = sum(self._execution_counts.values())
            successful_executions = 0
            failed_executions = 0
            total_duration = 0.0
            total_tokens = {"input": 0, "output": 0, "cached": 0}

            for records in self._execution_records.values():
                for record in records:
                    if record.is_complete():
                        total_duration += record.duration
                        if record.was_successful():
                            successful_executions += 1
                        else:
                            failed_executions += 1

                        if record.token_usage:
                            total_tokens["input"] += record.token_usage.get("input", 0)
                            total_tokens["output"] += record.token_usage.get("output", 0)
                            total_tokens["cached"] += record.token_usage.get("cached", 0)

            return {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": (
                    successful_executions / total_executions if total_executions > 0 else 0
                ),
                "total_duration": total_duration,
                "total_tokens": total_tokens,
                "nodes_executed": len(self._execution_counts),
                "execution_order": self._execution_order.copy(),
            }

    def get_execution_order(self) -> list[NodeID]:
        """Get the order in which nodes were executed.

        Returns:
            List of node IDs in execution order (may contain duplicates)
        """
        with self._lock:
            return self._execution_order.copy()

    # ========================================================================
    # Iteration Limit Methods
    # ========================================================================

    def can_execute_in_loop(
        self, node_id: NodeID, epoch: int, max_iteration: int | None = None
    ) -> bool:
        """Check if a node can execute within iteration limits.

        Args:
            node_id: The node to check
            epoch: The current epoch
            max_iteration: Node-specific max iterations (overrides default)

        Returns:
            True if the node hasn't exceeded max iterations for this epoch
        """
        with self._lock:
            key = (node_id, epoch)
            current_count = self._node_iterations_per_epoch[key]

            if max_iteration is not None:
                return current_count < max_iteration

            return current_count < self._max_iterations_per_epoch

    def get_iterations_in_epoch(self, node_id: NodeID, epoch: int) -> int:
        """Get the number of iterations a node has executed in a specific epoch.

        Args:
            node_id: The node to query
            epoch: The epoch to query

        Returns:
            Number of iterations in the specified epoch
        """
        with self._lock:
            return self._node_iterations_per_epoch.get((node_id, epoch), 0)

    # ========================================================================
    # Metadata Methods
    # ========================================================================

    def get_node_metadata(self, node_id: NodeID) -> dict[str, Any]:
        """Get metadata for a node.

        Args:
            node_id: The node to query

        Returns:
            Copy of node metadata dictionary
        """
        with self._lock:
            return self._node_metadata.get(node_id, {}).copy()

    def set_node_metadata(self, node_id: NodeID, key: str, value: Any) -> None:
        """Set metadata for a node.

        Args:
            node_id: The node to update
            key: Metadata key
            value: Metadata value
        """
        with self._lock:
            if node_id not in self._node_metadata:
                self._node_metadata[node_id] = {}
            self._node_metadata[node_id][key] = value

    # ========================================================================
    # Persistence Methods
    # ========================================================================

    def load_states(
        self,
        node_states: dict[NodeID, NodeState],
        execution_records: dict[NodeID, list[NodeExecutionRecord]] | None = None,
        execution_counts: dict[NodeID, int] | None = None,
        last_outputs: dict[NodeID, Envelope] | None = None,
    ) -> None:
        """Load persisted states.

        Args:
            node_states: Persisted node states
            execution_records: Persisted execution records (optional)
            execution_counts: Persisted execution counts (optional)
            last_outputs: Persisted last outputs (optional)
        """
        with self._lock:
            self._node_states = node_states.copy()
            if execution_records is not None:
                self._execution_records = {k: list(v) for k, v in execution_records.items()}
            if execution_counts is not None:
                self._execution_counts = execution_counts.copy()
            if last_outputs is not None:
                self._last_outputs = last_outputs.copy()

            logger.debug(f"Loaded states for {len(node_states)} nodes")

    def clear_history(self) -> None:
        """Clear all execution history (for testing)."""
        with self._lock:
            self._execution_records.clear()
            self._node_states.clear()
            self._execution_counts.clear()
            self._last_outputs.clear()
            self._execution_order.clear()
            self._node_iterations_per_epoch.clear()
            self._node_metadata.clear()

            logger.debug("Cleared all execution history")

    # ========================================================================
    # Backward Compatibility Methods
    # ========================================================================

    def get_tracker(self) -> UnifiedStateTracker:
        """Get tracker reference (for backward compatibility).

        Returns:
            Self (maintains compatibility with old code expecting ExecutionTracker)
        """
        return self

    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Alias for get_execution_count (backward compatibility).

        Args:
            node_id: The node to query

        Returns:
            Cumulative execution count
        """
        return self.get_execution_count(node_id)

    def get_node_output(self, node_id: NodeID) -> Envelope | None:
        """Alias for get_last_output (backward compatibility).

        Args:
            node_id: The node to query

        Returns:
            The last output envelope or None
        """
        return self.get_last_output(node_id)

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _complete_execution_record(
        self,
        node_id: NodeID,
        status: CompletionStatus,
        output: Envelope | None = None,
        error: str | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> None:
        """Complete the current execution record (internal use only).

        Assumes lock is already held.

        Args:
            node_id: The node whose execution is completing
            status: Completion status
            output: Output envelope (optional)
            error: Error message (optional)
            token_usage: Token usage statistics (optional)

        Raises:
            ValueError: If no execution was started or already completed
        """
        records = self._execution_records.get(node_id, [])
        if not records:
            raise ValueError(f"No execution started for node {node_id}")

        current_record = records[-1]
        if current_record.ended_at is not None:
            raise ValueError(f"Node {node_id} execution already completed")

        end_time = datetime.now()
        current_record.ended_at = end_time
        current_record.status = status
        current_record.output = output
        current_record.error = error
        current_record.token_usage = token_usage
        current_record.duration = (end_time - current_record.started_at).total_seconds()

        if output:
            self._last_outputs[node_id] = output
