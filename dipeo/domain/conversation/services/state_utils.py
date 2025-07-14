# Utilities for managing conversation state and forgetting logic

from typing import Any, Dict, List, Optional
from dipeo.models import ForgettingMode


def should_forget_messages(
    execution_count: int,
    forget_mode: ForgettingMode,
) -> bool:
    # Determine if messages should be forgotten based on mode and execution count
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
    # Apply forgetting strategy to messages
    if forget_mode == ForgettingMode.no_forget:
        return messages
    
    # For on_every_turn and other modes, keep system messages and last user message
    system_messages = [m for m in messages if m.get("role") == "system"]
    user_messages = [m for m in messages if m.get("role") == "user"]
    
    if user_messages:
        return system_messages + [user_messages[-1]]
    return system_messages




