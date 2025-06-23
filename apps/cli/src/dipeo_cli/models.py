"""
CLI models - re-exports from generated models.

This module re-exports the generated models for CLI usage.
No wrappers or renames are needed - we use the generated types directly.
"""

from dataclasses import asdict
from typing import Any, Dict

# Re-export all models directly from generated code
from dipeo_domain import (
    DiagramDictFormat,
    DomainDiagram,
    LLMService,
    # Enums
    NodeType,
)

# Utility functions for working with generated models


def diagram_to_dict(diagram: DiagramDictFormat) -> Dict[str, Any]:
    """Convert a diagram to dictionary for JSON serialization.

    Uses the generated models' dict() method from dataclasses.
    """
    # The generated dataclasses already have appropriate serialization
    return asdict(diagram)


def diagram_dict_to_array(diagram: DiagramDictFormat) -> DomainDiagram:
    """Convert dictionary format to array format."""
    return DomainDiagram(
        nodes=list(diagram.nodes.values()),
        arrows=list(diagram.arrows.values()),
        handles=list(diagram.handles.values()),
        persons=list(diagram.persons.values()),
        apiKeys=list(diagram.api_keys.values()),
        metadata=diagram.metadata,
    )


def diagram_array_to_dict(diagram: DomainDiagram) -> DiagramDictFormat:
    """Convert array format to dictionary format."""
    return DiagramDictFormat(
        nodes={node.id: node for node in diagram.nodes},
        arrows={arrow.id: arrow for arrow in diagram.arrows},
        handles={handle.id: handle for handle in diagram.handles},
        persons={person.id: person for person in diagram.persons},
        apiKeys={api_key.id: api_key for api_key in diagram.api_keys},
        metadata=diagram.metadata,
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
