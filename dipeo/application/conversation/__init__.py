"""Conversation bounded context in application layer.

This module handles:
- Person management
- Conversation state management
- Memory management for conversations
"""

from .wiring import wire_conversation

__all__ = ["wire_conversation"]
