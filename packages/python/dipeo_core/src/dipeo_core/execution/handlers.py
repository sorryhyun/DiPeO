"""Handler registry and base classes for DiPeO."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from .types import NodeDefinition, NodeHandler
from ..unified_context import UnifiedExecutionContext

T = TypeVar("T", bound=BaseModel)


class BaseNodeHandler(ABC):

    @property
    @abstractmethod
    def node_type(self) -> str:
        pass

    @property
    @abstractmethod
    def schema(self) -> Type[BaseModel]:
        pass

    @property
    def requires_services(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return f"Handler for {self.node_type} nodes"

    @abstractmethod
    async def execute(
        self,
        props: BaseModel,
        context: UnifiedExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        pass

    def to_node_handler(self) -> NodeHandler:
        return self.execute


class HandlerRegistry:

    def __init__(self):
        self._handlers: Dict[str, NodeDefinition] = {}

    def register(self, handler: BaseNodeHandler) -> None:
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
        node_def = NodeDefinition(
            type=node_type,
            node_schema=schema,
            handler=handler,
            requires_services=requires_services or [],
            description=description or f"Handler for {node_type} nodes",
        )
        self._handlers[node_type] = node_def

    def get(self, node_type: str) -> Optional[NodeDefinition]:
        return self._handlers.get(node_type)

    def get_handler(self, node_type: str) -> Optional[NodeHandler]:
        node_def = self._handlers.get(node_type)
        return node_def.handler if node_def else None

    def list_types(self) -> List[str]:
        return list(self._handlers.keys())

    def clear(self) -> None:
        self._handlers.clear()


# Global registry instance
_global_registry = HandlerRegistry()


def create_node_output(
    value: Dict[str, Any] | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Any:
    from dipeo_domain import NodeOutput

    return NodeOutput(value=value or {}, metadata=metadata)


def register_handler(handler_class: type[BaseNodeHandler]) -> type[BaseNodeHandler]:
    # Instantiate the handler and register it
    handler_instance = handler_class()
    _global_registry.register(handler_instance)
    return handler_class


def get_global_registry() -> HandlerRegistry:
    return _global_registry
