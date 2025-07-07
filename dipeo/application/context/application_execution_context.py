"""
Application implementation of ExecutionContextPort.

This provides a lightweight execution context that wraps ExecutionState
and provides access to services via a service registry.
"""

from typing import Any, Optional

from dipeo.models import ExecutionState
from dipeo.domain.services.ports.execution_context import ExecutionContextPort


class ApplicationExecutionContext:
    """Concrete implementation of ExecutionContextPort."""
    
    def __init__(
        self, 
        execution_state: ExecutionState, 
        service_registry: Any,
        current_node_id: str = "",
        executed_nodes: Optional[list[str]] = None,
        exec_counts: Optional[dict[str, int]] = None,
    ):
        """Initialize with execution state and service registry.
        
        Args:
            execution_state: The immutable execution state
            service_registry: Registry for accessing services
            current_node_id: ID of the currently executing node
            executed_nodes: List of node IDs that have been executed
            exec_counts: Dictionary of node execution counts
        """
        self._state = execution_state
        self._service_registry = service_registry
        self._current_node_id = current_node_id
        self._executed_nodes = executed_nodes or []
        self._exec_counts = exec_counts or {}
    
    def get_node_output(self, node_id: str) -> Optional[Any]:
        """Get the output of a specific node."""
        if not self._state.node_outputs:
            return None
        output = self._state.node_outputs.get(node_id)
        if output is None:
            return None
        # Extract value from NodeOutput if present
        if hasattr(output, 'value'):
            return output.value
        return output
    
    def get_variable(self, key: str) -> Optional[Any]:
        """Get a variable from the execution context."""
        if not self._state.variables:
            return None
        return self._state.variables.get(key)
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name from the service registry."""
        return getattr(self._service_registry, service_name, None)
    
    @property
    def diagram_id(self) -> str:
        """Get the current diagram ID."""
        return self._state.diagram_id
    
    @property
    def execution_state(self) -> ExecutionState:
        """Get the underlying execution state (read-only)."""
        return self._state
    
    def get_node_execution_count(self, node_id: str) -> int:
        """Get the execution count for a specific node."""
        return self._exec_counts.get(node_id, 0)
    
    @property
    def current_node_id(self) -> str:
        """Get the ID of the currently executing node."""
        return self._current_node_id
    
    @property
    def executed_nodes(self) -> list[str]:
        """Get the list of node IDs that have been executed."""
        return self._executed_nodes
    
    def create_node_view(self, node_id: str) -> "ApplicationExecutionContext":
        """Create a lightweight view of the context for a specific node.
        
        This creates a new context with the current node ID set.
        """
        return ApplicationExecutionContext(
            execution_state=self._state,
            service_registry=self._service_registry,
            current_node_id=node_id,
            executed_nodes=self._executed_nodes,
            exec_counts=self._exec_counts,
        )