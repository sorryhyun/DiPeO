"""
CLI-specific models for diagram validation and structure.

These models extend the generated models with CLI-specific functionality.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field

# Import all models from generated code
from dipeo_cli.__generated__.models import (
    # Enums
    NodeType,
    HandleDirection,
    DataType,
    LLMService,
    ForgettingMode,
    DiagramFormat,
    ExecutionStatus,
    NodeExecutionStatus,
    EventType,
    DBBlockSubType,
    ContentType,
    ContextCleaningRule,
    # Core models
    DomainNode as Node,
    DomainArrow as Arrow,
    DomainHandle as Handle,
    DomainPerson as Person,
    DomainApiKey as ApiKey,
    DomainDiagram,
    DiagramMetadata as BaseMetadata,
    # Other models
    Vec2,
    TokenUsage,
)

# CLI-specific extensions

@dataclass
class DiagramMetadata(BaseMetadata):
    """Extended metadata for CLI usage"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "created": self.created,
            "modified": self.modified,
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
            "author": self.author
        }


@dataclass
class CLIDiagram:
    """Simplified diagram model for CLI usage (wrapper around generated model)"""
    nodes: Dict[str, Node]
    arrows: Dict[str, Arrow]
    handles: Dict[str, Handle]
    persons: Dict[str, Person]
    api_keys: Dict[str, ApiKey]
    metadata: Optional[DiagramMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "nodes": {k: v.to_dict() if hasattr(v, 'to_dict') else vars(v) for k, v in self.nodes.items()},
            "arrows": {k: v.to_dict() if hasattr(v, 'to_dict') else vars(v) for k, v in self.arrows.items()},
            "handles": {k: v.to_dict() if hasattr(v, 'to_dict') else vars(v) for k, v in self.handles.items()},
            "persons": {k: v.to_dict() if hasattr(v, 'to_dict') else vars(v) for k, v in self.persons.items()},
            "api_keys": {k: v.to_dict() if hasattr(v, 'to_dict') else vars(v) for k, v in self.api_keys.items()},
            "metadata": self.metadata.to_dict() if self.metadata else None
        }
    
    def to_array_format(self) -> DomainDiagram:
        """Convert to array format for GraphQL"""
        return DomainDiagram(
            nodes=list(self.nodes.values()),
            arrows=list(self.arrows.values()),
            handles=list(self.handles.values()),
            persons=list(self.persons.values()),
            api_keys=list(self.api_keys.values()),
            metadata=self.metadata
        )
    
    @classmethod
    def from_array_format(cls, array_format: DomainDiagram) -> 'CLIDiagram':
        """Create from array format"""
        return cls(
            nodes={node.id: node for node in array_format.nodes},
            arrows={arrow.id: arrow for arrow in array_format.arrows},
            handles={handle.id: handle for handle in array_format.handles},
            persons={person.id: person for person in array_format.persons},
            api_keys={api_key.id: api_key for api_key in array_format.api_keys},
            metadata=array_format.metadata
        )


# Validation helpers
def validate_node_type(node_type: str) -> bool:
    """Check if node type is valid"""
    try:
        NodeType(node_type)
        return True
    except ValueError:
        return False


def validate_llm_service(service: str) -> bool:
    """Check if LLM service is valid"""
    try:
        LLMService(service)
        return True
    except ValueError:
        return False