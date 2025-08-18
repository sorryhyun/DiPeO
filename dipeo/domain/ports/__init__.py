"""Domain port definitions.

This module contains protocol definitions that establish boundaries
between the domain layer and infrastructure implementations.
"""

from .storage import (
    Artifact,
    ArtifactRef,
    ArtifactStorePort,
    BlobStorePort,
    FileInfo,
    FileSystemPort,
)

# DiagramInfo is in diagram.ports
try:
    from dipeo.domain.diagram.ports import DiagramInfo
except ImportError:
    DiagramInfo = None

from .conversation_repository import ConversationRepository
from .person_repository import PersonRepository

__all__ = [
    # Storage ports
    "BlobStorePort",
    "FileSystemPort", 
    "ArtifactStorePort",
    "FileInfo",
    "Artifact",
    "ArtifactRef",
    # Repository ports
    "ConversationRepository",
    "PersonRepository",
]

if DiagramInfo is not None:
    __all__.insert(5, "DiagramInfo")