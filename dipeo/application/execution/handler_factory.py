# Handler registry, base classes, and factory for DiPeO

from abc import ABC, abstractmethod
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, TYPE_CHECKING

from pydantic import BaseModel

from .types import NodeDefinition, NodeHandler
from ..unified_service_registry import UnifiedServiceRegistry
from .typed_handler_base import TypedNodeHandler

if TYPE_CHECKING:
    from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext

T = TypeVar("T", bound=BaseModel)


# Legacy BaseNodeHandler - now just an alias for TypedNodeHandler compatibility
class BaseNodeHandler(ABC):
    """Legacy interface maintained for backward compatibility.
    
    All new handlers should use TypedNodeHandler directly.
    """

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
        context: Any,  # ExecutionContext implementation
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        pass

    def to_node_handler(self) -> NodeHandler:
        return self.execute


class HandlerRegistry:

    def __init__(self):
        self._handlers: Dict[str, NodeDefinition] = {}
        self._handler_classes: Dict[str, Type[TypedNodeHandler]] = {}
        self._service_registry: Optional[UnifiedServiceRegistry] = None

    def set_service_registry(self, service_registry: UnifiedServiceRegistry) -> None:
        # Set the service registry for dependency injection.
        self._service_registry = service_registry

    def register(self, handler: Any) -> None:
        # Register a handler instance (supports both BaseNodeHandler and TypedNodeHandler).
        node_def = NodeDefinition(
            type=handler.node_type,
            node_schema=handler.schema,
            handler=handler.to_node_handler() if hasattr(handler, 'to_node_handler') else handler.execute,
            requires_services=handler.requires_services,
            description=handler.description,
        )
        self._handlers[handler.node_type] = node_def

    def register_class(self, handler_class: Type[TypedNodeHandler]) -> None:
        # Register a handler class for later instantiation.
        # Create a temporary instance to get the node_type
        temp_instance = handler_class()
        node_type = temp_instance.node_type
        self._handler_classes[node_type] = handler_class
        # Also register the instance for immediate use
        self.register(temp_instance)

    def register_function(
        self,
        node_type: str,
        schema: Type[BaseModel],
        handler: NodeHandler,
        requires_services: Optional[List[str]] = None,
        description: str = "",
    ) -> None:
        # Register a function-based handler.
        node_def = NodeDefinition(
            type=node_type,
            node_schema=schema,
            handler=handler,
            requires_services=requires_services or [],
            description=description or f"Handler for {node_type} nodes",
        )
        self._handlers[node_type] = node_def

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        handler_class = self._handler_classes.get(node_type)
        if not handler_class:
            raise ValueError(f"No handler class registered for node type: {node_type}")

        sig = inspect.signature(handler_class.__init__)
        params = list(sig.parameters.keys())

        if len(params) == 1 and params[0] == 'self':
            return handler_class()
        else:
            return self._create_handler_with_services(handler_class)

    def _create_handler_with_services(self, handler_class: Type[TypedNodeHandler]) -> TypedNodeHandler:
        if not self._service_registry:
            raise RuntimeError("Service registry not set. Call set_service_registry first.")

        sig = inspect.signature(handler_class.__init__)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            service_name = param_name

            if service_name == 'template_service':
                service_name = 'template'
            elif service_name == 'conversation_service':
                service_name = 'conversation_service'

            try:
                service = self._service_registry.get_service(service_name)
                kwargs[param_name] = service
            except:
                if param.default is inspect.Parameter.empty:
                    if service_name.endswith('_service'):
                        alt_name = service_name[:-8]
                        try:
                            service = self._service_registry.get_service(alt_name)
                            kwargs[param_name] = service
                            continue
                        except:
                            pass
                    raise ValueError(f"Required service '{service_name}' not found for handler {handler_class.__name__}")

        return handler_class(**kwargs)

    def get(self, node_type: str) -> Optional[NodeDefinition]:
        # Get node definition by type.
        return self._handlers.get(node_type)

    def get_handler(self, node_type: str) -> Optional[NodeHandler]:
        # Get handler function by node type.
        node_def = self._handlers.get(node_type)
        return node_def.handler if node_def else None

    def list_types(self) -> List[str]:
        # List all registered node types.
        return list(self._handlers.keys())

    def clear(self) -> None:
        # Clear all registered handlers.
        self._handlers.clear()
        self._handler_classes.clear()


# Global registry instance
_global_registry = HandlerRegistry()


def register_handler(handler_class: type) -> type:
    # Decorator to register a handler class.
    # Only support TypedNodeHandler now
    if hasattr(handler_class, 'node_type') and hasattr(handler_class, 'schema'):
        # Directly register TypedNodeHandler classes
        _global_registry.register_class(handler_class)
    else:
        raise ValueError(f"Handler class {handler_class.__name__} must have node_type and schema properties")
    return handler_class


def get_global_registry() -> HandlerRegistry:
    # Get the global handler registry.
    return _global_registry


class HandlerFactory:
    # Legacy factory class for backward compatibility.

    def __init__(self, service_registry: UnifiedServiceRegistry):
        self.service_registry = service_registry
        # Set the service registry on the global registry
        _global_registry.set_service_registry(service_registry)

    def register_handler_class(self, handler_class: Type[TypedNodeHandler]) -> None:
        _global_registry.register_class(handler_class)

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        return _global_registry.create_handler(node_type)


def create_handler_factory_provider():
    # Provider function for DI container.
    def factory(service_registry: UnifiedServiceRegistry) -> HandlerFactory:
        return HandlerFactory(service_registry)
    return factory