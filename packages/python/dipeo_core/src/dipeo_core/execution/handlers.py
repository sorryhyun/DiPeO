"""Handler registry and base classes for DiPeO."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from .types import NodeDefinition, NodeHandler, RuntimeContext

T = TypeVar("T", bound=BaseModel)


class BaseNodeHandler(ABC):
    """Abstract base class for node handlers."""

    @property
    @abstractmethod
    def node_type(self) -> str:
        """Return the node type this handler processes."""
        pass

    @property
    @abstractmethod
    def schema(self) -> Type[BaseModel]:
        """Return the Pydantic schema for node properties."""
        pass

    @property
    def requires_services(self) -> List[str]:
        """Return list of required service names."""
        return []

    @property
    def description(self) -> str:
        """Return handler description."""
        return f"Handler for {self.node_type} nodes"

    @abstractmethod
    async def execute(
        self,
        props: BaseModel,
        context: RuntimeContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        """Execute the node logic.

        Args:
            props: Validated node properties
            context: Runtime execution context
            inputs: Input data from connected nodes
            services: Injected service instances

        Returns:
            Node output data
        """
        pass

    def to_node_handler(self) -> NodeHandler:
        """Convert to NodeHandler protocol."""
        return self.execute


class HandlerRegistry:
    """Registry for node handlers."""

    def __init__(self):
        self._handlers: Dict[str, NodeDefinition] = {}

    def register(self, handler: BaseNodeHandler) -> None:
        """Register a node handler.

        Args:
            handler: The handler to register
        """
        node_def = NodeDefinition(
            type=handler.node_type,
            node_schema=handler.schema,
            handler=handler.to_node_handler(),
            requires_services=handler.requires_services,
            description=handler.description,
        )
        self._handlers[handler.node_type] = node_def

    def register_function(
        self,
        node_type: str,
        schema: Type[BaseModel],
        handler: NodeHandler,
        requires_services: Optional[List[str]] = None,
        description: str = "",
    ) -> None:
        """Register a function as a node handler.

        Args:
            node_type: The node type
            schema: Pydantic schema for properties
            handler: The handler function
            requires_services: Optional list of required services
            description: Optional handler description
        """
        node_def = NodeDefinition(
            type=node_type,
            node_schema=schema,
            handler=handler,
            requires_services=requires_services or [],
            description=description or f"Handler for {node_type} nodes",
        )
        self._handlers[node_type] = node_def

    def get(self, node_type: str) -> Optional[NodeDefinition]:
        """Get a handler definition by node type.

        Args:
            node_type: The node type to look up

        Returns:
            NodeDefinition if found, None otherwise
        """
        return self._handlers.get(node_type)

    def get_handler(self, node_type: str) -> Optional[NodeHandler]:
        """Get a handler function by node type.

        Args:
            node_type: The node type to look up

        Returns:
            NodeHandler if found, None otherwise
        """
        node_def = self._handlers.get(node_type)
        return node_def.handler if node_def else None

    def list_types(self) -> List[str]:
        """List all registered node types."""
        return list(self._handlers.keys())

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()


# Global registry instance
_global_registry = HandlerRegistry()


def register_handler(handler_class: type[BaseNodeHandler]) -> type[BaseNodeHandler]:
    """Decorator to register a handler class.

    Example:
        @register_handler
        class MyHandler(BaseNodeHandler):
            ...
    """
    # Instantiate the handler and register it
    handler_instance = handler_class()
    _global_registry.register(handler_instance)
    return handler_class


def get_global_registry() -> HandlerRegistry:
    """Get the global handler registry."""
    return _global_registry