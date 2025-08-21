
import inspect
import logging
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from ..registry import ServiceRegistry, ServiceKey
from .handler_base import TypedNodeHandler

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=BaseModel)

log = logging.getLogger(__name__)


class HandlerRegistry:

    def __init__(self):
        self._handler_classes: dict[str, type[TypedNodeHandler]] = {}
        self._service_registry: ServiceRegistry | None = None

    def set_service_registry(self, service_registry: ServiceRegistry) -> None:
        self._service_registry = service_registry

    def register_class(self, handler_class: type[TypedNodeHandler]) -> None:
        # Use NODE_TYPE class variable instead of instantiating
        if hasattr(handler_class, 'NODE_TYPE'):
            node_type = handler_class.NODE_TYPE
        else:
            # Fallback for handlers not yet updated
            temp_instance = handler_class()
            node_type = temp_instance.node_type
        self._handler_classes[node_type] = handler_class

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        handler_class = self._handler_classes.get(node_type)
        if not handler_class:
            available_types = list(self._handler_classes.keys())
            log.error(f"No handler class registered for node type: {node_type}. Available types: {available_types}")
            raise ValueError(f"No handler class registered for node type: {node_type}")

        # Simply instantiate the handler class with no arguments
        return handler_class()


_global_registry = HandlerRegistry()


def register_handler(handler_class: type[TypedNodeHandler]) -> type[TypedNodeHandler]:
    _global_registry.register_class(handler_class)
    return handler_class


def get_global_registry() -> HandlerRegistry:
    return _global_registry


class HandlerFactory:

    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        _global_registry.set_service_registry(service_registry)

    def register_handler_class(self, handler_class: type[TypedNodeHandler]) -> None:
        _global_registry.register_class(handler_class)

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        return _global_registry.create_handler(node_type)


def create_handler_factory_provider():
    def factory(service_registry: ServiceRegistry) -> HandlerFactory:
        return HandlerFactory(service_registry)
    return factory