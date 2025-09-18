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
    # Factory
    "HandlerRegistry",
    "Optional",
    "Required",
    "ServiceRequirement",
    "ServiceSpec",
    "TokenHandlerMixin",
    # Base classes
    "TypedNodeHandler",
    "create_handler_factory_provider",
    "get_global_registry",
    "register_handler",
    # Decorators
    "requires_services",
]
