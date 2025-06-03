"""
Node type normalization utilities for consistent type handling.
"""

from typing import Dict, Optional

# Since we now use snake_case everywhere, no conversion is needed.
# Keep minimal aliases for backward compatibility during transition
TYPE_ALIASES: Dict[str, str] = {
    # Legacy camelCase+Node suffix support (temporary)
    "startNode": "start",
    "personJobNode": "person_job",
    "personBatchJobNode": "person_batch_job", 
    "conditionNode": "condition",
    "dbNode": "db",
    "jobNode": "job",
    "endpointNode": "endpoint",
    # Other common aliases
    "personjob": "person_job",
    "personbatchjob": "person_batch_job",
    "personJob": "person_job",
    "personBatchJob": "person_batch_job"
}


def normalize_node_type_to_backend(node_type: str) -> str:
    """
    Normalize a node type string to the backend convention (snake_case).
    
    Args:
        node_type: The node type string
        
    Returns:
        The normalized backend node type string
    """
    # Check aliases for backward compatibility
    if node_type in TYPE_ALIASES:
        return TYPE_ALIASES[node_type]
    
    # Return as-is (already snake_case or unknown type)
    return node_type


def normalize_node_type_to_frontend(node_type: str) -> str:
    """
    Normalize a node type string to the frontend convention.
    Since we now use snake_case everywhere, this is the same as backend normalization.
    
    Args:
        node_type: The node type string
        
    Returns:
        The normalized frontend node type string (snake_case)
    """
    # Same as backend normalization now
    return normalize_node_type_to_backend(node_type)


def is_start_node(node_type: str) -> bool:
    """Check if a node type represents a start node."""
    normalized = normalize_node_type_to_backend(node_type)
    return normalized == "start"


def get_supported_backend_types() -> list[str]:
    """Get list of all supported backend node types."""
    # Return the standard snake_case types
    return ["start", "person_job", "person_batch_job", "condition", "db", "job", "endpoint"]


def get_supported_frontend_types() -> list[str]:
    """Get list of all supported frontend node types."""
    # Same as backend types now that we use snake_case everywhere
    return get_supported_backend_types()


def extract_node_type(node: dict) -> str:
    """
    Extract node type from various possible locations.
    Priority: data.type > properties.type > type
    
    Args:
        node: The node dictionary
        
    Returns:
        The normalized backend node type string
        
    Raises:
        ValueError: If no type found in node
    """
    # Try data.type first (frontend logical type)
    data = node.get("data")
    if data and isinstance(data, dict):
        data_type = data.get("type")
        if data_type:
            return normalize_node_type_to_backend(data_type)
    
    # Try properties.type (backend receives this)
    properties = node.get("properties")
    if properties and isinstance(properties, dict):
        prop_type = properties.get("type")
        if prop_type:
            return normalize_node_type_to_backend(prop_type)
    
    # Fallback to top-level type
    top_type = node.get("type")
    if top_type:
        return normalize_node_type_to_backend(top_type)
    
    raise ValueError(f"No type found in node: {node.get('id', 'unknown')}")