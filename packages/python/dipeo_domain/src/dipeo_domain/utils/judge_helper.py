"""Judge-specific utility functions for preparing context from conversations."""

from typing import Any, Dict


def prepare_judge_context(inputs: Dict[str, Any], diagram: Any) -> str:
    """Prepare context for judge nodes from conversation inputs."""
    # Handle nested conversation data from condition nodes
    conversations = None
    
    # First check for direct conversation key
    if "conversation" in inputs:
        conversations = inputs["conversation"]
    # Then check for conversation data nested under 'default' (from condition nodes)
    elif "default" in inputs and isinstance(inputs["default"], dict):
        if "default" in inputs["default"] and isinstance(inputs["default"]["default"], list):
            # Check if this looks like conversation data
            potential_conv = inputs["default"]["default"]
            if potential_conv and isinstance(potential_conv[0], dict) and "role" in potential_conv[0]:
                conversations = potential_conv
    
    if not conversations or not isinstance(conversations, list):
        return ""

    # Group by person and format
    context_parts = ["Here are the arguments from different panels:\n"]

    # Simple formatting - just extract the last few messages
    for msg in conversations[-10:]:  # Last 10 messages
        if msg.get("role") == "assistant":
            # Fix: Use 'person_id' instead of 'personId' to match person_job handler output
            person_id = msg.get("person_id", "Unknown")
            content = msg.get("content", "")
            context_parts.append(f"\n{person_id}: {content}\n")

    return "".join(context_parts)
