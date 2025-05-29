"""Centralized node type mapping and utilities."""

from enum import Enum
from typing import Dict, Set
from ..constants import NodeType


class NodeTypeMapping:
    """Centralized node type mapping between legacy strings and modern enums."""
    
    # Legacy string names to enum mapping
    LEGACY_TO_ENUM: Dict[str, NodeType] = {
        'startNode': NodeType.START,
        'personjobNode': NodeType.PERSON_JOB,
        'conditionNode': NodeType.CONDITION,
        'dbNode': NodeType.DB,
        'jobNode': NodeType.JOB,
        'endpointNode': NodeType.ENDPOINT,
    }
    
    # Reverse mapping for convenience
    ENUM_TO_LEGACY: Dict[NodeType, str] = {v: k for k, v in LEGACY_TO_ENUM.items()}
    
    # Node types that require LLM service
    LLM_DEPENDENT_TYPES: Set[NodeType] = {
        NodeType.PERSON_JOB,
        NodeType.JOB
    }
    
    # Node types that can have iteration limits
    ITERATABLE_TYPES: Set[NodeType] = {
        NodeType.PERSON_JOB,
        NodeType.CONDITION,
        NodeType.JOB
    }
    
    # Node types that produce no output
    NO_OUTPUT_TYPES: Set[NodeType] = {
        NodeType.START
    }
    
    @classmethod
    def normalize(cls, node_type: str) -> NodeType:
        """Convert any node type string to enum.
        
        Args:
            node_type: Node type string (legacy or modern)
            
        Returns:
            NodeType enum value
            
        Raises:
            ValueError: If node type is not recognized
        """
        # First try direct enum lookup
        try:
            return NodeType(node_type)
        except ValueError:
            pass
        
        # Try legacy mapping
        if node_type in cls.LEGACY_TO_ENUM:
            return cls.LEGACY_TO_ENUM[node_type]
        
        # Fallback: use the existing from_legacy method
        return NodeType.from_legacy(node_type)
    
    @classmethod
    def to_legacy(cls, node_type: NodeType) -> str:
        """Convert enum to legacy string format.
        
        Args:
            node_type: NodeType enum
            
        Returns:
            Legacy string representation
        """
        return cls.ENUM_TO_LEGACY.get(node_type, node_type.value)
    
    @classmethod
    def requires_llm(cls, node_type: NodeType) -> bool:
        """Check if node type requires LLM service.
        
        Args:
            node_type: NodeType to check
            
        Returns:
            True if node requires LLM service
        """
        return node_type in cls.LLM_DEPENDENT_TYPES
    
    @classmethod
    def supports_iterations(cls, node_type: NodeType) -> bool:
        """Check if node type supports iteration limits.
        
        Args:
            node_type: NodeType to check
            
        Returns:
            True if node supports iteration limits
        """
        return node_type in cls.ITERATABLE_TYPES
    
    @classmethod
    def produces_output(cls, node_type: NodeType) -> bool:
        """Check if node type produces output.
        
        Args:
            node_type: NodeType to check
            
        Returns:
            True if node produces output
        """
        return node_type not in cls.NO_OUTPUT_TYPES
    
    @classmethod
    def get_all_legacy_names(cls) -> list:
        """Get all supported legacy node type names."""
        return list(cls.LEGACY_TO_ENUM.keys())
    
    @classmethod
    def get_all_enum_values(cls) -> list:
        """Get all NodeType enum values."""
        return list(NodeType)