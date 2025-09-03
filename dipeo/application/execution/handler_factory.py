
import inspect
import logging
from typing import TYPE_CHECKING, TypeVar, Type, Dict

from pydantic import BaseModel

from ..registry import ServiceRegistry, ServiceKey
from .handler_base import TypedNodeHandler
from dipeo.diagram_generated.enums import NodeType

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=BaseModel)

log = logging.getLogger(__name__)

# Lazy import to avoid circular dependencies
def _get_node_handlers() -> Dict[str, Type[TypedNodeHandler]]:
    """Get handler mapping, importing handlers lazily to avoid circular imports."""
    from .handlers.start import StartNodeHandler
    from .handlers.person_job import PersonJobNodeHandler
    from .handlers.code_job import CodeJobNodeHandler
    from .handlers.condition import ConditionNodeHandler
    from .handlers.api_job import ApiJobNodeHandler
    from .handlers.endpoint import EndpointNodeHandler
    from .handlers.db import DBTypedNodeHandler
    from .handlers.user_response import UserResponseNodeHandler
    from .handlers.hook import HookNodeHandler
    from .handlers.template_job import TemplateJobNodeHandler
    from .handlers.json_schema_validator import JsonSchemaValidatorNodeHandler
    from .handlers.typescript_ast import TypescriptAstNodeHandler
    from .handlers.sub_diagram import SubDiagramNodeHandler
    from .handlers.integrated_api import IntegratedApiNodeHandler

    return {
        NodeType.START: StartNodeHandler,
        NodeType.PERSON_JOB: PersonJobNodeHandler,
        NodeType.CODE_JOB: CodeJobNodeHandler,
        NodeType.CONDITION: ConditionNodeHandler,
        NodeType.API_JOB: ApiJobNodeHandler,
        NodeType.ENDPOINT: EndpointNodeHandler,
        NodeType.DB: DBTypedNodeHandler,
        NodeType.USER_RESPONSE: UserResponseNodeHandler,
        NodeType.HOOK: HookNodeHandler,
        NodeType.TEMPLATE_JOB: TemplateJobNodeHandler,
        NodeType.JSON_SCHEMA_VALIDATOR: JsonSchemaValidatorNodeHandler,
        NodeType.TYPESCRIPT_AST: TypescriptAstNodeHandler,
        NodeType.SUB_DIAGRAM: SubDiagramNodeHandler,
        NodeType.INTEGRATED_API: IntegratedApiNodeHandler,
        # Note: PERSON_BATCH_JOB handler may be missing - add when available
    }


class HandlerRegistry:

    def __init__(self):
        # Initialize empty, handlers will be loaded lazily
        self._handler_classes: Dict[str, Type[TypedNodeHandler]] = {}
        self._service_registry: ServiceRegistry | None = None
        self._initialized = False

    def set_service_registry(self, service_registry: ServiceRegistry) -> None:
        self._service_registry = service_registry

    def register_class(self, handler_class: Type[TypedNodeHandler]) -> None:
        # Use NODE_TYPE class variable instead of instantiating
        if hasattr(handler_class, 'NODE_TYPE'):
            node_type = handler_class.NODE_TYPE
        else:
            # Fallback for handlers not yet updated
            temp_instance = handler_class()
            node_type = temp_instance.node_type
        self._handler_classes[node_type] = handler_class

    def _ensure_initialized(self):
        """Ensure handlers are loaded lazily on first use."""
        if not self._initialized:
            self._handler_classes.update(_get_node_handlers())
            self._initialized = True

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        self._ensure_initialized()
        handler_class = self._handler_classes.get(node_type)
        if not handler_class:
            available_types = list(self._handler_classes.keys())
            log.error(f"No handler class registered for node type: {node_type}. Available types: {available_types}")
            raise ValueError(f"No handler class registered for node type: {node_type}")

        # Simply instantiate the handler class with no arguments
        return handler_class()


_global_registry = HandlerRegistry()


def register_handler(handler_class: Type[TypedNodeHandler]) -> Type[TypedNodeHandler]:
    """Decorator to register a handler class.
    
    Still supported for backward compatibility, but handlers are now
    explicitly mapped in NODE_HANDLERS.
    """
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