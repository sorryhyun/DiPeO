"""Utility functions for DiPeO Core."""

# Export conversation detection utilities
from .conversation_detection import (
    contains_conversation,
    has_nested_conversation,
    is_conversation,
)

__all__ = [
    # Conversation detection utilities
    "is_conversation",
    "has_nested_conversation",
    "contains_conversation",
]