"""
Unified execution context implementing the core ExecutionContext protocol.

This provides a protocol-compliant implementation that bridges the application layer
with the core protocols, replacing the existing ApplicationExecutionContext with a
cleaner, more maintainable version.
"""

from typing import Any

from dipeo.core.dynamic.execution_context import ExecutionContext
from dipeo.models import ExecutionState, NodeExecutionStatus, NodeID, NodeOutput, NodeState


class UnifiedExecutionContext(ExecutionContext):
    """Protocol-compliant execution context implementation.
    
    This context manages the runtime state during diagram execution,
    providing full implementation of the core ExecutionContext protocol.
    """
    
    def __init__(
        self,
        execution_state: ExecutionState,
        service_registry: Any,
        current_node_id: str = "",
        executed_nodes: list[str] | None = None,
        exec_counts: dict[str, int] | None = None,
    ):
        """Initialize the unified execution context.
        
        Args:
            execution_state: The execution state
            service_registry: Service registry for accessing application services
            current_node_id: ID of the currently executing node
            executed_nodes: List of node IDs that have been executed
            exec_counts: Dictionary of node execution counts
        """
        self._execution_id = execution_state.id
        self._execution_state = execution_state  # Store for compatibility
        self._service_registry = service_registry
        self._current_node: NodeID | None = NodeID(current_node_id) if current_node_id else None
        self._executed_nodes = executed_nodes or []
        self._exec_counts = exec_counts or {}
        
        # Initialize state tracking
        self._node_states: dict[NodeID, NodeState] = {}
        self._node_results: dict[NodeID, dict[str, Any]] = {}
        self._global_context: dict[str, Any] = {}
        
        # Populate from execution state
        self._populate_from_state(execution_state)
    
    
    def _populate_from_state(self, state: ExecutionState) -> None:
        """Populate context from an existing execution state.
        
        Args:
            state: The execution state to populate from
        """
        if state.node_states:
            for node_id, node_state in state.node_states.items():
                self._node_states[NodeID(node_id)] = node_state
        
        if state.node_outputs:
            for node_id, output in state.node_outputs.items():
                # Convert NodeOutput to result dict
                result = {"value": output.value}
                if output.metadata:
                    result["metadata"] = output.metadata
                self._node_results[NodeID(node_id)] = result
        
        if state.variables:
            self._global_context.update(state.variables)
    
    # ExecutionContext Protocol Implementation
    
    
    
    
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the execution state of a specific node."""
        return self._node_states.get(node_id)
    
    def set_node_state(self, node_id: NodeID, state: NodeState) -> None:
        """Set the execution state of a node."""
        self._node_states[node_id] = state
    
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node."""
        return self._node_results.get(node_id)
    
    
    
    def get_completed_nodes(self) -> list[NodeID]:
        """Get list of all completed node IDs."""
        completed = []
        for node_id, state in self._node_states.items():
            if state.status == NodeExecutionStatus.COMPLETED:
                completed.append(node_id)
        return completed
    
    
    # Additional methods for compatibility with existing code
    
    def get_node_output(self, node_id: str) -> Any:
        """Get the output of a specific node.
        
        Convenience method that extracts the value from node results.
        """
        result = self.get_node_result(NodeID(node_id))
        if result:
            return result.get("value")
        
        # Check in execution state node outputs
        state = self.get_node_state(NodeID(node_id))
        if state and state.output:
            return state.output.value
        return None
    
    def get_variable(self, key: str) -> Any:
        """Get a variable from the execution context.
        
        Implementation of ExecutionContext protocol method.
        """
        return self._global_context.get(key)
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name from the registry.
        
        Application-specific method for service access.
        """
        return self._service_registry.get(service_name)
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the execution count for a specific node.
        
        Implementation of ExecutionContext protocol method.
        """
        # First check the execution state for the most up-to-date count
        if hasattr(self, '_execution_state') and self._execution_state:
            node_state = self._execution_state.node_states.get(str(node_id))
            if node_state:
                # Use extra fields instead of metadata
                return getattr(node_state, "exec_count", 0)
        # Fall back to cached exec counts
        return self._exec_counts.get(str(node_id), 0)
    
    @property
    def current_node_id(self) -> str:
        """Get the ID of the currently executing node.
        
        Convenience property for backward compatibility.
        """
        return str(self._current_node) if self._current_node else ""
    
    @property
    def executed_nodes(self) -> list[str]:
        """Get the list of node IDs that have been executed.
        
        Convenience property for backward compatibility.
        """
        return self._executed_nodes
    
    
    
    @property
    def execution_state(self) -> ExecutionState:
        """Get the underlying execution state (read-only).
        
        Application-specific property for state access.
        """
        # Need to store execution state reference
        if hasattr(self, '_execution_state'):
            return self._execution_state
        # Build execution state from current data
        return self.to_execution_state("")
    
    @property
    def node_outputs(self) -> dict[str, NodeOutput]:
        """Get all node outputs from the execution state."""
        if hasattr(self, '_execution_state') and self._execution_state:
            return self._execution_state.node_outputs.copy()
        return {}
    
    
    
    def increment_execution_count(self, node_id: NodeID) -> None:
        """Increment and track execution count for a node.
        
        Args:
            node_id: The ID of the node to increment count for
        """
        current = self.get_node_execution_count(node_id)
        self._exec_counts[str(node_id)] = current + 1
        
        # Update execution state
        if hasattr(self, '_execution_state') and self._execution_state:
            self._execution_state.exec_counts[str(node_id)] = current + 1
        
        # Track executed nodes
        if str(node_id) not in self._executed_nodes:
            self._executed_nodes.append(str(node_id))
            if hasattr(self, '_execution_state') and self._execution_state:
                if str(node_id) not in self._execution_state.executed_nodes:
                    self._execution_state.executed_nodes.append(str(node_id))
    
    def resolve_inputs(self, node: "ExecutableNode", diagram: "ExecutableDiagram") -> dict[str, Any]:
        """Resolve all inputs for a node based on edges and outputs.
        
        Args:
            node: The node to resolve inputs for
            diagram: The diagram containing edge information
            
        Returns:
            Dictionary of resolved inputs
        """
        from dipeo.application.execution.input.typed_input_resolution import TypedInputResolutionService
        from dipeo.core.static.generated_nodes import PersonJobNode
        
        # Create typed input resolution service
        typed_input_service = TypedInputResolutionService()
        
        # Get memory config if this is a PersonJobNode
        node_memory_config = None
        if isinstance(node, PersonJobNode) and node.memory_config:
            node_memory_config = node.memory_config
        
        # Resolve inputs using the typed ExecutableDiagram
        inputs = typed_input_service.resolve_inputs_for_node(
            node_id=str(node.id),
            node_type=node.type,
            diagram=diagram,
            node_outputs=self.node_outputs,
            node_exec_counts=self._exec_counts.copy(),
            node_memory_config=node_memory_config
        )
        
        return inputs
    
    def complete_node(self, node_id: NodeID, output: Any | None = None) -> None:
        """Mark node complete with output in one operation.
        
        Args:
            node_id: The ID of the node to complete
            output: The output value from the node execution
        """
        # Update node state to completed
        node_state = self.get_node_state(node_id) or NodeState(status=NodeExecutionStatus.PENDING)
        node_state.status = NodeExecutionStatus.COMPLETED
        self.set_node_state(node_id, node_state)
        
        # Store output if provided
        if output is not None:
            # Convert to result dict format
            if isinstance(output, NodeOutput):
                result = {"value": output.value}
                if output.metadata:
                    result["metadata"] = output.metadata
            else:
                result = {"value": output}
            self._node_results[node_id] = result
            
            # Also update in execution state
            if hasattr(self, '_execution_state') and self._execution_state:
                if not isinstance(output, NodeOutput):
                    output = NodeOutput(node_id=node_id, value=output)
                self._execution_state.node_outputs[str(node_id)] = output
    
    def reset_node(self, node_id: NodeID) -> None:
        """Reset node state for loops.
        
        Args:
            node_id: The ID of the node to reset
        """
        # Reset state to pending
        node_state = self.get_node_state(node_id) or NodeState(status=NodeExecutionStatus.COMPLETED)
        node_state.status = NodeExecutionStatus.PENDING
        node_state.started_at = None
        node_state.ended_at = None
        node_state.error = None
        self.set_node_state(node_id, node_state)
        
        # Clear any previous output
        if node_id in self._node_results:
            del self._node_results[node_id]
        
        # Clear from execution state
        if hasattr(self, '_execution_state') and self._execution_state:
            if str(node_id) in self._execution_state.node_outputs:
                del self._execution_state.node_outputs[str(node_id)]
    
    def to_execution_state(self, diagram_id: str) -> ExecutionState:
        """Convert this context to an ExecutionState for persistence.
        
        Args:
            diagram_id: The ID of the diagram being executed
            
        Returns:
            An ExecutionState instance with current context data
        """
        from datetime import datetime

        from dipeo.models import ExecutionID, ExecutionStatus, TokenUsage
        
        # Convert results back to NodeOutput format
        node_outputs = {}
        for node_id, result in self._node_results.items():
            output = NodeOutput(
                value=result.get("value"),
                metadata=result.get("metadata"),
                node_id=node_id
            )
            node_outputs[str(node_id)] = output
        
        # Calculate aggregate token usage
        total_input = 0
        total_output = 0
        for state in self._node_states.values():
            if state.token_usage:
                total_input += state.token_usage.input
                total_output += state.token_usage.output
        
        # Determine overall status
        has_failed = any(s.status == NodeExecutionStatus.FAILED for s in self._node_states.values())
        has_running = any(s.status == NodeExecutionStatus.RUNNING for s in self._node_states.values())
        
        if has_failed:
            status = ExecutionStatus.FAILED
        elif has_running:
            status = ExecutionStatus.RUNNING
        else:
            status = ExecutionStatus.COMPLETED
        
        from dipeo.models import DiagramID
        
        return ExecutionState(
            id=ExecutionID(self._execution_id),
            status=status,
            diagram_id=DiagramID(diagram_id) if diagram_id else None,
            started_at=datetime.now().isoformat(),
            node_states={str(k): v for k, v in self._node_states.items()},
            node_outputs=node_outputs,
            token_usage=TokenUsage(input=total_input, output=total_output),
            variables=self._global_context,
            is_active=has_running,
            exec_counts=self._exec_counts.copy(),
            executed_nodes=self._executed_nodes.copy()
        )