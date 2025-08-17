"""Shared utility for conversation detection logic."""

from typing import Any


def is_conversation(value: Any) -> bool:
    """Check if value is a conversation - list of dicts with 'role' and 'content' keys."""
    return (isinstance(value, list) and 
            value and 
            all(isinstance(item, dict) and 
                "role" in item and 
                "content" in item for item in value))


def has_nested_conversation(inputs: dict[str, Any]) -> bool:
    return (isinstance(inputs, dict) and 
            "default" in inputs and 
            is_conversation(inputs.get("default")))


def contains_conversation(inputs: dict[str, Any]) -> bool:
    if not isinstance(inputs, dict):
        return False
        
    for value in inputs.values():
        if is_conversation(value):
            return True
    
    return False