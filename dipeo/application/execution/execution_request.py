"""Unified execution request objects for handler interface."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.models import NodeExecutionStatus

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext

# Type variable for node types
T = TypeVar('T', bound=ExecutableNode)


@dataclass
class ExecutionRequest(Generic[T]):
    """Unified request object for node execution.
    
    This encapsulates all parameters needed for node execution,
    providing a cleaner interface for handlers.
    """
    
    # Core execution data
    node: T
    context: "ExecutionContext"
    inputs: dict[str, Any] = field(default_factory=dict)
    services: dict[str, Any] = field(default_factory=dict)
    
    # Execution metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_id: str = ""
    iteration: int = 1
    
    # Runtime references
    runtime: Optional["ExecutionRuntime"] = None
    
    @property
    def node_id(self) -> str:
        """Get the node ID."""
        return self.node.id
    
    @property
    def node_type(self) -> str:
        """Get the node type."""
        return self.node.node_type
    
    @property
    def execution_count(self) -> int:
        """Get the execution count for this node."""
        if self.context:
            return self.context.get_node_execution_count(self.node_id)
        return 1
    
    @property
    def node_status(self) -> Optional[NodeExecutionStatus]:
        """Get the current node status."""
        if self.context:
            state = self.context.get_node_state(self.node_id)
            return state.status if state else None
        return None
    
    def get_service(self, name: str) -> Any:
        """Get a service by name."""
        return self.services.get(name)
    
    def get_input(self, name: str, default: Any = None) -> Any:
        """Get an input value by name."""
        return self.inputs.get(name, default)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the request."""
        self.metadata[key] = value
    
    def has_service(self, name: str) -> bool:
        """Check if a service is available."""
        return name in self.services
    
    def has_input(self, name: str) -> bool:
        """Check if an input is available."""
        return name in self.inputs
    
    def with_inputs(self, inputs: dict[str, Any]) -> "ExecutionRequest[T]":
        """Create a new request with updated inputs."""
        return ExecutionRequest(
            node=self.node,
            context=self.context,
            inputs={**self.inputs, **inputs},
            services=self.services,
            metadata=self.metadata,
            execution_id=self.execution_id,
            iteration=self.iteration,
            runtime=self.runtime
        )
    
    def with_metadata(self, metadata: dict[str, Any]) -> "ExecutionRequest[T]":
        """Create a new request with updated metadata."""
        return ExecutionRequest(
            node=self.node,
            context=self.context,
            inputs=self.inputs,
            services=self.services,
            metadata={**self.metadata, **metadata},
            execution_id=self.execution_id,
            iteration=self.iteration,
            runtime=self.runtime
        )


class ServiceProvider:
    """Type-safe service provider for execution requests."""
    
    def __init__(self, services: dict[str, Any]):
        self._services = services
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a service by key."""
        return self._services.get(key, default)
    
    def require(self, key: str) -> Any:
        """Get a required service, raising if not found."""
        if key not in self._services:
            raise ValueError(f"Required service '{key}' not found")
        return self._services[key]
    
    def has(self, key: str) -> bool:
        """Check if a service is available."""
        return key in self._services
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access."""
        return self.require(key)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return self.has(key)