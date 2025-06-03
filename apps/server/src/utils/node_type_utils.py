"""
Node type normalization utilities for consistent type handling between frontend and backend.
"""

from typing import Dict, Optional

# Mapping from frontend node types (with "Node" suffix) to backend node types
FRONTEND_TO_BACKEND_TYPE_MAP: Dict[str, str] = {
    "startNode": "start",
    "personJobNode": "person_job",
    "personBatchJobNode": "person_batch_job", 
    "conditionNode": "condition",
    "dbNode": "db",
    "jobNode": "job",
    "endpointNode": "endpoint"
}

# Reverse mapping for backend to frontend
BACKEND_TO_FRONTEND_TYPE_MAP: Dict[str, str] = {
    v: k for k, v in FRONTEND_TO_BACKEND_TYPE_MAP.items()
}

# Additional aliases for flexibility
TYPE_ALIASES: Dict[str, str] = {
    "personjob": "person_job",
    "personbatchjob": "person_batch_job",
    "personJob": "person_job",
    "personBatchJob": "person_batch_job"
}


def normalize_node_type_to_backend(node_type: str) -> str:
    """
    Normalize a node type string to the backend convention.
    
    Args:
        node_type: The node type string (could be frontend or backend format)
        
    Returns:
        The normalized backend node type string
    """
    # First check if it's already a backend type
    if node_type in BACKEND_TO_FRONTEND_TYPE_MAP:
        return node_type
    
    # Check if it's a frontend type
    if node_type in FRONTEND_TO_BACKEND_TYPE_MAP:
        return FRONTEND_TO_BACKEND_TYPE_MAP[node_type]
    
    # Check aliases
    if node_type in TYPE_ALIASES:
        return TYPE_ALIASES[node_type]
    
    # Return as-is if not recognized (for backward compatibility)
    return node_type


def normalize_node_type_to_frontend(node_type: str) -> str:
    """
    Normalize a node type string to the frontend convention.
    
    Args:
        node_type: The node type string (could be frontend or backend format)
        
    Returns:
        The normalized frontend node type string
    """
    # First check if it's already a frontend type
    if node_type in FRONTEND_TO_BACKEND_TYPE_MAP:
        return node_type
    
    # Check if it's a backend type
    if node_type in BACKEND_TO_FRONTEND_TYPE_MAP:
        return BACKEND_TO_FRONTEND_TYPE_MAP[node_type]
    
    # Check aliases and convert to frontend
    if node_type in TYPE_ALIASES:
        backend_type = TYPE_ALIASES[node_type]
        if backend_type in BACKEND_TO_FRONTEND_TYPE_MAP:
            return BACKEND_TO_FRONTEND_TYPE_MAP[backend_type]
    
    # Return as-is if not recognized (for backward compatibility)
    return node_type


def is_start_node(node_type: str) -> bool:
    """Check if a node type represents a start node."""
    normalized = normalize_node_type_to_backend(node_type)
    return normalized == "start"


def get_supported_backend_types() -> list[str]:
    """Get list of all supported backend node types."""
    return list(BACKEND_TO_FRONTEND_TYPE_MAP.keys())


def get_supported_frontend_types() -> list[str]:
    """Get list of all supported frontend node types."""
    return list(FRONTEND_TO_BACKEND_TYPE_MAP.keys())