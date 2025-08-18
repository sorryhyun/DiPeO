"""Domain storage services and ports.

Re-exports storage ports from the main ports module for backward compatibility.
"""

from ..ports.storage import (
    Artifact,
    ArtifactRef,
    ArtifactStorePort,
    BlobStorePort,
    FileInfo,
    FileSystemPort,
)

# DiagramInfo is likely in diagram.ports
try:
    from ..diagram.ports import DiagramInfo
except ImportError:
    DiagramInfo = None

__all__ = [
    "BlobStorePort",
    "FileSystemPort",
    "ArtifactStorePort",
    "FileInfo",
    "Artifact",
    "ArtifactRef",
]

if DiagramInfo is not None:
    __all__.append("DiagramInfo")