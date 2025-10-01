"""Unified execution request objects for handler interface."""

import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, Union, cast

from dipeo.diagram_generated import Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceKey, ServiceRegistry
    from dipeo.domain.execution.execution_context import ExecutionContext

T = TypeVar("T", bound=ExecutableNode)


@dataclass
class ExecutionRequest[T: ExecutableNode]:
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

    _handler_state: dict[str, Any] = field(default_factory=dict)

    @property
    def node_id(self) -> str:
        return self.node.id

    @property
    def node_type(self) -> str:
        return self.node.node_type

    @property
    def execution_count(self) -> int:
        if self.context:
            return self.context.state.get_node_execution_count(self.node_id)
        return 1

    @property
    def node_status(self) -> Status | None:
        if self.context:
            state = self.context.state.get_node_state(self.node_id)
            return state.status if state else None
        return None

    def get_service(self, name: str) -> Any:
        """Legacy service resolution method.

        DEPRECATED: Use get_required_service() or get_optional_service() instead.
        """
        warnings.warn(
            "get_service() is deprecated. Use get_required_service() or get_optional_service() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if isinstance(self.services, dict):
            return self.services.get(name)
        else:
            from dipeo.application.registry import ServiceKey

            key = ServiceKey(name)
            try:
                return self.services.resolve(key)
            except KeyError:
                return self.services.get(key)

    def get_required_service[S](self, key: Union["ServiceKey[S]", str]) -> S:
        """Get a required service, raising KeyError if not found.

        Args:
            key: Service key or name string

        Returns:
            The service instance

        Raises:
            KeyError: If the service is not found
        """
        from dipeo.application.registry import ServiceKey

        # Handle string keys for backward compatibility
        if isinstance(key, str):
            service_key = ServiceKey(key)
            name = key
        else:
            service_key = key
            name = key.name

        if isinstance(self.services, dict):
            if name not in self.services:
                raise KeyError(f"Required service '{name}' not found in service container")
            return cast(S, self.services[name])
        else:
            # ServiceRegistry.resolve already raises KeyError if not found
            return self.services.resolve(service_key)

    def get_optional_service[S](
        self, key: Union["ServiceKey[S]", str], default: S | None = None
    ) -> S | None:
        """Get an optional service, returning default if not found.

        Args:
            key: Service key or name string
            default: Default value to return if service not found

        Returns:
            The service instance or default value
        """
        from dipeo.application.registry import ServiceKey

        # Handle string keys for backward compatibility
        if isinstance(key, str):
            service_key = ServiceKey(key)
            name = key
        else:
            service_key = key
            name = key.name

        if isinstance(self.services, dict):
            return cast(S, self.services.get(name, default))
        else:
            try:
                return self.services.resolve(service_key)
            except KeyError:
                return default

    def get_input(self, name: str, default: Any = None) -> Any:
        return self.inputs.get(name, default)

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def has_service(self, name: str) -> bool:
        if isinstance(self.services, dict):
            return name in self.services
        else:
            from dipeo.application.registry import ServiceKey

            return self.services.has(ServiceKey(name))

    def has_input(self, name: str) -> bool:
        return name in self.inputs

    def set_handler_state(self, key: str, value: Any) -> None:
        """Store handler-specific state for this request.

        Args:
            key: State key
            value: State value
        """
        self._handler_state[key] = value

    def get_handler_state(self, key: str, default: Any = None) -> Any:
        """Retrieve handler-specific state for this request.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self._handler_state.get(key, default)

    def clear_handler_state(self) -> None:
        """Clear all handler-specific state."""
        self._handler_state.clear()

    def create_sub_registry(self) -> Optional["ServiceRegistry"]:
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
            parent_registry=self.parent_registry,
            _handler_state=self._handler_state.copy(),
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
            parent_registry=self.parent_registry,
            _handler_state=self._handler_state.copy(),
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
