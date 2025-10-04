"""Helper functions for the execution engine."""

from typing import Any


def extract_llm_usage(output: Any) -> dict | None:
    """Extract LLM usage information from output envelope.

    Args:
        output: Output envelope that may contain LLM usage metadata

    Returns:
        Dictionary with LLM usage information, or None if not present
    """
    if hasattr(output, "meta") and isinstance(output.meta, dict):
        llm_usage = output.meta.get("llm_usage")
        if llm_usage:
            if hasattr(llm_usage, "model_dump"):
                return llm_usage.model_dump()
            elif isinstance(llm_usage, dict):
                return llm_usage
    return None


def format_node_result(envelope: Any) -> dict[str, Any]:
    """Format node execution result for output.

    Args:
        envelope: Output envelope from node execution

    Returns:
        Dictionary representation of the result
    """
    if hasattr(envelope, "body"):
        body = envelope.body
        if hasattr(body, "dict"):
            return body.dict()
        elif hasattr(body, "model_dump"):
            return body.model_dump()
        elif isinstance(body, dict):
            return body
        else:
            return {"value": str(body)}
    elif hasattr(envelope, "to_dict"):
        return envelope.to_dict()
    elif hasattr(envelope, "value"):
        result = {"value": envelope.value}
        if hasattr(envelope, "metadata") and envelope.metadata:
            result["metadata"] = envelope.metadata
        return result
    else:
        return {"value": envelope}


def get_handler(service_registry, node_type: str):
    """Get handler for a specific node type.

    Args:
        service_registry: Service registry instance
        node_type: Type of node to get handler for

    Returns:
        Handler instance for the node type
    """
    from dipeo.application import get_global_registry
    from dipeo.application.execution.handlers.core.factory import HandlerFactory

    registry = get_global_registry()
    if not hasattr(registry, "_service_registry") or registry._service_registry is None:
        HandlerFactory(service_registry)

    if hasattr(node_type, "value"):
        node_type = node_type.value

    return registry.create_handler(node_type)
