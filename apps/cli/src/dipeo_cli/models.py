from typing import Any

# Re-export all models directly from generated code
from dipeo_domain import (
    DomainDiagram,
    LLMService,
    # Enums
    NodeType,
)

# Utility functions for working with generated models


def diagram_to_dict(diagram: DomainDiagram) -> dict[str, Any]:
    """Convert a diagram to dictionary for JSON serialization.

    Uses Pydantic's model_dump() method.
    """
    # Convert to dict using Pydantic's method
    return diagram.model_dump(by_alias=True)


def diagram_dict_to_backend(diagram_dict: dict[str, Any]) -> dict[str, Any]:
    """Convert diagram dict from array format to backend format (dict of dicts)."""
    backend_dict = {
        "nodes": {},
        "arrows": {},
        "handles": {},
        "persons": {},
        "api_keys": {},
        "metadata": None,
    }

    if "nodes" in diagram_dict:
        for node in diagram_dict["nodes"]:
            backend_dict["nodes"][node["id"]] = node

    if "arrows" in diagram_dict:
        for arrow in diagram_dict["arrows"]:
            backend_dict["arrows"][arrow["id"]] = arrow

    if "handles" in diagram_dict:
        for handle in diagram_dict["handles"]:
            backend_dict["handles"][handle["id"]] = handle

    if "persons" in diagram_dict:
        for person in diagram_dict["persons"]:
            backend_dict["persons"][person["id"]] = person

    if "apiKeys" in diagram_dict:
        for api_key in diagram_dict["apiKeys"]:
            backend_dict["api_keys"][api_key["id"]] = api_key
    elif "api_keys" in diagram_dict:
        for api_key in diagram_dict["api_keys"]:
            backend_dict["api_keys"][api_key["id"]] = api_key

    if "metadata" in diagram_dict:
        backend_dict["metadata"] = diagram_dict["metadata"]

    return backend_dict


def backend_to_diagram_dict(backend_dict: dict[str, Any]) -> dict[str, Any]:
    return {
        "nodes": list(backend_dict.get("nodes", {}).values()),
        "arrows": list(backend_dict.get("arrows", {}).values()),
        "handles": list(backend_dict.get("handles", {}).values()),
        "persons": list(backend_dict.get("persons", {}).values()),
        "apiKeys": list(backend_dict.get("api_keys", {}).values()),
        "metadata": backend_dict.get("metadata"),
    }


# Validation helpers
def validate_node_type(node_type: str) -> bool:
    try:
        NodeType(node_type)
        return True
    except ValueError:
        return False


def validate_llm_service(service: str) -> bool:
    try:
        LLMService(service)
        return True
    except ValueError:
        return False
