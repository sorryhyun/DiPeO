"""DiPeO Dependency Injection Container.

This module is transitioning from a complex 6-container system to a simplified
3-container architecture. During migration, both systems are available.
"""

import os

# Control which container system to use
USE_SIMPLE_CONTAINERS = os.environ.get("DIPEO_USE_SIMPLE_CONTAINERS", "false").lower() == "true"

if USE_SIMPLE_CONTAINERS:
    # Use new simplified 3-container system
    from .containers import (
        Container,
        init_resources,
        shutdown_resources,
    )
    # Simple containers don't have validate_protocol_compliance yet
    def validate_protocol_compliance(*args, **kwargs):
        pass
else:
    # Use legacy 6-container system
    from .container import (
        Container,
        init_resources,
        shutdown_resources,
        validate_protocol_compliance,
    )

__all__ = [
    "Container",
    "init_resources",
    "shutdown_resources",
    "validate_protocol_compliance",
]