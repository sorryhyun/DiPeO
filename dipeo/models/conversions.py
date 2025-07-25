"""
Auto-generated 2025-07-25T23:10:17.306230. Do NOT edit by hand.
Source of truth: `conversions.ts`
"""

from typing import Dict, Any, TypedDict
from .models import (
    NodeType,
    HandleDirection,
    NodeID,
    HandleID,
)

# ---------------------------------------------------------------------------

NODE_TYPE_MAP: Dict[str, NodeType] = {
    "code_job": NodeType.code_job,
    "api_job": NodeType.api_job,
    "person_job": NodeType.person_job,
    "person_batch_job": NodeType.person_batch_job,
    "condition": NodeType.condition,
    "user_response": NodeType.user_response,
    "start": NodeType.start,
    "endpoint": NodeType.endpoint,
    "db": NodeType.db,
    "notion": NodeType.notion,
    "hook": NodeType.hook,
    "template_job": NodeType.template_job,
    "json_schema_validator": NodeType.json_schema_validator,
    "typescript_ast": NodeType.typescript_ast,
    "sub_diagram": NodeType.sub_diagram,
}

NODE_TYPE_REVERSE_MAP: Dict[NodeType, str] = {v: k for k, v in NODE_TYPE_MAP.items()}

def node_kind_to_domain_type(kind: str) -> NodeType:
    try:
        return NODE_TYPE_MAP[kind]
    except KeyError as exc:
        raise ValueError(f"Unknown node kind: {kind}") from exc


def domain_type_to_node_kind(node_type: NodeType) -> str:
    try:
        return NODE_TYPE_REVERSE_MAP[node_type]
    except KeyError as exc:
        raise ValueError(f"Unknown node type: {node_type}") from exc


# ---------------------------------------------------------------------------
# Handle helpers – kept trivial and logic-aligned with TypeScript.
# ---------------------------------------------------------------------------

def normalize_node_id(node_id: str) -> NodeID:  # noqa: D401
    """Return the node ID unchanged (placeholder for future logic)."""
    return node_id  # type: ignore[return-value]


def create_handle_id(
    node_id: NodeID,
    handle_label: str,
    direction: HandleDirection,
) -> HandleID:
    """Compose a handle ID the same way the frontend expects it."""
    return f"{node_id}_{handle_label}_{direction.value}"  # type: ignore[return-value]


class ParsedHandle(TypedDict):
    node_id: NodeID
    handle_label: str
    direction: HandleDirection


def parse_handle_id(handle_id: HandleID) -> ParsedHandle:
    parts = handle_id.split("_")
    if len(parts) != 3:
        raise ValueError(f"Invalid handle ID: {handle_id}")
    node_id, label, dir_str = parts
    try:
        direction = HandleDirection[dir_str.upper()]
    except KeyError as exc:
        raise ValueError(f"Unknown handle direction: {dir_str}") from exc
    return {"node_id": node_id, "handle_label": label, "direction": direction}  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Data Structure Conversions
# ---------------------------------------------------------------------------

def diagram_arrays_to_maps(diagram: Dict[str, Any]) -> Dict[str, Any]:
    """Convert array-based diagram to map-based structure."""
    return {
        "nodes": {n["id"]: n for n in diagram.get("nodes", [])},
        "arrows": {a["id"]: a for a in diagram.get("arrows", [])},
        "handles": {h["id"]: h for h in diagram.get("handles", [])},
        "persons": {p["id"]: p for p in diagram.get("persons", [])}
    }


def diagram_maps_to_arrays(
    nodes: Dict[str, Any] = None,
    arrows: Dict[str, Any] = None,
    handles: Dict[str, Any] = None,
    persons: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convert map-based diagram to array-based structure."""
    # Handle both calling styles for backward compatibility
    if nodes is None and len(kwargs) == 1 and 'diagram' in kwargs:
        # Called with single diagram dict
        diagram = kwargs['diagram']
        return {
            "nodes": list(diagram.get("nodes", {}).values()),
            "arrows": list(diagram.get("arrows", {}).values()),
            "handles": list(diagram.get("handles", {}).values()),
            "persons": list(diagram.get("persons", {}).values())
        }
    else:
        # Called with individual components (current usage)
        return {
            "nodes": list((nodes or {}).values()),
            "arrows": list((arrows or {}).values()),
            "handles": list((handles or {}).values()),
            "persons": list((persons or {}).values())
        }


__all__ = [
    "NODE_TYPE_MAP",
    "NODE_TYPE_REVERSE_MAP",
    "node_kind_to_domain_type",
    "domain_type_to_node_kind",
    "normalize_node_id",
    "create_handle_id",
    "parse_handle_id",
    "diagram_arrays_to_maps",
    "diagram_maps_to_arrays",
]