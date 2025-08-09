
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
        temp_instance = handler_class()
        node_type = temp_instance.node_type
        self._handler_classes[node_type] = handler_class

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        handler_class = self._handler_classes.get(node_type)
        if not handler_class:
            available_types = list(self._handler_classes.keys())
            log.error(f"No handler class registered for node type: {node_type}. Available types: {available_types}")
            raise ValueError(f"No handler class registered for node type: {node_type}")

        sig = inspect.signature(handler_class.__init__)
        params = list(sig.parameters.keys())

        if len(params) == 1 and params[0] == 'self':
            handler = handler_class()
            return handler
        else:
            handler = self._create_handler_with_services(handler_class)
            return handler

    def _create_handler_with_services(self, handler_class: type[TypedNodeHandler]) -> TypedNodeHandler:
        if not self._service_registry:
            raise RuntimeError("Service registry not set. Call set_service_registry first.")

        sig = inspect.signature(handler_class.__init__)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            service_name = param_name

            if service_name == 'template_service':
                service_name = 'template'
            elif service_name == 'conversation_service':
                service_name = 'conversation_service'

            key = ServiceKey(service_name)
            service = self._service_registry.get(key)
            
            if service is not None:
                kwargs[param_name] = service
            else:
                if service_name.endswith('_service'):
                    alt_name = service_name[:-8]
                    alt_key = ServiceKey(alt_name)
                    service = self._service_registry.get(alt_key)
                    if service is not None:
                        kwargs[param_name] = service
                        continue
                
                if param.default is inspect.Parameter.empty:
                    raise ValueError(f"Required service '{service_name}' not found for handler {handler_class.__name__}")

        return handler_class(**kwargs)


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