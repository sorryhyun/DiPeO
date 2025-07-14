"""
Auto-generated conversions. Do NOT edit by hand.
Source of truth: `conversions.ts`
"""

from typing import TypedDict

from .models import (
    HandleDirection,
    HandleID,
    NodeID,
    NodeType,
)

# ---------------------------------------------------------------------------

NODE_TYPE_MAP: dict[str, NodeType] = {
    "job": NodeType.job,
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
}

NODE_TYPE_REVERSE_MAP: dict[NodeType, str] = {v: k for k, v in NODE_TYPE_MAP.items()}

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

def normalize_node_id(node_id: str) -> NodeID:
    """Return the node ID unchanged (placeholder for future logic)."""
    return node_id  # type: ignore[return-value]


def create_handle_id(
    node_id: NodeID,
    handle_label: str,
    direction: HandleDirection,
) -> HandleID:
    """Compose a handle ID the same way the frontend expects it."""
    return f"handle:{node_id}:{handle_label}:{direction.name.lower()}"  # type: ignore[return-value]


class ParsedHandle(TypedDict):
    node_id: NodeID
    handle_label: str
    direction: HandleDirection


def parse_handle_id(handle_id: HandleID) -> ParsedHandle:
    parts = handle_id.split("_")
    if len(parts) != 4 or parts[0] != "handle":
        raise ValueError(f"Invalid handle ID: {handle_id}")
    _, node_id, label, dir_str = parts
    try:
        direction = HandleDirection[dir_str.upper()]
    except KeyError as exc:
        raise ValueError(f"Unknown handle direction: {dir_str}") from exc
    return {"node_id": node_id, "handle_label": label, "direction": direction}  # type: ignore[return-value]


# Array/Map conversion utilities
def diagram_arrays_to_maps(
    nodes: list = None,
    arrows: list = None, 
    handles: list = None,
    persons: list = None,
    api_keys: list = None
) -> dict[str, dict]:
    """Convert diagram arrays to map format."""
    return {
        "nodes": {n.id if hasattr(n, 'id') else n['id']: n for n in (nodes or [])},
        "arrows": {a.id if hasattr(a, 'id') else a['id']: a for a in (arrows or [])},
        "handles": {h.id if hasattr(h, 'id') else h['id']: h for h in (handles or [])},
        "persons": {p.id if hasattr(p, 'id') else p['id']: p for p in (persons or [])}
    }


def diagram_maps_to_arrays(
    nodes: dict = None,
    arrows: dict = None,
    handles: dict = None,
    persons: dict = None,
    api_keys: dict = None
) -> dict[str, list]:
    """Convert diagram maps to array format."""
    return {
        "nodes": list((nodes or {}).values()),
        "arrows": list((arrows or {}).values()),
        "handles": list((handles or {}).values()),
        "persons": list((persons or {}).values())
    }


__all__ = [
    "NODE_TYPE_MAP",
    "NODE_TYPE_REVERSE_MAP",
    "create_handle_id",
    "diagram_arrays_to_maps",
    "diagram_maps_to_arrays",
    "domain_type_to_node_kind",
    "node_kind_to_domain_type",
    "normalize_node_id",
    "parse_handle_id",
]