"""Legacy event infrastructure - DEPRECATED.

This module is deprecated and will be removed in a future version.
Please use dipeo.infrastructure.adapters.events instead.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "dipeo.infrastructure.events is deprecated. "
    "Please use dipeo.infrastructure.adapters.events instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.infrastructure.adapters.events.legacy import (
    AsyncEventBus,
    NullEventBus,
    ObserverToEventConsumerAdapter,
    create_event_bus_with_observers,
)

__all__ = [
    "AsyncEventBus",
    "NullEventBus",
    "ObserverToEventConsumerAdapter",
    "create_event_bus_with_observers",
]