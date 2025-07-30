"""Domain port definitions.

This module contains protocol definitions that establish boundaries
between the domain layer and infrastructure implementations.
"""

from .storage import (
    BlobStorePort,
    FileSystemPort,
    ArtifactStorePort,
    FileInfo,
    Artifact,
    ArtifactRef,
)

__all__ = [
    "BlobStorePort",
    "FileSystemPort", 
    "ArtifactStorePort",
    "FileInfo",
    "Artifact",
    "ArtifactRef",
]