"""Judge-specific utility functions for preparing context from conversations."""

from typing import Any, Dict


def prepare_judge_context(inputs: Dict[str, Any], diagram: Any) -> str:
    """Prepare context for judge nodes from conversation inputs."""
    if "conversation" not in inputs:
        return ""

    conversations = inputs["conversation"]
    if not isinstance(conversations, list):
        return ""

    # Group by person and format
    context_parts = ["Here are the arguments from different panels:\n"]

    # Simple formatting - just extract the last few messages
    for msg in conversations[-10:]:  # Last 10 messages
        if msg.get("role") == "assistant":
            person_id = msg.get("personId", "Unknown")
            content = msg.get("content", "")
            context_parts.append(f"\n{person_id}: {content}\n")

    return "".join(context_parts)
