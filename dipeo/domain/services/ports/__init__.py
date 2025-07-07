"""Domain ports for infrastructure dependencies."""

from .file_storage import FileStoragePort
from .messaging import MessageRouterPort
from .state_store import StateStorePort

# Type alias for backward compatibility
StateStore = StateStorePort

__all__ = [
    "FileStoragePort",
    "MessageRouterPort",
    "StateStorePort",
    "StateStore",
]
