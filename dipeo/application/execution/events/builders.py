"""Event building and enrichment utilities."""

from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import NodeState, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode

if TYPE_CHECKING:
    from dipeo.domain.execution.messaging.envelope import Envelope
    from dipeo.domain.execution.state.state_tracker import StateTracker


def get_node_state(
    node: ExecutableNode,
    status: Status,
    exec_count: int = 0,
    state_tracker: "StateTracker | None" = None,
) -> NodeState:
    """Get or create node state for event emission.

    Args:
        node: The node to get state for
        status: The current status
        exec_count: Execution count for the node
        state_tracker: Optional state tracker to query existing state

    Returns:
        NodeState instance
    """
    if state_tracker:
        node_state = state_tracker.get_node_state(node.id)
        if node_state:
            return node_state

    return NodeState(
        node_id=str(node.id),
        status=status,
        execution_count=exec_count,
    )


def create_output_summary(output: Any) -> str | None:
    """Create a concise summary of output for logging and events.

    Args:
        output: The output data to summarize

    Returns:
        Human-readable summary string, or None if output is None
    """
    if output is None:
        return None

    if isinstance(output, str):
        return output[:100] + "..." if len(output) > 100 else output
    elif isinstance(output, dict):
        return f"Object with {len(output)} keys"
    elif isinstance(output, list):
        return f"Array with {len(output)} items"
    else:
        return str(type(output).__name__)


def extract_token_usage(envelope: "Envelope | None") -> dict | None:
    """Extract token usage information from envelope metadata.

    Args:
        envelope: The envelope to extract from

    Returns:
        Token usage dictionary, or None if not available
    """
    if not envelope or not hasattr(envelope, "meta") or not isinstance(envelope.meta, dict):
        return None

    llm_usage = envelope.meta.get("llm_usage") or envelope.meta.get("token_usage")
    if not llm_usage:
        return None

    if hasattr(llm_usage, "model_dump"):
        return llm_usage.model_dump()
    elif isinstance(llm_usage, dict):
        return llm_usage

    return None


def extract_envelope_metadata(envelope: "Envelope | None") -> dict[str, Any]:
    """Extract relevant metadata from envelope for event enrichment.

    Args:
        envelope: The envelope to extract metadata from

    Returns:
        Dictionary with person_id, model, and memory_selection if available
    """
    result = {}

    if envelope and hasattr(envelope, "meta") and isinstance(envelope.meta, dict):
        for key in ("person_id", "model", "memory_selection"):
            if key in envelope.meta:
                result[key] = envelope.meta[key]

    return result
