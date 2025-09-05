"""Messaging adapter module."""

from .message_router import MessageRouter, message_router
from .null_event_bus import NullEventBus

__all__ = [
    "MessageRouter",
    "NullEventBus",
    "message_router",
]
