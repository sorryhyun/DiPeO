"""Utilities for managing conversation state and forgetting logic."""

from typing import Any, Dict, List, Optional
from dipeo.models import ForgettingMode


def should_forget_messages(
    execution_count: int,
    forget_mode: ForgettingMode,
) -> bool:
    """Determine if messages should be forgotten based on mode and execution count.
    
    Args:
        execution_count: Current execution count (0-based)
        forget_mode: The forgetting mode to apply
        
    Returns:
        True if messages should be forgotten
    """
    if forget_mode == ForgettingMode.no_forget:
        return False
    elif forget_mode == ForgettingMode.on_every_turn:
        return execution_count > 0
    elif forget_mode == ForgettingMode.upon_request:
        # This would be handled by explicit user request
        return False
    return False


def apply_forgetting_strategy(
    messages: List[Dict[str, Any]],
    forget_mode: ForgettingMode,
) -> List[Dict[str, Any]]:
    """Apply forgetting strategy to messages.
    
    Args:
        messages: List of message dictionaries
        forget_mode: The forgetting mode to apply
        
    Returns:
        Filtered messages based on forgetting strategy
    """
    if forget_mode == ForgettingMode.no_forget:
        return messages
    
    # For on_every_turn and other modes, keep system messages and last user message
    system_messages = [m for m in messages if m.get("role") == "system"]
    user_messages = [m for m in messages if m.get("role") == "user"]
    
    if user_messages:
        return system_messages + [user_messages[-1]]
    return system_messages


def extract_conversation_messages(
    inputs: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Extract conversation messages from inputs.
    
    Args:
        inputs: Input dictionary that may contain conversation states
        
    Returns:
        List of message dictionaries
    """
    messages = []
    
    for value in inputs.values():
        if isinstance(value, dict) and "messages" in value:
            for msg in value["messages"]:
                if isinstance(msg, dict):
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                        "tool_calls": msg.get("tool_calls"),
                        "tool_call_id": msg.get("tool_call_id"),
                    })
    
    return messages


def has_conversation_input(
    inputs: Dict[str, Any],
) -> bool:
    """Check if inputs contain conversation state.
    
    Args:
        inputs: Input dictionary to check
        
    Returns:
        True if conversation state is present
    """
    for value in inputs.values():
        if _is_conversation_state(value):
            return True
    return False


def _is_conversation_state(value: Any) -> bool:
    """Check if a value represents a conversation state."""
    if not isinstance(value, dict):
        return False
        
    # Check for conversation state structure
    if "messages" in value and isinstance(value.get("messages"), list):
        return True
        
    # Check for single message structure
    if "role" in value and "content" in value:
        return True
        
    return False


def consolidate_conversation_messages(
    inputs: Dict[str, Any],
    person_labels: Dict[str, str],
) -> str:
    """Consolidate conversation messages for on_every_turn mode.
    
    Args:
        inputs: Input dictionary containing conversation states
        person_labels: Mapping of input keys to person labels
        
    Returns:
        Consolidated message string
    """
    consolidated = []
    
    for key, value in inputs.items():
        if _is_conversation_state(value):
            person_label = person_labels.get(key)
            messages = _format_conversation_messages(value, person_label)
            consolidated.extend(messages)
    
    # Process external messages if present
    if "external_messages" in inputs:
        external = inputs["external_messages"]
        if isinstance(external, list):
            for msg in external:
                if isinstance(msg, dict) and "content" in msg:
                    formatted_msg = _format_external_message(msg)
                    consolidated.append(formatted_msg)
    
    return "\n\n".join(consolidated)


def _format_conversation_messages(
    conversation: Dict[str, Any],
    person_label: Optional[str],
) -> List[str]:
    """Format conversation messages for display."""
    formatted = []
    
    messages = conversation.get("messages", [])
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "")
            role = msg.get("role", "")
            
            if person_label:
                formatted.append(f"[{person_label} - {role}]: {content}")
            else:
                formatted.append(f"[{role}]: {content}")
    
    return formatted


def _format_external_message(msg: Dict[str, Any]) -> str:
    """Format an external message."""
    content = msg.get("content", "")
    role = msg.get("role", "user")
    return f"[{role}]: {content}"


# Re-export class for backward compatibility
class ConversationStateManager:
    """Legacy class wrapper for state management functions.
    
    This class is maintained for backward compatibility.
    New code should use the module functions directly.
    """
    
    def should_forget_messages(self, execution_count: int, forget_mode: ForgettingMode) -> bool:
        return should_forget_messages(execution_count, forget_mode)
    
    def apply_forgetting_strategy(self, messages: List[Dict[str, Any]], forget_mode: ForgettingMode) -> List[Dict[str, Any]]:
        return apply_forgetting_strategy(messages, forget_mode)
    
    def extract_conversation_messages(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        return extract_conversation_messages(inputs)
    
    def has_conversation_input(self, inputs: Dict[str, Any]) -> bool:
        return has_conversation_input(inputs)
    
    def consolidate_conversation_messages(self, inputs: Dict[str, Any], person_labels: Dict[str, str]) -> str:
        return consolidate_conversation_messages(inputs, person_labels)