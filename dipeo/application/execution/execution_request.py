"""Unified execution request objects for handler interface."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, Union

from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.diagram_generated import Status

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

T = TypeVar('T', bound=ExecutableNode)


@dataclass
class ExecutionRequest(Generic[T]):
    """Unified request object for node execution."""
    
    node: T
    context: "ExecutionContext"
    inputs: dict[str, Any] = field(default_factory=dict)
    services: Union[dict[str, Any], "ServiceRegistry"] = field(default_factory=dict)
    
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_id: str = ""
    iteration: int = 1
    
    parent_container: Optional["Container"] = None
    parent_registry: Optional["ServiceRegistry"] = None
    
    @property
    def node_id(self) -> str:
        return self.node.id
    
    @property
    def node_type(self) -> str:
        return self.node.node_type
    
    @property
    def execution_count(self) -> int:
        if self.context:
            return self.context.get_node_execution_count(self.node_id)
        return 1
    
    @property
    def node_status(self) -> Optional[Status]:
        if self.context:
            state = self.context.get_node_state(self.node_id)
            return state.status if state else None
        return None
    
    def get_service(self, name: str) -> Any:
        if isinstance(self.services, dict):
            return self.services.get(name)
        else:
            # Try to resolve from ServiceRegistry properly
            from dipeo.application.registry import ServiceKey
            key = ServiceKey(name)
            # Use resolve() instead of get() to properly handle factories
            try:
                return self.services.resolve(key)
            except KeyError:
                # Fall back to get() with None default
                return self.services.get(key)
    
    def get_input(self, name: str, default: Any = None) -> Any:
        return self.inputs.get(name, default)
    
    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value
    
    def has_service(self, name: str) -> bool:
        if isinstance(self.services, dict):
            return name in self.services
        else:
            from dipeo.application.registry import ServiceKey
            key = ServiceKey(name)
            return self.services.has(key)
    
    def has_input(self, name: str) -> bool:
        return name in self.inputs
    
    def create_sub_registry(self) -> Optional["ServiceRegistry"]:
        """Create a hierarchical registry for sub-execution."""
        if self.parent_registry:
            return self.parent_registry.create_child()
        return None
    
    def with_inputs(self, inputs: dict[str, Any]) -> "ExecutionRequest[T]":
        return ExecutionRequest(
            node=self.node,
            context=self.context,
            inputs={**self.inputs, **inputs},
            services=self.services,
            metadata=self.metadata,
            execution_id=self.execution_id,
            iteration=self.iteration,
            parent_container=self.parent_container,
            parent_registry=self.parent_registry
        )
    
    def with_metadata(self, metadata: dict[str, Any]) -> "ExecutionRequest[T]":
        return ExecutionRequest(
            node=self.node,
            context=self.context,
            inputs=self.inputs,
            services=self.services,
            metadata={**self.metadata, **metadata},
            execution_id=self.execution_id,
            iteration=self.iteration,
            parent_container=self.parent_container,
            parent_registry=self.parent_registry
        )


class ServiceProvider:
    """Type-safe service provider for execution requests."""
    
    def __init__(self, services: dict[str, Any]):
        self._services = services
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._services.get(key, default)
    
    def require(self, key: str) -> Any:
        if key not in self._services:
            raise ValueError(f"Required service '{key}' not found")
        return self._services[key]
    
    def has(self, key: str) -> bool:
        return key in self._services
    
    def __getitem__(self, key: str) -> Any:
        return self.require(key)
    
    def __contains__(self, key: str) -> bool:
        return self.has(key)