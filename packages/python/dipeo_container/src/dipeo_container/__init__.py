"""DiPeO Dependency Injection Container - DEPRECATED.

This package has been migrated to dipeo.container.
Please update your imports to use the new location.
"""

import warnings

# Issue deprecation warning on import
warnings.warn(
    "dipeo_container is deprecated. Please use dipeo.container instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.container import Container, init_resources, shutdown_resources
from dipeo.container.providers import create_provider_overrides

__all__ = [
    "Container",
    "create_provider_overrides",
    "init_resources",
    "shutdown_resources",
]
__version__ = "0.1.0"
