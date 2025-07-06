"""Shared utility for conversation detection logic."""

from typing import Any, Dict, List


def is_conversation(value: Any) -> bool:
    """Check if value is a conversation (list of messages with role and content).
    
    A conversation is defined as a list of dictionaries where each dictionary
    contains both 'role' and 'content' keys.
    
    Args:
        value: The value to check
        
    Returns:
        True if value is a valid conversation format
    """
    return (isinstance(value, list) and 
            value and 
            all(isinstance(item, dict) and 
                "role" in item and 
                "content" in item for item in value))


def has_nested_conversation(inputs: Dict[str, Any]) -> bool:
    """Check if inputs contain a nested conversation in default key.
    
    Args:
        inputs: Dictionary of inputs to check
        
    Returns:
        True if inputs contain a nested conversation
    """
    return (isinstance(inputs, dict) and 
            "default" in inputs and 
            is_conversation(inputs.get("default")))


def contains_conversation(inputs: Dict[str, Any]) -> bool:
    """Check if any value in inputs is a conversation.
    
    Args:
        inputs: Dictionary of inputs to check
        
    Returns:
        True if any value is a conversation
    """
    if not isinstance(inputs, dict):
        return False
        
    for value in inputs.values():
        if is_conversation(value):
            return True
    
    return False