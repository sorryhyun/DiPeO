"""Centralized node type utilities."""

from typing import Set
from ..constants import NodeType


class NodeTypeMapping:
    """Centralized node type utilities and categorization."""
    
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
    def get_all_enum_values(cls) -> list:
        """Get all NodeType enum values."""
        return list(NodeType)