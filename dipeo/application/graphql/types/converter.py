"""
Strawberry type converter for DiPeO application layer.

This module provides a bridge between the application layer's Pydantic domain models
and the generated Strawberry GraphQL types. It ensures proper type resolution
for GraphQL schema creation.
"""

from typing import Dict, Type, Any, NewType
from functools import lru_cache

import strawberry
from strawberry.scalars import JSON as JSONScalar

# Import the Pydantic models we need to wrap
from dipeo.diagram_generated.domain_models import (
    DomainDiagram,
    DomainNode,
    DomainHandle,
    DomainArrow,
    DomainPerson,
    DomainApiKey,
    ExecutionState,
    NodeState,
    TokenUsage,
    DiagramMetadata,
    PersonLLMConfig,
    MemorySettings,
    # Import ID types
    NodeID,
    HandleID,
    ArrowID,
    PersonID,
    ApiKeyID,
    DiagramID,
    ExecutionID,
    HookID,
    TaskID,
)


class StrawberryTypeRegistry:
    """Registry for mapping Pydantic models to Strawberry types."""
    
    def __init__(self):
        self._type_map: Dict[Type, Type] = {}
        self._initialize_type_map()
    
    def _initialize_type_map(self):
        """Initialize the mapping of Pydantic models to Strawberry types."""
        if STRAWBERRY_TYPES_AVAILABLE:
            # Use generated types when available
            from dipeo.diagram_generated.domain_models import (
                DomainDiagram,
                DomainNode,
                DomainHandle,
                DomainArrow,
                DomainPerson,
                DomainApiKey,
                ExecutionState,
                NodeState,
                TokenUsage,
                DiagramMetadata,
                PersonLLMConfig,
                MemorySettings,
            )
            
            self._type_map = {
                DomainDiagram: DomainDiagramType,
                DomainNode: DomainNodeType,
                DomainHandle: DomainHandleType,
                DomainArrow: DomainArrowType,
                DomainPerson: DomainPersonType,
                DomainApiKey: DomainApiKeyType,
                ExecutionState: ExecutionStateType,
                NodeState: NodeStateType,
                TokenUsage: TokenUsageType,
                DiagramMetadata: DiagramMetadataType,
                PersonLLMConfig: PersonLLMConfigType,
                MemorySettings: MemorySettingsType,
            }
        else:
            # Create minimal wrappers as fallback
            self._create_fallback_types()
    
    def _create_fallback_types(self):
        """Create minimal Strawberry type wrappers when generated types aren't available."""
        # This is a temporary solution until full migration
        @strawberry.experimental.pydantic.type(DomainDiagram, all_fields=True)
        class DomainDiagramTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(DomainNode, all_fields=True)
        class DomainNodeTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(DomainHandle, all_fields=True)
        class DomainHandleTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(DomainArrow, all_fields=True)
        class DomainArrowTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(DomainPerson, all_fields=True)
        class DomainPersonTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(DomainApiKey, all_fields=True)
        class DomainApiKeyTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(ExecutionState, all_fields=True)
        class ExecutionStateTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(NodeState, all_fields=True)
        class NodeStateTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(TokenUsage, all_fields=True)
        class TokenUsageTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(DiagramMetadata, all_fields=True)
        class DiagramMetadataTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(PersonLLMConfig, all_fields=True)
        class PersonLLMConfigTypeFallback:
            pass
        
        @strawberry.experimental.pydantic.type(MemorySettings, all_fields=True)
        class MemorySettingsTypeFallback:
            pass
        
        self._type_map = {
            DomainDiagram: DomainDiagramTypeFallback,
            DomainNode: DomainNodeTypeFallback,
            DomainHandle: DomainHandleTypeFallback,
            DomainArrow: DomainArrowTypeFallback,
            DomainPerson: DomainPersonTypeFallback,
            DomainApiKey: DomainApiKeyTypeFallback,
            ExecutionState: ExecutionStateTypeFallback,
            NodeState: NodeStateTypeFallback,
            TokenUsage: TokenUsageTypeFallback,
            DiagramMetadata: DiagramMetadataTypeFallback,
            PersonLLMConfig: PersonLLMConfigTypeFallback,
            MemorySettings: MemorySettingsTypeFallback,
        }
    
    def get_strawberry_type(self, pydantic_model_class: Type) -> Type:
        """Get the Strawberry type for a Pydantic model class."""
        return self._type_map.get(pydantic_model_class, pydantic_model_class)
    
    def register_type(self, pydantic_model: Type, strawberry_type: Type):
        """Register a custom type mapping."""
        self._type_map[pydantic_model] = strawberry_type


# Global registry instance
type_registry = StrawberryTypeRegistry()


@lru_cache(maxsize=128)
def get_strawberry_type(pydantic_model_class: Type) -> Type:
    """Get the Strawberry GraphQL type for a Pydantic model class.
    
    This function provides a cached lookup for converting Pydantic models
    to their corresponding Strawberry types.
    
    Args:
        pydantic_model_class: The Pydantic model class
        
    Returns:
        The corresponding Strawberry type class
    """
    return type_registry.get_strawberry_type(pydantic_model_class)


def convert_pydantic_instance_to_strawberry(instance: Any) -> Any:
    """Convert a Pydantic model instance to its Strawberry type instance.
    
    Args:
        instance: A Pydantic model instance
        
    Returns:
        The corresponding Strawberry type instance
    """
    if instance is None:
        return None
    
    # Get the Strawberry type for this Pydantic model
    pydantic_class = type(instance)
    strawberry_type = get_strawberry_type(pydantic_class)
    
    # If it's the same class (no mapping), return as-is
    if strawberry_type == pydantic_class:
        return instance
    
    # Create Strawberry instance from Pydantic instance
    # The generated types handle this conversion internally
    return strawberry_type.from_pydantic(instance)


# Export the types for direct import
__all__ = [
    'get_strawberry_type',
    'convert_pydantic_instance_to_strawberry',
    'type_registry',
    'StrawberryTypeRegistry',
]

# If generated types are available, also export them
if STRAWBERRY_TYPES_AVAILABLE:
    __all__.extend([
        'DomainDiagramType',
        'DomainNodeType', 
        'DomainHandleType',
        'DomainArrowType',
        'DomainPersonType',
        'DomainApiKeyType',
        'ExecutionStateType',
        'NodeStateType',
        'TokenUsageType',
        'DiagramMetadataType',
        'PersonLLMConfigType',
        'MemorySettingsType',
        'NodeID',
        'HandleID',
        'ArrowID',
        'PersonID',
        'ApiKeyID',
        'DiagramID',
        'ExecutionID',
        'HookID',
        'TaskID',
        'JSONScalar',
    ])