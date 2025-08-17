"""Domain port definitions.

This module contains protocol definitions that establish boundaries
between the domain layer and infrastructure implementations.
"""

from dipeo.domain.storage import (
    Artifact,
    ArtifactRef,
    ArtifactStorePort,
    BlobStorePort,
    DiagramInfo,
    FileInfo,
    FileSystemPort,
)

from .conversation_repository import ConversationRepository
from .person_repository import PersonRepository

__all__ = [
    # Storage ports
    "BlobStorePort",
    "FileSystemPort", 
    "ArtifactStorePort",
    "FileInfo",
    "DiagramInfo",
    "Artifact",
    "ArtifactRef",
    # Repository ports
    "ConversationRepository",
    "PersonRepository",
]