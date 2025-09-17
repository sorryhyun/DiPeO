import logging
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from dipeo.diagram_generated.enums import NodeType

from ..registry import ServiceRegistry
from .handler_base import TypedNodeHandler

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=BaseModel)

log = logging.getLogger(__name__)


def _get_node_handlers() -> dict[str, type[TypedNodeHandler]]:
    from .handlers.api_job import ApiJobNodeHandler
    from .handlers.code_job import CodeJobNodeHandler
    from .handlers.condition import ConditionNodeHandler
    from .handlers.db import DBTypedNodeHandler
    from .handlers.endpoint import EndpointNodeHandler
    from .handlers.hook import HookNodeHandler
    from .handlers.integrated_api import IntegratedApiNodeHandler
    from .handlers.ir_builder import IrBuilderNodeHandler
    from .handlers.json_schema_validator import JsonSchemaValidatorNodeHandler
    from .handlers.person_job import PersonJobNodeHandler
    from .handlers.start import StartNodeHandler
    from .handlers.sub_diagram import SubDiagramNodeHandler
    from .handlers.template_job import TemplateJobNodeHandler
    from .handlers.typescript_ast import TypescriptAstNodeHandler
    from .handlers.user_response import UserResponseNodeHandler

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
        NodeType.IR_BUILDER: IrBuilderNodeHandler,
    }


class HandlerRegistry:
    def __init__(self):
        self._handler_classes: dict[str, type[TypedNodeHandler]] = {}
        self._service_registry: ServiceRegistry | None = None
        self._initialized = False

    def set_service_registry(self, service_registry: ServiceRegistry) -> None:
        self._service_registry = service_registry

    def register_class(self, handler_class: type[TypedNodeHandler]) -> None:
        if hasattr(handler_class, "NODE_TYPE"):
            node_type = handler_class.NODE_TYPE
        else:
            temp_instance = handler_class()
            node_type = temp_instance.node_type
        self._handler_classes[node_type] = handler_class

    def _ensure_initialized(self):
        if not self._initialized:
            self._handler_classes.update(_get_node_handlers())
            self._initialized = True

    def create_handler(self, node_type: str) -> TypedNodeHandler:
        self._ensure_initialized()
        handler_class = self._handler_classes.get(node_type)
        if not handler_class:
            available_types = list(self._handler_classes.keys())
            log.error(
                f"No handler class registered for node type: {node_type}. Available types: {available_types}"
            )
            raise ValueError(f"No handler class registered for node type: {node_type}")

        return handler_class()


_global_registry = HandlerRegistry()


def register_handler(handler_class: type[TypedNodeHandler]) -> type[TypedNodeHandler]:
    """Decorator to register a handler class."""
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
