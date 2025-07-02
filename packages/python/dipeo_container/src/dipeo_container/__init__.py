"""DiPeO Dependency Injection Container."""

from .container import Container, init_resources, shutdown_resources
from .providers import create_provider_overrides

__all__ = [
    "Container",
    "create_provider_overrides",
    "init_resources",
    "shutdown_resources",
]
__version__ = "0.1.0"
