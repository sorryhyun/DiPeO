"""State snapshot and query helpers for execution state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from dipeo.diagram_generated import NodeState, Status
from dipeo.diagram_generated.domain_models import ExecutionID, NodeID


@dataclass
class StateSnapshot:
    """Immutable snapshot of execution state at a point in time.

    Represents the complete state of an execution at a specific version,
    including all node states and execution metadata.
    """

    execution_id: ExecutionID
    status: Status
    node_states: dict[NodeID, NodeState]
    start_time: datetime
    end_time: datetime | None
    error: str | None
    metadata: dict[str, Any]
    version: int

    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get state for a specific node.

        Args:
            node_id: ID of the node to query

        Returns:
            NodeState if found, None otherwise
        """
        return self.node_states.get(node_id)

    def get_nodes_by_status(self, status: Status) -> list[NodeID]:
        """Get all nodes with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of node IDs matching the status
        """
        return [node_id for node_id, state in self.node_states.items() if state.status == status]

    def get_all_node_ids(self) -> list[NodeID]:
        """Get all node IDs in this snapshot."""
        return list(self.node_states.keys())

    def get_completed_count(self) -> int:
        """Get count of completed nodes."""
        return sum(
            1
            for state in self.node_states.values()
            if state.status in [Status.COMPLETED, Status.MAXITER_REACHED]
        )

    def get_failed_count(self) -> int:
        """Get count of failed nodes."""
        return sum(1 for state in self.node_states.values() if state.status == Status.FAILED)

    def get_running_count(self) -> int:
        """Get count of running nodes."""
        return sum(1 for state in self.node_states.values() if state.status == Status.RUNNING)

    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return self.status in [Status.COMPLETED, Status.FAILED]
