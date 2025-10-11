"""Execution state persistence logic extracted from ExecutionRuntime."""

from datetime import datetime
from typing import TYPE_CHECKING

from dipeo.diagram_generated import (
    ExecutionState,
    LLMUsage,
    NodeID,
    NodeState,
    Status,
)
from dipeo.domain.execution.messaging.envelope import deserialize_protocol, serialize_protocol
from dipeo.domain.execution.state.execution_tracker import CompletionStatus

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.domain.execution.state.execution_tracker import ExecutionTracker


class ExecutionStatePersistence:
    """Handles conversion between runtime state and persistent ExecutionState."""

    @staticmethod
    def load_from_state(
        state: ExecutionState, node_states: dict[NodeID, NodeState], tracker: "ExecutionTracker"
    ) -> None:
        """Load runtime state from persisted ExecutionState."""
        # Load node states
        if state.node_states:
            for node_id_str, node_state in state.node_states.items():
                node_states[NodeID(node_id_str)] = node_state

        # Load node outputs into tracker
        if state.node_outputs:
            for node_id_str, output_data in state.node_outputs.items():
                node_id = NodeID(node_id_str)
                protocol_output = deserialize_protocol(output_data)
                # Store in tracker (this is a hack - tracker should have proper API)
                tracker._last_outputs[node_id] = protocol_output

        # Load execution counts into tracker
        if state.exec_counts:
            for node_id_str, count in state.exec_counts.items():
                # Pre-populate tracker counts by simulating executions
                for _ in range(count):
                    tracker.start_execution(NodeID(node_id_str))
                    tracker.complete_execution(NodeID(node_id_str), CompletionStatus.SUCCESS)

    @staticmethod
    def save_to_state(
        execution_id: str,
        diagram_id: str,
        diagram: "ExecutableDiagram",
        node_states: dict[NodeID, NodeState],
        tracker: "ExecutionTracker",
    ) -> ExecutionState:
        """Convert runtime state to ExecutionState for persistence."""
        # Calculate aggregate LLM usage
        total_input = 0
        total_output = 0
        for state in node_states.values():
            if state.llm_usage:
                total_input += state.llm_usage.input
                total_output += state.llm_usage.output

        # Determine overall status
        has_failed = any(s.status == Status.FAILED for s in node_states.values())
        has_running = any(s.status == Status.RUNNING for s in node_states.values())

        if has_failed:
            status = Status.FAILED
        elif has_running:
            status = Status.RUNNING
        else:
            status = Status.COMPLETED

        # Serialize protocol outputs for storage
        serialized_outputs = {}
        all_nodes = diagram.get_nodes_by_type(None) or diagram.nodes
        for node in all_nodes:
            protocol_output = tracker.get_last_output(node.id)
            if protocol_output:
                serialized_outputs[str(node.id)] = serialize_protocol(protocol_output)

        # Get execution summary from tracker
        summary = tracker.get_execution_summary()

        return ExecutionState(
            id=execution_id,
            status=status,
            diagram_id=diagram_id,
            started_at=datetime.now().isoformat(),
            node_states={str(k): v for k, v in node_states.items()},
            node_outputs=serialized_outputs,
            llm_usage=LLMUsage(input=total_input, output=total_output),
            is_active=has_running,
            exec_counts={
                str(node_id): tracker.get_execution_count(node_id) for node_id in node_states
            },
            executed_nodes=[str(node_id) for node_id in summary["execution_order"]],
        )
