"""Execution tracking system that separates runtime state from execution history.

This module provides a robust tracking system that:
- Maintains immutable execution history for reliable condition checking
- Manages mutable runtime state for flow control
- Supports iteration without losing execution records
- Provides clear semantics for execution counting
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated.enums import CompletionStatus, FlowStatus

if TYPE_CHECKING:
    from dipeo.diagram_generated import NodeID
    from dipeo.domain.execution.envelope import Envelope


@dataclass
class NodeExecutionRecord:
    node_id: NodeID
    execution_number: int  # 1-based counting for clarity
    started_at: datetime
    ended_at: datetime | None
    status: CompletionStatus
    output: Envelope | None
    error: str | None
    token_usage: dict[str, int] | None = None
    duration: float = 0.0  # seconds

    def is_complete(self) -> bool:
        return self.ended_at is not None

    def was_successful(self) -> bool:
        return self.status == CompletionStatus.SUCCESS


@dataclass
class NodeRuntimeState:
    node_id: NodeID
    flow_status: FlowStatus
    is_active: bool = True
    dependencies_met: bool = False
    last_check: datetime = field(default_factory=datetime.now)

    def can_execute(self) -> bool:
        return self.flow_status == FlowStatus.READY and self.is_active and self.dependencies_met


class ExecutionTracker:
    def __init__(self):
        self._execution_records: dict[NodeID, list[NodeExecutionRecord]] = {}
        self._runtime_states: dict[NodeID, NodeRuntimeState] = {}
        self._execution_counts: dict[NodeID, int] = {}
        self._last_outputs: dict[NodeID, Envelope] = {}
        self._execution_order: list[NodeID] = []

    def start_execution(self, node_id: NodeID) -> int:
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

        self._update_runtime_state(node_id, FlowStatus.RUNNING)
        self._execution_order.append(node_id)

        return new_count

    def complete_execution(
        self,
        node_id: NodeID,
        status: CompletionStatus,
        output: Envelope | None = None,
        error: str | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> None:
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
        if status == CompletionStatus.SUCCESS:
            self._update_runtime_state(node_id, FlowStatus.WAITING)  # Ready for next iteration
        elif status == CompletionStatus.FAILED:
            self._update_runtime_state(node_id, FlowStatus.BLOCKED)
        else:
            self._update_runtime_state(node_id, FlowStatus.WAITING)

    def get_execution_count(self, node_id: NodeID) -> int:
        return self._execution_counts.get(node_id, 0)

    def has_executed(self, node_id: NodeID) -> bool:
        records = self._execution_records.get(node_id, [])
        return len(records) > 0

    def get_last_output(self, node_id: NodeID) -> Envelope | None:
        return self._last_outputs.get(node_id)

    def get_runtime_state(self, node_id: NodeID) -> NodeRuntimeState:
        if node_id not in self._runtime_states:
            self._runtime_states[node_id] = NodeRuntimeState(
                node_id=node_id, flow_status=FlowStatus.WAITING
            )
        return self._runtime_states[node_id]

    def update_runtime_state(self, node_id: NodeID, status: FlowStatus) -> None:
        self._update_runtime_state(node_id, status)

    def reset_for_iteration(self, node_id: NodeID) -> None:
        runtime_state = self.get_runtime_state(node_id)
        runtime_state.flow_status = FlowStatus.READY
        runtime_state.dependencies_met = True
        runtime_state.is_active = True
        runtime_state.last_check = datetime.now()

    def _update_runtime_state(self, node_id: NodeID, status: FlowStatus) -> None:
        runtime_state = self.get_runtime_state(node_id)
        runtime_state.flow_status = status
        runtime_state.last_check = datetime.now()

    def get_execution_summary(self) -> dict[str, Any]:
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
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "total_duration": total_duration,
            "total_tokens": total_tokens,
            "nodes_executed": len(self._execution_counts),
            "execution_order": self._execution_order.copy(),
        }

    def get_node_execution_history(self, node_id: NodeID) -> list[NodeExecutionRecord]:
        return self._execution_records.get(node_id, []).copy()

    def clear_history(self) -> None:
        self._execution_records.clear()
        self._runtime_states.clear()
        self._execution_counts.clear()
        self._last_outputs.clear()
        self._execution_order.clear()
