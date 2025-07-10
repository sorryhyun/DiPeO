"""Execution protocols and interfaces."""

from .protocols import ExecutionObserver
from .interfaces import ArrowProcessorProtocol
from .service_registry import ServiceRegistryProtocol, TypedServiceRegistryProtocol

__all__ = [
    "ExecutionObserver",
    "ArrowProcessorProtocol",
    "ServiceRegistryProtocol",
    "TypedServiceRegistryProtocol",
]