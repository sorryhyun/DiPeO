"""Hybrid execution context supporting both old and new output/state systems.

This module provides a compatibility layer that allows gradual migration
from the legacy NodeOutput system to the new type-safe protocol-based system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dipeo.core.execution.execution_tracker import CompletionStatus, ExecutionTracker
from dipeo.core.execution.node_output import (
    LegacyNodeOutput,
    NodeOutputProtocol,
    OutputCompatibilityWrapper,
)

if TYPE_CHECKING:
    from dipeo.models import ExecutionState, NodeID, NodeOutput


class HybridExecutionContext:
    """Context supporting both old and new output/state systems."""
    
    def __init__(
        self,
        legacy_state: ExecutionState | None = None,
        use_new_system: bool = False
    ):
        self.legacy_state = legacy_state
        self.execution_tracker = ExecutionTracker()
        self._use_new_system = use_new_system
        self.metadata: dict[str, Any] = {}
        self.variables: dict[str, Any] = {}
        
        # Make tracker available in metadata for handlers
        self.metadata["execution_tracker"] = self.execution_tracker
    
    def set_node_output(self, node_id: NodeID, output: Any) -> None:
        """Legacy output setting with migration."""
        if self._use_new_system:
            # Convert legacy output to modern format
            if isinstance(output, NodeOutputProtocol):
                modern_output = output
            else:
                # Handle legacy dict format
                if isinstance(output, dict) and "value" in output:
                    legacy_output = LegacyNodeOutput(
                        output.get("value"),
                        output.get("metadata", {})
                    )
                else:
                    # Handle direct value
                    legacy_output = LegacyNodeOutput(output, {})
                
                modern_output = legacy_output.to_modern(node_id)
            
            # Store in new system
            # Note: In real implementation, this would be called after execution completes
            # For now, we'll mark it as successful completion
            if node_id not in [record.node_id for records in self.execution_tracker._execution_records.values() for record in records if not record.is_complete()]:
                # Start execution if not already started
                self.execution_tracker.start_execution(node_id)
            
            self.execution_tracker.complete_execution(
                node_id,
                CompletionStatus.SUCCESS,
                modern_output
            )
        else:
            # Use legacy system
            if hasattr(self.legacy_state, 'set_node_output'):
                self.legacy_state.set_node_output(node_id, output)
            else:
                # Store in node_outputs dict
                if not hasattr(self.legacy_state, 'node_outputs'):
                    self.legacy_state.node_outputs = {}
                self.legacy_state.node_outputs[node_id] = output
    
    def get_node_output(self, node_id: NodeID) -> Any:
        """Legacy output retrieval with fallback."""
        if self._use_new_system:
            modern_output = self.execution_tracker.get_last_output(node_id)
            if modern_output:
                # Return wrapped output for compatibility
                return OutputCompatibilityWrapper(modern_output)
            return None
        else:
            # Use legacy system
            if hasattr(self.legacy_state, 'get_node_output'):
                return self.legacy_state.get_node_output(node_id)
            else:
                # Get from node_outputs dict
                if hasattr(self.legacy_state, 'node_outputs'):
                    return self.legacy_state.node_outputs.get(node_id)
                return None
    
    def has_node_executed(self, node_id: NodeID) -> bool:
        """Check if a node has executed."""
        if self._use_new_system:
            return self.execution_tracker.has_executed(node_id)
        else:
            # Check legacy system
            if hasattr(self.legacy_state, 'node_outputs'):
                return node_id in self.legacy_state.node_outputs
            return False
    
    def get_execution_count(self, node_id: NodeID) -> int:
        """Get execution count for a node."""
        if self._use_new_system:
            return self.execution_tracker.get_execution_count(node_id)
        else:
            # Check legacy system
            if hasattr(self.legacy_state, 'exec_counts'):
                return self.legacy_state.exec_counts.get(node_id, 0)
            return 0
    
    def increment_execution_count(self, node_id: NodeID) -> None:
        """Increment execution count (legacy compatibility)."""
        if self._use_new_system:
            # In new system, this is handled by start_execution
            pass
        else:
            # Update legacy system
            if hasattr(self.legacy_state, 'exec_counts'):
                if not hasattr(self.legacy_state.exec_counts, '__setitem__'):
                    self.legacy_state.exec_counts = {}
                current = self.legacy_state.exec_counts.get(node_id, 0)
                self.legacy_state.exec_counts[node_id] = current + 1
    
    def reset_node_for_iteration(self, node_id: NodeID) -> None:
        """Reset node for iteration."""
        if self._use_new_system:
            # New system preserves history
            self.execution_tracker.reset_for_iteration(node_id)
        else:
            # Legacy system loses history (the problem we're fixing!)
            if hasattr(self.legacy_state, 'node_states') and node_id in self.legacy_state.node_states:
                # Reset status but try to preserve output
                from dipeo.models import NodeExecutionStatus
                self.legacy_state.node_states[node_id].status = NodeExecutionStatus.PENDING
    
    def enable_new_system(self) -> None:
        """Enable the new execution tracking system."""
        self._use_new_system = True
        self.metadata["execution_tracker"] = self.execution_tracker
    
    def disable_new_system(self) -> None:
        """Disable the new execution tracking system (use legacy)."""
        self._use_new_system = False
    
    def migrate_legacy_outputs(self) -> None:
        """Migrate existing legacy outputs to the new system."""
        if not self.legacy_state or not hasattr(self.legacy_state, 'node_outputs'):
            return
        
        for node_id, output in self.legacy_state.node_outputs.items():
            if isinstance(output, dict) and "value" in output:
                legacy = LegacyNodeOutput(output["value"], output.get("metadata", {}))
            else:
                legacy = LegacyNodeOutput(output, {})
            
            modern = legacy.to_modern(node_id)
            
            # Start and complete execution in tracker
            self.execution_tracker.start_execution(node_id)
            self.execution_tracker.complete_execution(
                node_id,
                CompletionStatus.SUCCESS,
                modern
            )