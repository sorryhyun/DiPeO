"""
Application implementation of ExecutionContextPort.

This provides a lightweight execution context that wraps ExecutionState
and provides access to services via a service registry.
"""

from typing import Any, Optional

from dipeo.models import ExecutionState
from dipeo.domain.domains.ports.execution_context import ExecutionContextPort


class ApplicationExecutionContext:
    """Concrete implementation of ExecutionContextPort."""
    
    def __init__(self, execution_state: ExecutionState, service_registry: Any):
        """Initialize with execution state and service registry.
        
        Args:
            execution_state: The immutable execution state
            service_registry: Registry for accessing services
        """
        self._state = execution_state
        self._service_registry = service_registry
    
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
    
    def create_node_view(self, node_id: str) -> "ApplicationExecutionContext":
        """Create a lightweight view of the context for a specific node.
        
        This returns the same context since the state is immutable.
        Future versions might add node-specific filtering.
        """
        return self