# Handler registry, base classes, and factory for DiPeO

import inspect
import logging
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from ..unified_service_registry import UnifiedServiceRegistry
from .handler_base import TypedNodeHandler

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=BaseModel)

log = logging.getLogger(__name__)


class HandlerRegistry:

    def __init__(self):
        self._handler_classes: dict[str, type[TypedNodeHandler]] = {}
        self._service_registry: UnifiedServiceRegistry | None = None

    def set_service_registry(self, service_registry: UnifiedServiceRegistry) -> None:
        # Set the service registry for dependency injection.
        self._service_registry = service_registry

    def register_class(self, handler_class: type[TypedNodeHandler]) -> None:
        # Register a handler class for later instantiation.
        # Create a temporary instance to get the node_type
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
            
            # Skip *args and **kwargs parameters
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            service_name = param_name

            if service_name == 'template_service':
                service_name = 'template'
            elif service_name == 'conversation_service':
                service_name = 'conversation_service'

            try:
                service = self._service_registry.get_service(service_name)
                kwargs[param_name] = service
            except Exception:
                if param.default is inspect.Parameter.empty:
                    if service_name.endswith('_service'):
                        alt_name = service_name[:-8]
                        try:
                            service = self._service_registry.get_service(alt_name)
                            kwargs[param_name] = service
                            continue
                        except Exception:
                            pass
                    raise ValueError(f"Required service '{service_name}' not found for handler {handler_class.__name__}") from None

        return handler_class(**kwargs)


# Global registry instance
_global_registry = HandlerRegistry()


def register_handler(handler_class: type[TypedNodeHandler]) -> type[TypedNodeHandler]:
    # Decorator to register a handler class.
    _global_registry.register_class(handler_class)
    return handler_class


def get_global_registry() -> HandlerRegistry:
    # Get the global handler registry.
    return _global_registry


class HandlerFactory:
    # Factory class for creating handlers with dependency injection.

    def __init__(self, service_registry: UnifiedServiceRegistry):
        self.service_registry = service_registry
        # Set the service registry on the global registry
        _global_registry.set_service_registry(service_registry)

    def register_handler_class(self, handler_class: type[TypedNodeHandler]) -> None:
        _global_registry.register_class(handler_class)

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        return _global_registry.create_handler(node_type)


def create_handler_factory_provider():
    # Provider function for DI container.
    def factory(service_registry: UnifiedServiceRegistry) -> HandlerFactory:
        return HandlerFactory(service_registry)
    return factory