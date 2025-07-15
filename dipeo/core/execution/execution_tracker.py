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
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo.core.execution.node_output import NodeOutputProtocol
    from dipeo.models import NodeID


class FlowStatus(Enum):
    """Runtime flow status - independent of execution history."""
    WAITING = "waiting"      # Waiting for dependencies
    READY = "ready"          # Ready to execute
    RUNNING = "running"      # Currently executing
    BLOCKED = "blocked"      # Blocked by error or condition


class CompletionStatus(Enum):
    """Completion status for execution records."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    MAX_ITER = "max_iter"


@dataclass
class NodeExecutionRecord:
    """Immutable record of a single node execution."""
    node_id: NodeID
    execution_number: int  # 1-based counting for clarity
    started_at: datetime
    ended_at: datetime | None
    status: CompletionStatus
    output: NodeOutputProtocol | None
    error: str | None
    token_usage: dict[str, int] | None = None
    duration: float = 0.0  # seconds
    
    def is_complete(self) -> bool:
        """Check if this execution is complete."""
        return self.ended_at is not None
    
    def was_successful(self) -> bool:
        """Check if this execution was successful."""
        return self.status == CompletionStatus.SUCCESS


@dataclass
class NodeRuntimeState:
    """Mutable runtime state for execution flow."""
    node_id: NodeID
    flow_status: FlowStatus
    is_active: bool = True  # For loops - is this node in the active execution path?
    dependencies_met: bool = False
    last_check: datetime = field(default_factory=datetime.now)
    
    def can_execute(self) -> bool:
        """Check if node can execute now."""
        return (
            self.flow_status == FlowStatus.READY and
            self.is_active and
            self.dependencies_met
        )


class ExecutionTracker:
    """Separate tracking of execution history vs runtime state."""
    
    def __init__(self):
        # Execution history (immutable records)
        self._execution_records: dict[NodeID, list[NodeExecutionRecord]] = {}
        
        # Runtime state (mutable)
        self._runtime_states: dict[NodeID, NodeRuntimeState] = {}
        
        # Quick lookups
        self._execution_counts: dict[NodeID, int] = {}
        self._last_outputs: dict[NodeID, NodeOutputProtocol] = {}
        self._execution_order: list[NodeID] = []
    
    def start_execution(self, node_id: NodeID) -> int:
        """Start a new execution and return execution number (1-based)."""
        # Update count AFTER starting (not before)
        current_count = self._execution_counts.get(node_id, 0)
        new_count = current_count + 1
        self._execution_counts[node_id] = new_count
        
        # Create execution record
        record = NodeExecutionRecord(
            node_id=node_id,
            execution_number=new_count,
            started_at=datetime.now(),
            ended_at=None,
            status=CompletionStatus.SUCCESS,  # Will be updated on completion
            output=None,
            error=None
        )
        
        # Store record
        if node_id not in self._execution_records:
            self._execution_records[node_id] = []
        self._execution_records[node_id].append(record)
        
        # Update runtime state
        self._update_runtime_state(node_id, FlowStatus.RUNNING)
        
        # Track execution order
        self._execution_order.append(node_id)
        
        return new_count
    
    def complete_execution(
        self,
        node_id: NodeID,
        status: CompletionStatus,
        output: NodeOutputProtocol | None = None,
        error: str | None = None,
        token_usage: dict[str, int] | None = None
    ) -> None:
        """Complete the current execution for a node."""
        
        # Find the most recent incomplete record
        records = self._execution_records.get(node_id, [])
        if not records:
            raise ValueError(f"No execution started for node {node_id}")
        
        current_record = records[-1]
        if current_record.ended_at is not None:
            raise ValueError(f"Node {node_id} execution already completed")
        
        # Update record
        end_time = datetime.now()
        current_record.ended_at = end_time
        current_record.status = status
        current_record.output = output
        current_record.error = error
        current_record.token_usage = token_usage
        current_record.duration = (end_time - current_record.started_at).total_seconds()
        
        # Update quick lookups
        if output:
            self._last_outputs[node_id] = output
        
        # Update runtime state based on completion
        if status == CompletionStatus.SUCCESS:
            self._update_runtime_state(node_id, FlowStatus.WAITING)  # Ready for next iteration
        elif status == CompletionStatus.FAILED:
            self._update_runtime_state(node_id, FlowStatus.BLOCKED)
        else:
            self._update_runtime_state(node_id, FlowStatus.WAITING)
    
    def get_execution_count(self, node_id: NodeID) -> int:
        """Get total number of completed executions (0-based for conditions)."""
        return self._execution_counts.get(node_id, 0)
    
    def has_executed(self, node_id: NodeID) -> bool:
        """Check if node has executed (regardless of success/failure)."""
        records = self._execution_records.get(node_id, [])
        return len(records) > 0
    
    def get_last_output(self, node_id: NodeID) -> NodeOutputProtocol | None:
        """Get the last output regardless of current runtime state."""
        return self._last_outputs.get(node_id)
    
    def get_runtime_state(self, node_id: NodeID) -> NodeRuntimeState:
        """Get current runtime state."""
        if node_id not in self._runtime_states:
            self._runtime_states[node_id] = NodeRuntimeState(
                node_id=node_id,
                flow_status=FlowStatus.WAITING
            )
        return self._runtime_states[node_id]
    
    def update_runtime_state(self, node_id: NodeID, status: FlowStatus) -> None:
        """Update runtime flow state without affecting history."""
        self._update_runtime_state(node_id, status)
    
    def reset_for_iteration(self, node_id: NodeID) -> None:
        """Reset runtime state for next iteration without losing history."""
        runtime_state = self.get_runtime_state(node_id)
        runtime_state.flow_status = FlowStatus.READY
        runtime_state.dependencies_met = True  # Node is ready after reset
        runtime_state.is_active = True
        runtime_state.last_check = datetime.now()
        
        # Note: execution history and last output are preserved!
    
    def _update_runtime_state(self, node_id: NodeID, status: FlowStatus) -> None:
        """Internal method to update runtime state."""
        runtime_state = self.get_runtime_state(node_id)
        runtime_state.flow_status = status
        runtime_state.last_check = datetime.now()
    
    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of all executions."""
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
                    
                    # Aggregate token usage
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
            "execution_order": self._execution_order.copy()
        }
    
    def get_node_execution_history(self, node_id: NodeID) -> list[NodeExecutionRecord]:
        """Get all execution records for a node."""
        return self._execution_records.get(node_id, []).copy()
    
    def clear_history(self) -> None:
        """Clear all execution history. Use with caution!"""
        self._execution_records.clear()
        self._runtime_states.clear()
        self._execution_counts.clear()
        self._last_outputs.clear()
        self._execution_order.clear()