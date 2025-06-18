"""
Diagram Domain Facade
Provides backward-compatible imports during migration
"""

from src.__generated__.models import (
    DomainDiagram,
    DomainNode as Node, 
    DomainArrow as Edge,
    DomainPerson as Person,
    DomainApiKey as ApiKey,
    DomainHandle as Handle,
    ExecutionState,
    # Export other necessary items
    NodeType,
    LLMService,
    DiagramFormat,
    ExecutionStatus,
)
from src.shared.domain import (
    SERVICE_TO_PROVIDER_MAP,
    DEFAULT_SERVICE
)
# Use DomainDiagram as Diagram for backward compatibility
Diagram = DomainDiagram
# from .services.diagram_service import DiagramService  # Import when needed to avoid circular deps
# from .validators import validate_diagram  # TODO: Create validators module

def validate_diagram(diagram):
    """Placeholder validator"""
    return True

__all__ = [
    'DomainDiagram',
    'Node',
    'Edge',
    'Person',
    'ApiKey',
    'Handle',
    'ExecutionState',
    'Diagram',
    'NodeType',
    'LLMService',
    'DiagramFormat',
    'ExecutionStatus',
    'SERVICE_TO_PROVIDER_MAP',
    'DEFAULT_SERVICE',
    # 'DiagramService',  # Import when needed
    'validate_diagram'
]
