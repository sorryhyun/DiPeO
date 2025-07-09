"""
Execution context port - minimal interface for handlers.

This protocol defines the minimal behavior needed by handlers to access
execution state and services without tight coupling to implementation details.
"""

from typing import Protocol, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from dipeo.models import ExecutionState


class ExecutionContextPort(Protocol):
    """Minimal execution context interface for handlers."""
    
    def get_node_output(self, node_id: str) -> Optional[Any]:
        """Get the output of a specific node."""
        ...
    
    def get_variable(self, key: str) -> Optional[Any]:
        """Get a variable from the execution context."""
        ...
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name from the service registry."""
        ...
    
    def get_node_execution_count(self, node_id: str) -> int:
        """Get the execution count for a specific node."""
        ...
    
    @property
    def diagram_id(self) -> str:
        """Get the current diagram ID."""
        ...
    
    @property
    def execution_state(self) -> "ExecutionState":
        """Get the underlying execution state (read-only)."""
        ...
    
    @property
    def current_node_id(self) -> str:
        """Get the ID of the currently executing node."""
        ...
    
    @property
    def executed_nodes(self) -> list[str]:
        """Get the list of node IDs that have been executed."""
        ...