"""Core handler infrastructure components."""

from .base import TokenHandlerMixin, TypedNodeHandler
from .decorators import Optional, Required, ServiceRequirement, ServiceSpec, requires_services
from .factory import (
    HandlerFactory,
    HandlerRegistry,
    create_handler_factory_provider,
    get_global_registry,
    register_handler,
)

__all__ = [
    "HandlerFactory",
    "HandlerRegistry",
    "Optional",
    "Required",
    "ServiceRequirement",
    "ServiceSpec",
    "TokenHandlerMixin",
    "TypedNodeHandler",
    "create_handler_factory_provider",
    "get_global_registry",
    "register_handler",
    "requires_services",
]
